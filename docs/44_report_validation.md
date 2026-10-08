# Report Export and Recalculation | Execution Record

This record documents the reporting component increment of W-02. It supplements the SDLC [test plan](./40_testing.md) and [report contract](./14_reports.md). It is an actual offline software verification record, not a system acceptance report or a prompt-evolution finding.

## Baseline, Environment, and Scope

The pushed GitHub `main` baseline was freshly read at commit `430ddbf42d7ba348f9b1546e05f2cba18a1ecc73`. The fetched configuration/storage/scoring implementation and documentation matched the preceding delivered increment. The current SDLC baseline is revision 0.1.4. Original game/course resources and licensing remain in the repository.

Verification occurred on 2026-10-08 with Ubuntu 24.04.3, Linux, and Python 3.12.14. The implementation and tests use the Python standard library. No provider credentials, paid requests, actual matches, or generated-source execution were involved. Windows/macOS and the browser/game workflow remain unverified.

Implemented code: `reports.py`, report/verify-report CLI dispatch, and public structural `validate_results` for partial evidence. New fixtures contain independently handwritten optimization/holdout comparisons. Complete and partial example archives are supplied for review. The duplicate Offline Scoring section in the pushed README was consolidated while adding reporting instructions.

## Test Command and Actual Outcome

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Actual outcome: **122 tests passed**, with no failures or errors.

| Component | Passing tests |
| --- | --- |
| Configuration | 26 |
| Local storage | 35 |
| Offline scoring | 26 |
| Reporting | 35 |
| Total | 122 |

The initial reporting check found two incorrect new test assertions: an unnecessary assumed hyphen escape and a incorrectly constructed partial CLI argument list. Those assertions were corrected; the complete regression suite then passed. No pre-existing component regression was found.

## Reporting Assertions Executed

| Area | Actual verification |
| --- | --- |
| Independent arithmetic | All four fitness fractions matched handwritten expectations; phase deltas matched 11/40 and 7/80. |
| Consistent formats | JSON, Markdown, summary/opponent/slot/comparison CSV agree; 40 declared slots, 8 opponent rows; all files regenerate from archived inputs. |
| Partial evidence | Missing slot/sample/role/phase, infrastructure faults, and interruptions retain blockers and suppress affected final scores/rates/deltas. Correctly derived partial archives verify only as partial. |
| Failure categories | Invalid generation retains scheduled denominators and separate synthetic counts; bot timeout remains a played-category loss; infrastructure faults do not become losses. |
| Compatibility | Wrong configuration, malformed outcomes, duplicate slots/bundles, unrequested prompts, frozen-baseline mismatch, changed strategy hashes between phases, and mixed provenance are rejected. |
| Selection identity | Shared baseline/selection is counted once per phase; same strategy hash under distinct IDs is explicit. |
| Model ownership | Returned reports are detached; input documents remain unchanged. Bundle argument order produces identical exports. |
| Export content | Known synthetic/token/bearer/credential/email/field markers block before writes without echoing matched values. HTML/Markdown notes are escaped; spreadsheet formula reasons are escaped while raw archived values remain unchanged. |
| Filesystem publication | Existing output is preserved; stale lock remains available for inspection; injected flush/rename errors leave no final partial directory and clean owned temporary state. |
| Integrity and recomputation | Changed/deleted/extra files, links, unexpected directories, traversal/duplicate/oversized receipt entries are rejected. Rehashed score/denominator/CSV changes and a suppressed loss still fail recalculation checks. |
| Offline boundary | Network socket creation, credential lookup, and subprocess execution were patched to fail during export/verification; the workflow still passed. |
| CLI behavior | Complete/partial export and verification return 0 with explicit status; existing output returns 4. Incomplete standalone scoring still returns 5 without final fitness. |

## Commands and Reviewed Example Outputs

```bash
PYTHONPATH=src python examples/report_demo.py --output fixtures/reporting/example_report
PYTHONPATH=src python -m slither_evolver verify-report --report fixtures/reporting/example_report
PYTHONPATH=src python examples/scoring_demo.py
PYTHONPATH=src python examples/storage_demo.py
```

All returned `0`. The report demo checked each exact fitness/delta against the handwritten expectation file, exported the complete archive, and independently reconstructed it. The CLI verification retained synthetic provenance and complete declared-evidence status. Earlier scoring and storage demos continued to pass.

A separate report CLI smoke check exported all four bundles into a fresh directory and verified them. A partial smoke check exported one baseline optimization bundle with one missing slot; export/verification returned `0` with partial status and no final fitness. The checked-in [complete report](../fixtures/reporting/example_report/report.md) and [partial report](../fixtures/reporting/partial_report/report.md) retain the synthetic warning and interpretation limits.

## Requirement and System-Test Status

| Requirement / procedure | Completed component evidence and remaining boundary |
| --- | --- |
| FR-013 / TC-013 | Complete/partial Markdown, JSON, CSV, baseline comparisons, sample/opponent counts, and interpretation limits passed. Full actual experiment archive remains pending. |
| FR-022 / TC-022 | Declared phase schedules, frozen baseline hash, stable strategy hashes and comparison availability passed. Actual selection freeze and independent fresh holdout generation remain pending. |
| FR-019 / TC-019 | Reporting retains bot, synthetic-generation, infrastructure and interruption categories. Producing trusted runner/provider fault evidence remains pending. |
| NFR-004 / TC-026 | Known-marker/email/field export gate passed. Exhaustive sanitization is not claimed; human publication review remains pending. |
| NFR-010 / TC-032 | Archived evidence recalculates all formats; derived tampering and loss suppression are detected. Hashes are not signatures or trusted-outcome authentication. |
| NFR-002 / TC-024 | Injected export flush/publication failures passed alongside earlier storage checks. Process-kill/power-loss/full scheduler recovery remains pending. |
| NFR-006 / TC-028 | Config/store/scorer/reporter execute offline. Remaining provider/runner/search/coordinator contracts are pending. |
| FR-002 / TC-002 | Six offline command paths are implemented and tested. Planned experiment/guided/replay/resume command paths remain pending. |

W-02's offline fixture report component slice is verified. Integrated request/event/slot journals, checkpoints, and full recovery remain pending. W-03 guided import and inert recorded-result presentation is the next independent increment. No live automation, game isolation/parity, real recorded session bundle, or passing system acceptance is claimed.

## Review and Limitations

The implementation, arithmetic oracles, derived formats, and negative cases were reviewed against the requirements/design. AI assistance was used for implementation, tests, and documentation. Independent human code review, keyboard/screen-reader rehearsal, and real session evaluation have not occurred.

The result schema lacks actual usage/cost/time, full provider metadata and lineage, raw source bytes, trusted replay events, and authenticated match outcomes. Reports explicitly identify those limitations. Completing the full portfolio demonstration still requires genuine observed or trusted automated evidence, participant/facilitator rehearsal, and publication review.
