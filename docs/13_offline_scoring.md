# Offline Scoring | Implemented Contract

W-02 now includes a pure scorer and versioned sample/slot-result records. The scorer validates a declared schedule and calculates the design's effective scheduled-trial fitness. It does not schedule games, validate bot code, generate samples, resume a run, or certify actual outcomes.

## Run the Synthetic Example

From the repository root in Bash with Python 3.12 or later:

```bash
PYTHONPATH=src python examples/scoring_demo.py
```

Expected output includes `overall=0.725; worst=0.2; fitness=0.5675 (227/400)`. The demo compares the scorer with handwritten expectations. All inputs are synthetic; no actual matches or model requests occurred.

To obtain the full JSON scoring summary:

```bash
PYTHONPATH=src python -m slither_evolver score \
  --config fixtures/scoring/design_example.config.json \
  --results fixtures/scoring/design_example.results.json
```

Success returns `0` and writes one valid JSON object to standard output. Invalid configuration, malformed/incompatible results, or unreadable results return `2`. Valid but incomplete/infrastructure-blocked evidence returns `5`, writes an explanation to standard error, and emits no final score to standard output. Argument errors return `2`; help returns `0`. The command writes no files, reads no credentials, and executes no bot source.

The new `score` command supplements `validate`, `init`, and `inspect`. The separate [report workflow](./14_reports.md) now exports Markdown/JSON/CSV and recalculates archived declared evidence. Result bundles are separate JSON inputs; the current RunStore catalog still covers prompts/samples only. Persisting match-slot journals and integrating the store with a coordinator remain future work.

## Versioned Results Bundle

The complete runnable example is [design_example.results.json](../fixtures/scoring/design_example.results.json). Schema fields are closed at every record level.

| Top-level field | Contract |
| --- | --- |
| `schema_version` | Integer `1`; booleans are not integers. |
| `run_id` | Must equal the validated configuration's run ID. |
| `configuration_hash` | SHA-256 of the normalized configuration's UTF-8 JSON bytes, with sorted keys, two-space indentation, unescaped Unicode, and one final newline. This matches the RunStore configuration hash convention. |
| `prompt_id`, `prompt_hash` | 1–64-character ASCII identifier and lowercase 64-character SHA-256 declaration of the strategy prompt. The scorer does not load prompt bytes. |
| `phase` | `optimization` or `holdout`; selects exactly the corresponding configuration seed set. |
| `provenance` | Required object containing `kind` (`synthetic`, `manual`, or `automated`) and nonempty `description` of at most 2,048 UTF-8 characters. Labels are operator declarations, not independent certification. |
| `samples` | List of independent sample declarations using the record below. A complete comparison has exactly K unique IDs/indices. |
| `results` | List of versioned slot-result records. A final score requires every configured sample/opponent-profile/seed coordinate exactly once. |

Files are capped at 16 MiB. The loader rejects duplicate JSON fields, NaN/Infinity constants, invalid encoding/syntax, and excessive decoder depth. The scorer checks all field types and ranges. Source/prompt/profile hashes and provenance are declarations; this format alone cannot authenticate evidence.

### Sample Declaration

Each sample has exactly `sample_id`, `sample_index`, `source_hash`, `generation_status`, and `reason`.

* `sample_id` follows the ASCII identifier rule; IDs are unique within the bundle.
* `sample_index` is an integer from zero through K minus one; indices are unique.
* `accepted` generation status requires a lowercase SHA-256 source hash and null reason. This is a caller's declaration of accepted generation, not a validation performed by this scorer.
* `invalid` requires a nonempty reason of at most 2,048 characters; source hash may be null or a declared SHA-256. Every scheduled exposure must then be `invalid_generation`.
* `blocked` requires a nonempty reason and null source hash. Its exposures can only be infrastructure faults or interruptions; a blocked sample prevents final fitness.

Different samples may coincidentally have the same source hash. Independent model requests and source validity must be established by the future provider/validator pipeline. Raw responses and source text remain the evidence store's responsibility.

### Slot Result

Each result has exactly `slot_id`, `sample_id`, `opponent_id`, `opponent_source_hash`, `profile_hash`, `seed`, `status`, `outcome`, `cause`, and `reason`.

Sample/opponent IDs must exist. Opponent source/profile hashes must match the configuration. The seed must be an integer in the selected phase's configured set. Unknown seeds, mixed phase schedules, unknown references, duplicates, and mismatched identities are errors, not omitted observations.

| Status | Outcome | Cause / reason | Scoring policy |
| --- | --- | --- | --- |
| `played` | `win`, `loss`, or `draw` | Both null | Win gives one win; loss/draw zero. Included in played-category counts. |
| `bot_fault` | `loss` | `exception`, `illegal_direction`, or `decision_timeout`; nonempty reason | Played-category loss, with a separate bot-fault count. |
| `invalid_generation` | Null | `generation_contract`; nonempty reason | Synthetic zero-credit exposure, requires an invalid sample, never a played match. |
| `infrastructure_fault` | Null | `provider`, `runner`, `storage`, or `isolation`; nonempty reason | Blocks final fitness; never a loss. |
| `interrupted` | Null | `operator_interrupt`; nonempty reason | Blocks final fitness; never a loss. |

Nonempty reasons are capped at 2,048 characters. A `played`/`bot_fault` result requires an accepted sample; invalid and blocked sample declarations cannot claim these outcomes. An accepted sample cannot claim an invalid-generation exposure.

The stable slot ID is SHA-256 of the same canonical JSON convention applied to this ordered array:

```text
[1, configuration_hash, prompt_id, prompt_hash, phase,
 sample_id, sample_source_hash_or_null, opponent_id, seed]
```

`slot_id(...)` constructs this ID; the parser validates coordinates and recomputes it. Opponent/profile/game/model identities are included through the complete configuration hash. This helper assigns an identity; it does not schedule or execute a trial.

## Completeness and Formula

For the chosen phase, let K be configured samples, S be configured seeds, and O be opponent/profile combinations. Each opponent has denominator N = K × S; the complete schedule has K × S × O slots.

Unique in-bounds sample indices and result coordinates plus the exact required counts establish the complete Cartesian schedule. The scorer does not need to allocate a second copy of that schedule. Missing sample declarations or results block fitness. Infrastructure faults, blocked samples, and interruptions also block fitness even when a result record exists for every coordinate.

For opponent o, R_o = wins_o / N_o. Overall R = total wins / total scheduled slots; worst R_min = min(R_o). Scoring version 1 uses the frozen configured weights:

```text
fitness = overall_weight × R + worst_weight × R_min
```

Invalid-generation exposures retain their scheduled denominators. Played draws and bot faults contribute no wins. The configuration's weight validation allows its documented 1e-9 sum tolerance; the scorer uses supplied weights exactly, without renormalizing or clamping them. Near-unit weights can therefore produce a correspondingly near-unit all-win score.

The implementation uses exact rational arithmetic from the normalized weight values. JSON outputs include floats and reduced `numerator/denominator` strings for overall rate, worst rate, fitness, and every opponent rate. No display rounding changes the calculation.

## Summary and Python Interface

```python
from slither_evolver.config import load_config
from slither_evolver.scoring import load_results, score_results

config = load_config("my-experiment.json")
summary = score_results(config, load_results("my-results.json"))
snapshot = summary.to_dict()
```

The immutable `FitnessResult` includes identity/provenance, scoring version, weights, accepted/invalid sample counts, accepted-sample fraction, total/per-opponent denominators, played-category wins/losses/draws, bot faults, synthetic exposures, and exact/float rates and fitness. `to_dict()` returns a detached JSON-ready snapshot; neither inputs nor result records are mutated.

Malformed or incompatible inputs raise `ScoringError`. Valid but incomplete evidence raises `IncompleteEvidence` with counts of missing samples/slots, blocked samples, infrastructure faults, and interruptions. That exception has no fitness value. Configuration is revalidated before scoring, including manually constructed dataclasses.

In a synthetic bundle, even a `played`-category count is a fixture declaration, not an actual played game. The provenance label must remain attached to every derived summary. Do not publish raw notes or artifacts containing credentials or participant data; this scorer is not an export secret scanner.

## Arithmetic Fixture and Remaining Work

The fixture has two declared samples, four synthetic opponents, and 25 optimization seeds: 50 exposures per opponent and 200 total. Handwritten wins are 46, 44, 45, and 10. Thus total wins = 145, overall = 145/200 = 29/40, worst = 10/50 = 1/5, and fitness = (7/10)(29/40) + (3/10)(1/5) = 227/400 = 0.5675.

[design_example.expected.json](../fixtures/scoring/design_example.expected.json) contains handwritten expected values; it is not generated by the scorer. These workload values and hashes are arithmetic fixtures, not selected pilot defaults or experiment findings.

Trusted outcome production, bot interface validation, actual source provenance, live generation, automatic scheduling, slot persistence, freeze/fresh holdout enforcement, search, and checkpoint/resume remain pending. Markdown/JSON/CSV reporting now exists separately for declared bundles; it does not establish those pipeline controls. Holdout scoring supports its separate seed set but does not enforce selection freeze or prevent later tuning.

See [execution evidence](./43_scoring_validation.md) and the [broader test plan](./40_testing.md) for completed assertions and remaining system procedures.
