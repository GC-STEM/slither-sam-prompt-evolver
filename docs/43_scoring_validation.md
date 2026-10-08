# Offline Scoring | Execution Evidence

**Increment:** W-02, pure offline scoring after configuration and storage.

**Execution date:** October 7, 2026, America/New_York.

**Inspected repository baseline:** `1f51886de471a86f1396b83ea1249f1f127b494f`. This is the pushed storage implementation before the scoring change. The delivered file manifest identifies the new bytes; no GitHub commit or pull request containing this change is claimed.

## Environment and Procedure

* Ubuntu 24.04.3 LTS, Linux x86_64, Python 3.12.14.
* Standard-library Python implementation and `unittest`; no additional runtime/test packages.
* Declared synthetic configurations, generation records, and outcomes only.
* No credentials, provider requests, bot execution, or actual games.
* Windows/macOS execution and live pipeline integration: unverified.

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

**Actual result:** 87 tests passed, zero failures, zero errors, and zero skipped tests. The suite comprises 26 configuration tests, 35 storage tests, and 26 scoring tests, with additional subcases. These are component tests, not 87 completed system acceptance procedures.

## Independent Arithmetic Evidence

| Case | Independent expectation | Actual result |
| --- | --- | --- |
| Design example: 46/50, 44/50, 45/50, 10/50 | Overall 145/200 = 29/40; worst 1/5; fitness 227/400 = 0.5675 | Exact counts/fractions and float values matched. |
| All wins | Fitness 1 with configured 0.70/0.30 weights | Passed. |
| All played losses or draws | Fitness 0 | Passed. |
| All invalid generations | Fitness 0, 12 synthetic exposures, zero played-category matches | Passed. |
| One invalid sample, accepted sample with 4 wins/2 losses | 12 scheduled slots; 6 played-category matches; 6 synthetic failures; fitness 17/60 | Passed. |
| One bot fault among 12 otherwise winning trials | 11 wins, 1 loss, 1 separate bot fault; fitness 107/120 | Passed. |
| Configured overall-only, worst-only, and 0.20/0.80 weights | Fitness 11/12, 5/6, and 17/20 for the one-loss schedule | Passed. |
| Near-unit weights within the configuration's permitted sum tolerance | Exact supplied all-win weight sum 2000000001/2000000000; no silent normalization | Passed. |

All cases above are synthetic arithmetic declarations. Played-category labels in fixtures do not mean actual games occurred. Expected values were calculated from counts/fractions independently of the scorer.

## Contract and Failure Evidence

* Missing sample declarations and missing slot results block final fitness; the exception carries missing/blocked counts and has no fitness attribute.
* Infrastructure faults, interrupted slots, and blocked generation prevent fitness even when the coordinate schedule is otherwise complete.
* Invalid generations retain their full denominators and cannot claim played outcomes. Accepted samples cannot claim invalid-generation exposures.
* Duplicate sample IDs/indices or slot coordinates, unknown samples/opponents, mismatched hashes, stale configuration/run identity, wrong phase seeds, unknown schema fields/versions, invalid outcomes/causes, and contradictory statuses are rejected.
* Optimization and holdout use their separate configured seed sets; this does not establish freeze/fresh-generation behavior.
* Input order does not change the result; input dictionaries are not mutated. Result dataclasses are immutable and JSON snapshots are detached.
* Slot identity matches the documented canonical byte protocol; scorer configuration hashes match persisted RunStore manifest hashes.
* A huge configured expected schedule produces an incomplete-evidence count without allocating the Cartesian product.
* JSON loading rejects duplicates, nonfinite constants, invalid syntax/encoding, excessive decoder depth, oversized files, and unreadable paths.
* Mocked environment lookup, network sockets, and subprocess execution remain unused during scoring.

## Command and Fixture Checks

```bash
PYTHONPATH=src python examples/scoring_demo.py
PYTHONPATH=src python -m slither_evolver score \
  --config fixtures/scoring/design_example.config.json \
  --results fixtures/scoring/design_example.results.json
```

Actual results: both commands returned `0`. The demo matched [handwritten expectations](../fixtures/scoring/design_example.expected.json). The CLI emitted a single parseable JSON object with synthetic provenance, 200 declared scheduled exposures, fitness `0.5675`, and exact fraction `227/400`.

CLI tests additionally verified invalid input exit `2` and incomplete evidence exit `5`. A blocked command emits no score JSON on standard output and identifies the blocker on standard error. Existing configuration/storage tests continue to pass.

## Requirement and System-Test Status

| Requirement / Procedure | Completed assertions and remaining boundary |
| --- | --- |
| FR-010 / TC-010 | Offline arithmetic, weights, denominators, draws, bot faults, and synthetic-generation policy passed. Trusted outcome production and integrated runner scoring remain pending. |
| FR-008 / TC-008 | Exact coordinate/phase completeness and duplicate rejection passed. Automatically constructing equal candidate schedules remains pending. |
| FR-019 / TC-019 | Declared bot/invalid-generation versus infrastructure policies passed. Injecting actual provider/runner failures remains pending. |
| NFR-006 / TC-028 | Configuration/storage/scorer contracts execute offline. Provider, search, scheduler, and remaining component contracts remain pending. |
| NFR-010 / TC-032 | Counts, weights, exact ratios and input fixtures support independent recalculation; missing/contradictory records are blocked/rejected. Full exported run report, slot journal integrity and suppression detection remain pending. |
| FR-002 / TC-002 | `score` success/error/blocked CLI behavior passed alongside the earlier offline commands. Planned experiment workflow commands remain pending. |

W-02 still needs the report workflow and its complete evidence integration. No automated experiments, live-provider integration, actual game outcomes, isolation/parity, evolution, freeze/fresh holdout comparison, guided import, or system acceptance occurred.

## Review and Limitations

Code, record validation, independent arithmetic, and negative cases were reviewed against the design. AI assistance was used for implementation/test preparation. No independent human code review is claimed. Full files and fixtures are supplied for review and local integration.

The scorer trusts caller-declared provenance, prompt/source identities, accepted generations, and outcomes after structural checks. Hashes bind context and coordinates; they are not signatures or proof that a trusted game produced a result. Synthetic labels must remain in derived summaries. True independent sampling and actual source authenticity belong to future provider/validator/runner integration.

This increment produces a JSON component summary to standard output, not the planned Markdown/CSV report or a complete saved experiment archive. It does not persist slots in RunStore, authenticate raw evidence, repair incomplete data, certify game isolation, reserve spending, or enforce selection freeze. These boundaries remain recorded as future work.
