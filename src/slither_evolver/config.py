"""Validate experiment configuration without requests or secret lookups.

FR-001 / TC-001: enforce a closed, versioned JSON contract and return
immutable records. Live readiness checks configured controls only; it does
not verify prices, credentials, adapter availability, hashes, or isolation.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any


class ConfigError(ValueError):
    """An input does not satisfy the configuration contract."""


@dataclass(frozen=True)
class SearchConfig:
    elite_count: int
    tournament_size: int
    mutation_probability: float
    crossover_probability: float
    max_population_attempts: int
    seed: int


@dataclass(frozen=True)
class ScoringConfig:
    version: int
    overall_weight: float
    worst_weight: float


@dataclass(frozen=True)
class OpponentConfig:
    id: str
    source_hash: str
    profile_hash: str


@dataclass(frozen=True)
class FixedContext:
    source_commit: str
    game_hash: str
    api_hash: str
    system_prompt_hash: str
    baseline_prompt_hash: str


@dataclass(frozen=True)
class ResourceLimits:
    max_run_seconds: float
    match_timeout_seconds: float
    decision_timeout_ms: int
    max_frames: int
    memory_mb: int
    max_prompt_chars: int
    max_source_bytes: int
    max_response_bytes: int
    max_message_bytes: int


@dataclass(frozen=True)
class ProviderConfig:
    adapter: str
    model: str
    credential_env: str
    max_output_tokens: int
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class BudgetConfig:
    max_requests: int | None
    max_cost: Decimal | None
    currency: str | None
    max_request_cost: Decimal | None
    pricing_version: str | None


@dataclass(frozen=True)
class RunConfig:
    schema_version: int
    run_id: str
    mode: str
    population_size: int
    generation_count: int
    samples_per_prompt: int
    search: SearchConfig
    scoring: ScoringConfig
    opponents: tuple[OpponentConfig, ...]
    optimization_seeds: tuple[int, ...]
    holdout_seeds: tuple[int, ...]
    fixed_context: FixedContext
    limits: ResourceLimits
    provider: ProviderConfig | None
    budget: BudgetConfig

    def to_dict(self) -> dict[str, Any]:
        """Return a detached, JSON-compatible snapshot without credentials."""
        return _to_json(self)


def _to_json(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _to_json(getattr(value, field.name))
                for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: _to_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_json(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    return value


def _object(value: Any, record: type, path: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ConfigError(f"{path}: expected a JSON object with string keys")
    allowed = {field.name for field in fields(record)}
    unknown = sorted(value.keys() - allowed)
    missing = sorted(allowed - value.keys())
    if unknown:
        raise ConfigError(f"{path}: unknown field(s): {', '.join(unknown)}")
    if missing:
        raise ConfigError(f"{path}: missing field(s): {', '.join(missing)}")
    return value


def _integer(value: Any, path: str, minimum: int = 1,
             maximum: int | None = 2**53 - 1) -> int:
    # bool is an int subclass, but true is not a valid count or seed.
    if type(value) is not int or value < minimum:
        raise ConfigError(f"{path}: expected an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{path}: expected an integer <= {maximum}")
    return value


def _number(value: Any, path: str, *, probability: bool = False) -> float:
    if type(value) not in (int, float):
        raise ConfigError(f"{path}: expected a finite JSON number")
    try:
        number = float(value)
    except OverflowError:
        raise ConfigError(f"{path}: expected a finite JSON number") from None
    if not math.isfinite(number):
        raise ConfigError(f"{path}: expected a finite JSON number")
    if probability and not 0 <= number <= 1:
        raise ConfigError(f"{path}: expected a number between 0 and 1")
    if not probability and number <= 0:
        raise ConfigError(f"{path}: expected a number > 0")
    return number


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{path}: expected a nonempty string")
    if value != value.strip() or any(ord(char) < 32 for char in value):
        raise ConfigError(f"{path}: whitespace/control characters are not allowed")
    return value


def _identifier(value: Any, path: str) -> str:
    value = _text(value, path)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ConfigError(f"{path}: use 1–64 letters, digits, underscores, or hyphens")
    return value


def _hash(value: Any, path: str, length: int = 64) -> str:
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ConfigError(f"{path}: expected {length} lowercase hex characters")
    return value


def _seeds(value: Any, path: str) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{path}: expected a nonempty list of seeds")
    result = tuple(_integer(seed, f"{path}[{index}]", 0, 2**32 - 1)
                   for index, seed in enumerate(value))
    if len(result) != len(set(result)):
        raise ConfigError(f"{path}: duplicate seeds are not allowed")
    return result


def _money(value: Any, path: str) -> Decimal | None:
    if value is None:
        return None
    if type(value) not in (str, int, float):
        raise ConfigError(f"{path}: expected a positive decimal amount or null")
    if isinstance(value, str) and not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
        raise ConfigError(f"{path}: use a plain decimal string such as 0.05")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ConfigError(f"{path}: expected a positive decimal amount or null") from None
    if not amount.is_finite() or amount <= 0:
        raise ConfigError(f"{path}: expected a positive finite amount")
    return amount


def _freeze_settings(value: Any, path: str, depth: int = 0) -> Any:
    if depth > 64:
        raise ConfigError(f"{path}: settings nesting is too deep; maximum depth is 64")
    forbidden = {"api_key", "apikey", "authorization", "password", "secret",
                 "access_token", "api_token", "credentials"}
    if isinstance(value, dict):
        frozen = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ConfigError(f"{path}: settings keys must be strings")
            if key.lower().replace("-", "_") in forbidden:
                raise ConfigError(f"{path}: credential fields are not allowed; use credential_env")
            frozen[key] = _freeze_settings(item, f"{path}.{key}", depth + 1)
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(_freeze_settings(item, f"{path}[{index}]", depth + 1)
                     for index, item in enumerate(value))
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise ConfigError(f"{path}: expected finite JSON data")


def validate_config(document: Any, *, live: bool = False) -> RunConfig:
    """Validate schema 1, optionally requiring future live-request controls.

    No file writes, network calls, secret lookups, or bot execution occur.
    Workload/resource values are required; this function chooses no defaults.
    """
    if type(live) is not bool:
        raise ConfigError("live: expected a Boolean validation flag")
    data = _object(document, RunConfig, "config")
    version = _integer(data["schema_version"], "schema_version")
    if version != 1:
        raise ConfigError("schema_version: only version 1 is supported")
    run_id = _identifier(data["run_id"], "run_id")
    mode = _text(data["mode"], "mode")
    if mode not in {"pilot", "evolve"}:
        raise ConfigError("mode: experiment configurations support pilot or evolve")
    population = _integer(data["population_size"], "population_size", 2)
    generations = _integer(data["generation_count"], "generation_count")
    samples = _integer(data["samples_per_prompt"], "samples_per_prompt")

    values = _object(data["search"], SearchConfig, "search")
    search = SearchConfig(
        _integer(values["elite_count"], "search.elite_count", 1, population - 1),
        _integer(values["tournament_size"], "search.tournament_size", 1, population),
        _number(values["mutation_probability"], "search.mutation_probability", probability=True),
        _number(values["crossover_probability"], "search.crossover_probability", probability=True),
        _integer(values["max_population_attempts"], "search.max_population_attempts"),
        _integer(values["seed"], "search.seed", 0, 2**32 - 1),
    )
    if not math.isclose(search.mutation_probability + search.crossover_probability,
                        1, rel_tol=0, abs_tol=1e-9):
        raise ConfigError("search: mutation and crossover probabilities must sum to 1")
    values = _object(data["scoring"], ScoringConfig, "scoring")
    scoring = ScoringConfig(
        _integer(values["version"], "scoring.version"),
        _number(values["overall_weight"], "scoring.overall_weight", probability=True),
        _number(values["worst_weight"], "scoring.worst_weight", probability=True),
    )
    if scoring.version != 1:
        raise ConfigError("scoring.version: only version 1 is supported")
    if not math.isclose(scoring.overall_weight + scoring.worst_weight,
                        1, rel_tol=0, abs_tol=1e-9):
        raise ConfigError("scoring: overall and worst weights must sum to 1")

    if not isinstance(data["opponents"], list) or not data["opponents"]:
        raise ConfigError("opponents: expected a nonempty list")
    opponents = []
    for index, item in enumerate(data["opponents"]):
        path = f"opponents[{index}]"
        item = _object(item, OpponentConfig, path)
        opponents.append(OpponentConfig(
            _identifier(item["id"], f"{path}.id"),
            _hash(item["source_hash"], f"{path}.source_hash"),
            _hash(item["profile_hash"], f"{path}.profile_hash"),
        ))
    if len({opponent.id for opponent in opponents}) != len(opponents):
        raise ConfigError("opponents: IDs must uniquely name opponent/profile combinations")
    optimization = _seeds(data["optimization_seeds"], "optimization_seeds")
    holdout = _seeds(data["holdout_seeds"], "holdout_seeds")
    if set(optimization) & set(holdout):
        raise ConfigError("holdout_seeds: must not overlap optimization_seeds")
    values = _object(data["fixed_context"], FixedContext, "fixed_context")
    context = FixedContext(**{
        key: _hash(value, f"fixed_context.{key}", 40 if key == "source_commit" else 64)
        for key, value in values.items()
    })
    values = _object(data["limits"], ResourceLimits, "limits")
    limits = ResourceLimits(**{
        key: (_number(value, f"limits.{key}") if key.endswith("_seconds")
              else _integer(value, f"limits.{key}"))
        for key, value in values.items()
    })
    if limits.decision_timeout_ms / 1000 > limits.match_timeout_seconds:
        raise ConfigError("limits.decision_timeout_ms: must fit within match_timeout_seconds")

    provider = None
    if data["provider"] is not None:
        values = _object(data["provider"], ProviderConfig, "provider")
        env = _text(values["credential_env"], "provider.credential_env")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env):
            raise ConfigError("provider.credential_env: expected an environment-variable name, not a key")
        if not isinstance(values["settings"], dict):
            raise ConfigError("provider.settings: expected a JSON object")
        provider = ProviderConfig(
            _identifier(values["adapter"], "provider.adapter"),
            _text(values["model"], "provider.model"), env,
            _integer(values["max_output_tokens"], "provider.max_output_tokens"),
            _freeze_settings(values["settings"], "provider.settings"),
        )
    values = _object(data["budget"], BudgetConfig, "budget")
    requests = values["max_requests"]
    if requests is not None:
        requests = _integer(requests, "budget.max_requests")
    currency = values["currency"]
    if currency is not None and (not isinstance(currency, str)
                                 or not re.fullmatch(r"[A-Z]{3}", currency)):
        raise ConfigError("budget.currency: expected three uppercase letters or null")
    pricing = values["pricing_version"]
    if pricing is not None:
        pricing = _text(pricing, "budget.pricing_version")
    budget = BudgetConfig(requests, _money(values["max_cost"], "budget.max_cost"),
                          currency, _money(values["max_request_cost"], "budget.max_request_cost"), pricing)
    if budget.max_cost is not None and budget.max_request_cost is not None:
        if budget.max_request_cost > budget.max_cost:
            raise ConfigError("budget.max_request_cost: must not exceed max_cost in the same currency")
    if live:
        if provider is None:
            raise ConfigError("provider: required for live readiness; select it after the pilot")
        missing = [field.name for field in fields(BudgetConfig)
                   if getattr(budget, field.name) is None]
        if missing:
            raise ConfigError("budget: live readiness requires " + ", ".join(missing))
    return RunConfig(version, run_id, mode, population, generations, samples,
                     search, scoring, tuple(opponents), optimization, holdout,
                     context, limits, provider, budget)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("JSON: duplicate object fields are not allowed")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ConfigError("JSON: NaN and Infinity are not valid finite JSON numbers")


def load_config(path: str | Path, *, live: bool = False) -> RunConfig:
    """Read strict UTF-8 JSON without exposing its contents in errors."""
    try:
        with Path(path).open("rb") as stream:
            content = stream.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise ConfigError("config: file exceeds the 1 MiB schema-input limit")
        document = json.loads(content.decode("utf-8"),
                              object_pairs_hook=_unique_object,
                              parse_constant=_reject_constant)
        return validate_config(document, live=live)
    except json.JSONDecodeError as error:
        raise ConfigError(f"JSON: invalid syntax at line {error.lineno}, column {error.colno}") from None
    except ConfigError:
        raise
    except (OSError, UnicodeError):
        raise ConfigError("config: cannot read UTF-8 file; check the path and permissions") from None
    except ValueError:
        raise ConfigError("JSON: number exceeds the supported parser range") from None
    except RecursionError:
        raise ConfigError("config: nesting is too deep") from None
