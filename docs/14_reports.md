# Evidence Reports | Implemented Contract

W-02 now includes report building, versioned directory export, and independent recalculation for the scorer's declared JSON result bundles. This implements the offline reporting component of FR-013, FR-022, NFR-004, and NFR-010. It does not authenticate outcomes or establish a completed experiment.

## Run the Synthetic Demo

From the repository root in Bash with Python 3.12 or later:

```bash
PYTHONPATH=src python examples/report_demo.py --output runs/synthetic-report-demo
PYTHONPATH=src python -m slither_evolver verify-report --report runs/synthetic-report-demo
```

Open `runs/synthetic-report-demo/report.md`. Choose a new output directory when repeating the export; existing paths are never overwritten. The checked-in [complete example](../fixtures/reporting/example_report/report.md) and [partial example](../fixtures/reporting/partial_report/report.md) can be reviewed without running commands.

The complete fixture contains handwritten declarations for two prompts, two source samples per prompt and phase, two opponents, three optimization seeds, and two disjoint holdout seeds. Its 40 declared slots are not actual played games. The source and game hashes are synthetic declarations; no provider, bot execution, selection freeze, or fresh generation occurred.

| Phase | Baseline fitness | Selected fitness | Selected minus baseline |
| --- | --- | --- | --- |
| Optimization | 9/20 = 0.45 | 29/40 = 0.725 | 11/40 = 0.275 |
| Holdout | 1/2 = 0.5 | 47/80 = 0.5875 | 7/80 = 0.0875 |

These expectations are [handwritten independently](../fixtures/reporting/comparison.expected.json). The demo compares each exact score/delta before publishing and verifying the archive. A positive synthetic delta is an arithmetic check, not evidence of prompt improvement.

## Command Interface

```bash
PYTHONPATH=src python -m slither_evolver report \
  --config fixtures/reporting/comparison.config.json \
  --results fixtures/reporting/optimization-baseline.results.json \
  --results fixtures/reporting/optimization-selected.results.json \
  --results fixtures/reporting/holdout-baseline.results.json \
  --results fixtures/reporting/holdout-selected.results.json \
  --baseline baseline --selected selected \
  --output runs/synthetic-cli-report
```

Supply one through four `--results` arguments. All bundles must describe the requested baseline/selected prompts and share the validated configuration. Paths and role identifiers are explicit; the component does not infer the winning prompt or open a RunStore automatically.

| Operation / condition | Exit status and behavior |
| --- | --- |
| Successful complete or partial export | `0`; prints provenance and complete/partial declared-evidence status. |
| Successful complete or partial verification | `0`; retains the complete/partial status; does not certify system acceptance. |
| Invalid configuration or unreadable/malformed results JSON | `2`; no export is published. |
| Invalid/incompatible bundle contract, unsafe export, existing output/lock, filesystem or verification failure | `4`; reports the failure on standard error. |
| CLI argument error / help | `2` / `0`. |
| Separate `score` command with valid incomplete evidence | `5`; no final fitness. This differs from successfully exporting an honestly partial report. |

The commands read supplied files and write only the requested report directory and temporary publication files. They do not look up credentials, make requests, launch a game, or execute archived source.

## Input Compatibility and Completeness

The [scoring contract](./13_offline_scoring.md) defines the closed schema, record identities, schedule, statuses, and arithmetic. `validate_results` exposes that structural validation for partial reporting without inventing a score.

The reporter additionally requires:

* Unique prompt/phase bundles; only requested baseline/selected IDs are accepted.
* A stable strategy hash for each prompt across phases.
* The baseline hash matching `fixed_context.baseline_prompt_hash`.
* One declared provenance kind across the comparison; synthetic, manual, and automated bundles are never mixed.
* One frozen configuration and equal configured sample/opponent/seed denominators within each phase.

Missing samples, slots, roles, or phases remain explicit. Infrastructure faults, interruptions, and blocked samples yield partial entries with `score: null`. CSV fitness/rate fields are empty for such entries; Markdown says `Not available`. Observed counts remain visible and never substitute for the scheduled denominator.

A phase delta exists only when both baseline and selected entries are complete and scoreable. A complete optimization comparison may appear in a report whose holdout is unavailable; the overall report remains partial. Completion requires both phases for both roles. When baseline and selection share one ID, each phase is counted once and the delta is explicitly a shared-identity zero. Distinct IDs with the same hash are identified as the same strategy text.

Invalid-generation slots contribute zero credit within the fixed schedule but are counted separately from played matches. Bot faults are played-category losses with a separate count. Missing/infrastructure evidence is never converted into a bot loss. Per-sample and per-opponent diagnostics retain generation validity and outcome counts.

Manual and automated provenance are declarations. This interface requires known configuration seeds and full identities. Observations with unknown seeds need the future guided-import contract and cannot be disguised as deterministic scheduled evidence.

## Archive Contents and Recalculation

| File | Purpose |
| --- | --- |
| `config.json` | Normalized frozen configuration; its exact canonical bytes determine the configuration hash. |
| `evidence/<phase>-<prompt_id>.results.json` | Canonical snapshots of the supplied raw bundle values, retaining notes and slot IDs. Formatting is normalized; original whitespace is not preserved. |
| `report.json` | Report schema version 1: roles, phases, provenance, input hashes, missing evidence, counts, sample/opponent diagnostics, complete scores, exact deltas, and limitations. |
| `report.md` | Human-readable comparisons, counts, sample/opponent tables, blockers, and interpretation limits. |
| `summary.csv` | One row per supplied prompt/phase with fixed and observed counts, generation validity, and complete fitness. |
| `opponents.csv` | Per-opponent identities, denominators, counts, and complete effective rates. |
| `slots.csv` | Slot identities, source/context declarations, phase, sample index, outcome/status/cause/reason. Missing slots are not fabricated. |
| `comparisons.csv` | One row per phase with comparison availability, exact and numeric delta, and shared-identity flag. |
| `files.sha256` | SHA-256 receipt for every other file, including evidence snapshots and derived formats. |

CSV is UTF-8 with a header and LF line endings. JSON retains numeric summaries plus reduced rational strings; no rounding is used to derive a delta. Negative derived deltas remain machine-readable numbers. Import rational-string columns as text when using spreadsheet software.

`verify_report` checks supported paths, inventory, ordinary files/directories, file hashes, and strict JSON/configuration contracts. It rebuilds the model from the archived input files and regenerates every derived file byte for byte, including the receipt. Changing a score or denominator, suppressing a loss, or editing a CSV fails verification even if the receipt was updated to match the edited file. A consistently generated partial archive verifies as partial with unavailable final scores.

Hashes detect damage and disagreement. They are not signatures and cannot prove that a trusted game produced the outcomes. Someone replacing the entire archive and consistently recomputing all files can create a different internally consistent declaration. Trusted slot journals and controller provenance remain future integrations.

## Export Content Checks

Before filesystem writes, the reporter scans configuration and evidence for a synthetic secret marker, recognizable GitHub/provider token shapes, bearer tokens, credential assignments, email addresses, and known credential/participant-identity field names. A match blocks export with a generic error that does not repeat the matched value. `provider.credential_env` may name an environment variable; its contents are never read.

Untrusted Markdown notes are escaped for HTML and Markdown syntax and normalized to one line. CSV reason cells beginning with spreadsheet formula indicators, including leading whitespace, are prefixed with an apostrophe. Archived JSON evidence preserves the original reason value, so verification can reproduce the safe CSV transformation.

The gate is conservative and pattern-based. It does not identify every secret, personal name, or sensitive detail and can reject benign text resembling a credential. It does not silently redact evidence. Review/sanitize the source inputs and create a new export. Human publication review is still required.

## Publication and Recovery Boundaries

The exporter prepares all validated bytes first, uses an exclusive sibling writer lock, writes and flushes a temporary sibling directory, then publishes the directory by rename. Caught write/flush/rename failures remove unpublished temporary files and the owned lock when filesystem cleanup succeeds. Existing output paths are preserved. Reports are immutable by workflow: changes use a new output name.

A killed process can leave a pending directory or lock. Inspect that interrupted export before retrying; there is no automatic repair or resume command. Ordinary file flushing and staged publication do not claim full power-loss durability. Verification rejects links, unsupported paths, and unexpected files/directories. Cooperating exporters use the lock; this is not a security boundary against hostile concurrent filesystem changes.

Each input/archived JSON file is limited to 16 MiB. Other exported files are limited to 64 MiB; the receipt is limited to 8 KiB. Exports exceeding the JSON reload limit are rejected before publication. This component is intended for small local experiments, not unbounded datasets.

## Scope and Next Increment

The offline configuration/store/scorer/report component slice is verified. The scorer's declared acceptance/outcome labels do not upgrade the RunStore's unvalidated source records. Slot persistence, trusted replay events, source execution, provider adapters, usage/cost/time evidence, lineage reporting, selection freeze/fresh holdout enforcement, scheduler recovery, and real session results remain pending.

The next independently testable increment is W-03 guided import and inert recorded-result presentation. It should retain provenance, distinguish unknown manual seeds, and reuse these report contracts without executing supplied bot source. Real observation/replay bundles must be collected later; synthetic examples remain clearly labeled.
