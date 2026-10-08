# Experiment Configuration | Implemented Contract

This first construction increment implements `FR-001` configuration validation. It includes an immutable `RunConfig`, strict UTF-8 JSON loading, a synthetic offline example, and a validation command. Local storage is now implemented separately in [its contract](./12_local_storage.md). Generation, tournament execution, scoring, and reports remain planned.

## Run the Validator

From the repository root in Bash, using Python 3.12 or later:

```bash
PYTHONPATH=src python -m slither_evolver validate --config configs/offline.example.json
```

Expected output:

```text
Valid offline configuration: synthetic-config-check (schema 1).
No requests made, credentials read, or bot code executed.
```

Check whether a configuration contains the controls required for future live requests:

```bash
PYTHONPATH=src python -m slither_evolver validate --config configs/offline.example.json --live
```

The supplied offline example intentionally fails that check with exit status `2`, because no provider has been selected. `--live` changes validation requirements only; it does not make a request, read a credential, or execute a bot. An accepted configuration is not approval or evidence of safe live execution.

Use `PYTHONPATH=src python -m slither_evolver validate --help` for command help. Valid input returns `0`; configuration errors return `2` with a field-specific message. No files are written by the command.

## Schema Version 1

All fields shown in [offline.example.json](../configs/offline.example.json) are required. Unknown fields are rejected at each fixed-schema level. No workload values, resource bounds, provider, or budget are silently chosen. The example's counts, limits, seeds, opponents, and hashes are **synthetic test data**, not recommended pilot settings or actual artifact identities.

| Field / Object | Contract |
| --- | --- |
| `schema_version` | Integer `1`. Boolean values are not integers in this contract. |
| `run_id` | 1–64 ASCII letters/digits/underscores/hyphens; starts with a letter or digit; cannot be a path. |
| `mode` | `pilot` or `evolve`. These describe future experiment workflows; the current offline interface implements `validate`, `init`, and `inspect`. Guided/replay imports will have separate input contracts. |
| `population_size` | Integer at least 2. |
| `generation_count`, `samples_per_prompt` | Positive integers; generation count includes generation zero. |
| `search.elite_count` | Integer from 1 through population size minus 1. |
| `search.tournament_size` | Integer from 1 through population size. |
| `search.mutation_probability`, `search.crossover_probability` | Finite numbers in [0, 1], summing to 1 within absolute tolerance 1e-9. |
| `search.max_population_attempts` | Positive integer. |
| `search.seed` | Integer from 0 through 2^32 − 1. |
| `scoring.version` | Integer `1`. |
| `scoring.overall_weight`, `scoring.worst_weight` | Finite numbers in [0, 1], summing to 1 within absolute tolerance 1e-9. Supply 0.70/0.30 to use the initial design. |
| `opponents` | Nonempty list of objects containing unique `id`, `source_hash`, and `profile_hash`. Name each opponent/profile combination with a unique ID. IDs follow the run-ID rules; hashes are 64 lowercase hexadecimal characters. |
| `optimization_seeds`, `holdout_seeds` | Nonempty, unique lists of unsigned 32-bit integers. The two lists must be disjoint. |
| `fixed_context.source_commit` | 40 lowercase hexadecimal characters. |
| Other `fixed_context` fields | `game_hash`, `api_hash`, `system_prompt_hash`, and `baseline_prompt_hash`: 64 lowercase hexadecimal characters each. |
| `limits.max_run_seconds`, `limits.match_timeout_seconds` | Positive finite JSON numbers. |
| Other `limits` fields | Positive integers: `decision_timeout_ms`, `max_frames`, `memory_mb`, `max_prompt_chars`, `max_source_bytes`, `max_response_bytes`, `max_message_bytes`. Per-decision deadline must fit within the match deadline. |
| `provider` | Null while unselected, or the complete object described below. |
| `budget` | Complete object with explicit controls or null values while undecided, as described below. |

Ordinary integer fields cannot exceed 2^53 − 1, avoiding integers that cannot be represented exactly in JavaScript. Seed fields have the narrower unsigned 32-bit bound. JSON files are limited to 1 MiB; duplicate fields, NaN/Infinity, invalid UTF-8, and invalid syntax are rejected. Provider-setting nesting has a fixed maximum depth of 64.

### Provider Object

Required fields when the object is supplied:

* `adapter`: identifier following the run-ID rules.
* `model`: nonempty string without surrounding whitespace or control characters.
* `credential_env`: an environment-variable **name**, such as `PROJECT_LLM_KEY`, never the credential value.
* `max_output_tokens`: positive integer.
* `settings`: adapter-owned JSON object with finite values. This is the one extension point that accepts provider-specific keys. Nested objects/arrays are copied into immutable mappings/tuples.

Common credential fields such as `api_key`, `authorization`, and `access_token` are rejected in settings. This is a useful guard, not a general secret-detection guarantee: only put nonsensitive generation settings here. Values are not echoed in diagnostics. The validator never looks up the named environment variable.

### Budget Object

All fields are required, and may be null during offline planning:

* `max_requests`: positive integer when supplied.
* `max_cost`: positive finite monetary amount when supplied.
* `currency`: three uppercase letters when supplied; use the currency matching the provider's pricing.
* `max_request_cost`: positive conservative per-request upper bound, in the same currency, not exceeding `max_cost`.
* `pricing_version`: nonempty string identifying the operator's pricing/bound basis.

Prefer plain decimal strings for monetary amounts, such as `"0.10"`, to preserve precision. Numeric inputs are accepted and normalized to decimal amounts. Exported snapshots use plain decimal strings for money, including small numeric inputs that originally used exponent notation. Strings cannot contain whitespace, signs, exponents, underscores, or nonfinite values.

Live-readiness validation requires a complete provider object and every budget field to be non-null. The validator does not check current prices, ensure a supplied bound is conservative, reserve spending, or claim that the complete experiment fits its cap. Those responsibilities belong to the future provider/budget increment.

## Program Interface

```python
from slither_evolver.config import load_config

config = load_config("configs/offline.example.json")
print(config.samples_per_prompt)
snapshot = config.to_dict()
```

`validate_config(document, live=False)` validates an already-loaded dictionary. `load_config(path, live=False)` additionally checks the JSON file. Invalid inputs raise `ConfigError`. Records, nested provider settings, opponent lists, and seed lists are immutable. `to_dict()` returns a detached JSON-compatible snapshot. The storage module separately persists a configuration and run manifest.

Hash validation checks format only; matching hashes to real files and verifying runner isolation are future gates. Source strings, environment-variable names, and adapter names are data and are not executed or imported.

## Run the Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

No package installation, credentials, model requests, or game execution are required. See [configuration validation evidence](./41_configuration_validation.md) for the actual execution results and remaining scope.

## Traceability

* [Requirements](./10_requirements.md): FR-001; supporting safeguards for FR-017, FR-018, and NFR-001.
* [Design](./20_design.md): configuration, immutable records, finite limits, and proposed command interfaces.
* [Test plan](./40_testing.md): TC-001 validation assertions; downstream manifest/live execution integration remains pending.

Implementation and tests were prepared with AI assistance and verified through the recorded tests and command checks. Future provider/model, cap, scale, and runtime choices remain pilot decisions.
