"""Pure, versioned scoring of declared slot evidence; no game execution.

FR-010 / FR-019 / NFR-010: preserve scheduled denominators, separate played
outcomes from invalid-generation exposures, and block incomplete evidence.
Input provenance and accepted-source labels are declarations, not proof
that a provider or trusted runner produced these records.
"""

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from slither_evolver.config import ConfigError, RunConfig, validate_config


RESULTS_SCHEMA_VERSION = 1
MAX_RESULTS_BYTES = 16 * 1024 * 1024


class ScoringError(ValueError):
    """Malformed or incompatible scoring evidence."""


class IncompleteEvidence(ScoringError):
    """A valid partial/blocked bundle has no final fitness."""

    def __init__(self, *, missing_samples, missing_slots, blocked_samples,
                 infrastructure_faults, interrupted_slots):
        self.missing_samples = missing_samples
        self.missing_slots = missing_slots
        self.blocked_samples = blocked_samples
        self.infrastructure_faults = infrastructure_faults
        self.interrupted_slots = interrupted_slots
        super().__init__(
            f"{missing_samples} missing samples, {missing_slots} missing slots, "
            f"{blocked_samples} blocked samples, {infrastructure_faults} infrastructure faults, "
            f"{interrupted_slots} interrupted slots; no final fitness"
        )


@dataclass(frozen=True)
class Provenance:
    kind: str
    description: str


@dataclass(frozen=True)
class SampleRecord:
    sample_id: str
    sample_index: int
    source_hash: str | None
    generation_status: str
    reason: str | None


@dataclass(frozen=True)
class ResultRecord:
    slot_id: str
    sample_id: str
    opponent_id: str
    opponent_source_hash: str
    profile_hash: str
    seed: int
    status: str
    outcome: str | None
    cause: str | None
    reason: str | None


@dataclass(frozen=True)
class ScoringInput:
    run_id: str
    configuration_hash: str
    prompt_id: str
    prompt_hash: str
    phase: str
    provenance: Provenance
    samples: tuple[SampleRecord, ...]
    results: tuple[ResultRecord, ...]


@dataclass(frozen=True)
class OutcomeCounts:
    scheduled_slots: int
    played_matches: int
    wins: int
    losses: int
    draws: int
    bot_faults: int
    synthetic_failures: int


@dataclass(frozen=True)
class OpponentScore:
    opponent_id: str
    source_hash: str
    profile_hash: str
    counts: OutcomeCounts
    effective_win_rate: float
    effective_win_rate_fraction: str


@dataclass(frozen=True)
class FitnessResult:
    schema_version: int
    scoring_version: int
    run_id: str
    configuration_hash: str
    prompt_id: str
    prompt_hash: str
    phase: str
    provenance: Provenance
    samples_per_prompt: int
    accepted_samples: int
    invalid_samples: int
    accepted_sample_fraction: float
    counts: OutcomeCounts
    overall_weight: float
    worst_weight: float
    overall_effective_win_rate: float
    overall_effective_win_rate_fraction: str
    worst_opponent_effective_win_rate: float
    worst_opponent_effective_win_rate_fraction: str
    fitness: float
    fitness_fraction: str
    opponents: tuple[OpponentScore, ...]

    def to_dict(self):
        """Return a detached JSON-ready summary with full counts and ratios."""
        result = asdict(self)
        result["opponents"] = list(result["opponents"])
        return result


def _canonical(value):
    try:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                           allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ScoringError("evidence: expected finite UTF-8 JSON data") from None


def configuration_hash(config: RunConfig):
    """Hash normalized config using the store's UTF-8 JSON byte convention."""
    if not isinstance(config, RunConfig):
        raise ScoringError("config: expected a validated RunConfig")
    return hashlib.sha256(_canonical(config.to_dict())).hexdigest()


def slot_id(configuration_digest, prompt_id, prompt_hash, phase, sample_id,
            source_hash, opponent_id, seed):
    """Stable identity for one configured sample/opponent/seed exposure.

    This helper constructs IDs, not schedules. The parser validates fields
    and recomputes each ID before accepting the supplied result.
    """
    key = [RESULTS_SCHEMA_VERSION, configuration_digest, prompt_id, prompt_hash,
           phase, sample_id, source_hash, opponent_id, seed]
    return hashlib.sha256(_canonical(key)).hexdigest()


def _fields(value, fields, path):
    if type(value) is not dict or set(value) != set(fields.split()):
        raise ScoringError(f"{path}: missing or unknown fields")


def _identifier(value, path):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ScoringError(f"{path}: expected a 1–64-character ASCII identifier")
    return value


def _hash(value, path):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ScoringError(f"{path}: expected a lowercase SHA-256 hash")
    return value


def _text(value, path):
    if type(value) is not str or not value.strip() or len(value) > 2048:
        raise ScoringError(f"{path}: expected nonempty text of at most 2048 characters")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise ScoringError(f"{path}: expected UTF-8 text") from None
    return value


def _integer(value, path, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ScoringError(f"{path}: expected an integer from 0 through {maximum}")
    return value


def _sample(document, config):
    _fields(document, "sample_id sample_index source_hash generation_status reason", "sample")
    identity = _identifier(document["sample_id"], "sample_id")
    index = _integer(document["sample_index"], "sample_index", config.samples_per_prompt - 1)
    status = document["generation_status"]
    source = document["source_hash"]
    reason = document["reason"]
    if status == "accepted":
        _hash(source, "source_hash")
        if reason is not None:
            raise ScoringError("sample: accepted source has no failure reason")
    elif status in ("invalid", "blocked"):
        _text(reason, "sample.reason")
        if source is not None:
            _hash(source, "source_hash")
        if status == "blocked" and source is not None:
            raise ScoringError("sample: blocked generation has no accepted source")
    else:
        raise ScoringError("generation_status: expected accepted, invalid, or blocked")
    return SampleRecord(identity, index, source, status, reason)


def _result(document, sample, opponent, seeds, identity):
    _fields(document, "slot_id sample_id opponent_id opponent_source_hash profile_hash seed status outcome cause reason", "result")
    if (document["opponent_source_hash"] != opponent.source_hash
            or document["profile_hash"] != opponent.profile_hash):
        raise ScoringError("result: incompatible opponent/profile hashes")
    seed = _integer(document["seed"], "seed", 2**32 - 1)
    if seed not in seeds:
        raise ScoringError("seed: not in the configured phase schedule")
    expected = slot_id(identity.configuration_hash, identity.prompt_id, identity.prompt_hash,
                       identity.phase, sample.sample_id, sample.source_hash, opponent.id, seed)
    if _hash(document["slot_id"], "slot_id") != expected:
        raise ScoringError("slot_id: does not match its frozen coordinates")
    status = document["status"]
    outcome, cause, reason = document["outcome"], document["cause"], document["reason"]
    if status == "played":
        if outcome not in ("win", "loss", "draw") or cause is not None or reason is not None:
            raise ScoringError("played: requires win/loss/draw and no failure cause/reason")
    elif status == "bot_fault":
        if outcome != "loss" or cause not in ("exception", "illegal_direction", "decision_timeout"):
            raise ScoringError("bot_fault: requires loss and a known bot cause")
        _text(reason, "result.reason")
    elif status == "invalid_generation":
        if outcome is not None or cause != "generation_contract":
            raise ScoringError("invalid_generation: synthetic exposure has no played outcome")
        _text(reason, "result.reason")
    elif status == "infrastructure_fault":
        if outcome is not None or cause not in ("provider", "runner", "storage", "isolation"):
            raise ScoringError("infrastructure_fault: requires no outcome and a known infrastructure cause")
        _text(reason, "result.reason")
    elif status == "interrupted":
        if outcome is not None or cause != "operator_interrupt":
            raise ScoringError("interrupted: requires no outcome and operator_interrupt cause")
        _text(reason, "result.reason")
    else:
        raise ScoringError("result.status: unknown status")
    if sample.generation_status == "invalid" and status != "invalid_generation":
        raise ScoringError("sample: invalid generation must fill its schedule with synthetic exposures")
    if sample.generation_status == "accepted" and status == "invalid_generation":
        raise ScoringError("sample: accepted source cannot claim invalid-generation exposures")
    if sample.generation_status == "blocked" and status not in ("infrastructure_fault", "interrupted"):
        raise ScoringError("sample: blocked generation cannot be scored as played or synthetic failure")
    return ResultRecord(expected, sample.sample_id, opponent.id, opponent.source_hash,
                        opponent.profile_hash, seed, status, outcome, cause, reason)


def _parse_input(config, document):
    _fields(document, "schema_version run_id configuration_hash prompt_id prompt_hash phase provenance samples results", "results bundle")
    if type(document["schema_version"]) is not int or document["schema_version"] != RESULTS_SCHEMA_VERSION:
        raise ScoringError("schema_version: unsupported results schema")
    if document["run_id"] != config.run_id:
        raise ScoringError("run_id: incompatible with configuration")
    digest = _hash(document["configuration_hash"], "configuration_hash")
    if digest != configuration_hash(config):
        raise ScoringError("configuration_hash: incompatible with frozen configuration")
    prompt_id = _identifier(document["prompt_id"], "prompt_id")
    prompt_hash = _hash(document["prompt_hash"], "prompt_hash")
    phase = document["phase"]
    if phase not in ("optimization", "holdout"):
        raise ScoringError("phase: expected optimization or holdout")
    seeds = set(config.optimization_seeds if phase == "optimization" else config.holdout_seeds)
    provenance = document["provenance"]
    _fields(provenance, "kind description", "provenance")
    if provenance["kind"] not in ("synthetic", "manual", "automated"):
        raise ScoringError("provenance.kind: expected synthetic, manual, or automated")
    provenance = Provenance(provenance["kind"], _text(provenance["description"], "provenance.description"))
    if type(document["samples"]) is not list or type(document["results"]) is not list:
        raise ScoringError("samples/results: expected lists")
    samples = tuple(_sample(item, config) for item in document["samples"])
    by_id = {item.sample_id: item for item in samples}
    if len(by_id) != len(samples) or len({item.sample_index for item in samples}) != len(samples):
        raise ScoringError("samples: duplicate identity or index")
    identity = ScoringInput(config.run_id, digest, prompt_id, prompt_hash, phase,
                            provenance, samples, ())
    opponents = {item.id: item for item in config.opponents}
    results = []
    coordinates = set()
    for item in document["results"]:
        _fields(item, "slot_id sample_id opponent_id opponent_source_hash profile_hash seed status outcome cause reason", "result")
        sample_id = _identifier(item["sample_id"], "sample_id")
        opponent_id = _identifier(item["opponent_id"], "opponent_id")
        if sample_id not in by_id or opponent_id not in opponents:
            raise ScoringError("result: unknown sample or opponent")
        record = _result(item, by_id[sample_id], opponents[opponent_id], seeds, identity)
        key = (record.sample_id, record.opponent_id, record.seed)
        if key in coordinates:
            raise ScoringError("results: duplicate scheduled slot")
        coordinates.add(key)
        results.append(record)
    return ScoringInput(config.run_id, digest, prompt_id, prompt_hash, phase,
                        provenance, samples, tuple(results))


def _counts(records, denominator):
    played = [record for record in records if record.status in ("played", "bot_fault")]
    return OutcomeCounts(
        scheduled_slots=denominator, played_matches=len(played),
        wins=sum(record.outcome == "win" for record in played),
        losses=sum(record.outcome == "loss" for record in played),
        draws=sum(record.outcome == "draw" for record in played),
        bot_faults=sum(record.status == "bot_fault" for record in records),
        synthetic_failures=sum(record.status == "invalid_generation" for record in records),
    )


def _ratio(value):
    return f"{value.numerator}/{value.denominator}"


def validate_results(config: RunConfig, document) -> ScoringInput:
    """Validate declared records even when their schedule is incomplete.

    Reporting uses this contract to preserve partial evidence without
    assigning fitness. This does not certify source or trusted outcomes.
    """
    if not isinstance(config, RunConfig):
        raise ScoringError("config: expected a validated RunConfig")
    try:
        config = validate_config(config.to_dict())
    except ConfigError as error:
        raise ScoringError(f"config: {error}") from None
    return _parse_input(config, document)


def score_results(config: RunConfig, document) -> FitnessResult:
    """Compute fitness only for a complete, compatible, scoreable schedule.

    Return immutable counts and exact rational values alongside JSON floats.
    IncompleteEvidence never contains a fitness. Invalid records raise
    ScoringError instead of being dropped, repaired, or scored as losses.
    """
    if not isinstance(config, RunConfig):
        raise ScoringError("config: expected a validated RunConfig")
    try:
        config = validate_config(config.to_dict())
    except ConfigError as error:
        raise ScoringError(f"config: {error}") from None
    evidence = _parse_input(config, document)
    seeds = config.optimization_seeds if evidence.phase == "optimization" else config.holdout_seeds
    per_opponent = config.samples_per_prompt * len(seeds)
    expected_slots = per_opponent * len(config.opponents)
    missing_samples = config.samples_per_prompt - len(evidence.samples)
    missing_slots = expected_slots - len(evidence.results)
    blocked_samples = sum(item.generation_status == "blocked" for item in evidence.samples)
    infrastructure = sum(item.status == "infrastructure_fault" for item in evidence.results)
    interrupted = sum(item.status == "interrupted" for item in evidence.results)
    if missing_samples or missing_slots or blocked_samples or infrastructure or interrupted:
        raise IncompleteEvidence(missing_samples=missing_samples, missing_slots=missing_slots,
                                 blocked_samples=blocked_samples, infrastructure_faults=infrastructure,
                                 interrupted_slots=interrupted)
    # Unique in-bounds coordinates + exact cardinality prove a complete
    # Cartesian schedule without allocating a second potentially huge set.
    opponents = []
    rates = []
    for opponent in config.opponents:
        records = [record for record in evidence.results if record.opponent_id == opponent.id]
        counts = _counts(records, per_opponent)
        rate = Fraction(counts.wins, counts.scheduled_slots)
        rates.append(rate)
        opponents.append(OpponentScore(opponent.id, opponent.source_hash, opponent.profile_hash,
                                        counts, float(rate), _ratio(rate)))
    counts = _counts(evidence.results, expected_slots)
    overall = Fraction(counts.wins, expected_slots)
    worst = min(rates)
    fitness = (Fraction(str(config.scoring.overall_weight)) * overall
               + Fraction(str(config.scoring.worst_weight)) * worst)
    accepted = sum(item.generation_status == "accepted" for item in evidence.samples)
    invalid = sum(item.generation_status == "invalid" for item in evidence.samples)
    return FitnessResult(
        schema_version=RESULTS_SCHEMA_VERSION, scoring_version=config.scoring.version,
        run_id=config.run_id, configuration_hash=evidence.configuration_hash,
        prompt_id=evidence.prompt_id, prompt_hash=evidence.prompt_hash, phase=evidence.phase,
        provenance=evidence.provenance, samples_per_prompt=config.samples_per_prompt,
        accepted_samples=accepted, invalid_samples=invalid,
        accepted_sample_fraction=float(Fraction(accepted, config.samples_per_prompt)),
        counts=counts, overall_weight=config.scoring.overall_weight,
        worst_weight=config.scoring.worst_weight, overall_effective_win_rate=float(overall),
        overall_effective_win_rate_fraction=_ratio(overall),
        worst_opponent_effective_win_rate=float(worst),
        worst_opponent_effective_win_rate_fraction=_ratio(worst),
        fitness=float(fitness), fitness_fraction=_ratio(fitness), opponents=tuple(opponents),
    )


def load_results(path) -> dict:
    """Read a bounded strict UTF-8 JSON bundle; do not run referenced text."""
    def pairs(items):
        record = {}
        for key, value in items:
            if key in record:
                raise ScoringError("results JSON: duplicate fields")
            record[key] = value
        return record

    def constant(value):
        raise ScoringError("results JSON: nonfinite numbers")

    try:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_RESULTS_BYTES + 1)
        if len(data) > MAX_RESULTS_BYTES:
            raise ScoringError("results JSON: exceeds 16 MiB")
        document = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except OSError:
        raise ScoringError("results JSON: cannot read file") from None
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, ScoringError):
            raise
        raise ScoringError("results JSON: invalid UTF-8 JSON") from None
    if type(document) is not dict:
        raise ScoringError("results JSON: expected an object")
    return document
