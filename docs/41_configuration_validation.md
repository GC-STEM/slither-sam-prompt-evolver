# Configuration Validation | Execution Evidence

**Increment:** W-02, configuration validation only.

**Execution date:** October 7, 2026.

**Inspected repository baseline:** `8b416c15097c9b47b7855e2c47c9bbd6a07418f6`.

The implementation is the configuration-validation change containing this report. Tests import that source directly. The eventual pull-request commit identifies the complete reviewable change; it is not the inspected baseline commit above.

## Environment and Procedure

* Ubuntu 24.04.3 LTS, Linux x86_64, Python 3.12.14.
* Standard-library `unittest`; no third-party test dependencies.
* Synthetic fixture: `configs/offline.example.json`.
* Actual Windows and macOS execution: unverified.

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

**Actual result:** 26 tests passed, zero failures and zero errors on the final execution. The suite uses additional subcases for invalid counts, fields, limits, seeds, and budgets. These are implementation tests, not 26 completed procedures from the broader system test plan.

## Verified Behavior

* Valid offline configuration loads into an immutable record and round-trips through a detached JSON snapshot.
* Unknown/missing fields, unsupported versions, invalid count types, and invalid search/scoring settings are rejected.
* Optimization and holdout seeds are nonempty, unique, bounded and disjoint.
* Opponent identities and hash formats are checked; deadlines and resource values are validated.
* Live-readiness checks require provider/model settings and explicit finite spending/request controls.
* Decimal spending amounts retain precision; per-request bound cannot exceed total spending cap.
* Nested provider data is immutable; common credential fields are rejected without echoing their values.
* Validation performs no environment credential lookup or network connection, including the live-readiness check.
* Strict JSON loading rejects duplicate fields, nonfinite constants, oversized input, excessive setting depth, and malformed/invalidly encoded files.
* CLI success/error paths return the documented exit statuses.

## Command Checks

| Check | Actual Result |
| --- | --- |
| `python -m slither_evolver validate --config configs/offline.example.json` with `PYTHONPATH=src` | Exit 0; reports valid offline configuration and no external work. |
| Same command with `--live` | Exit 2; reports missing provider, as intended for this undecided example. |
| `python -m slither_evolver --help` with `PYTHONPATH=src` | Exit 0; lists the implemented validation command. |

## Requirement and Test Status

FR-001's validator and TC-001's configuration assertions are implemented and verified. Integration that proves every future model request/bot execution passes through validation is still pending. Returning normalized configuration is verified; creation of a full persistent run manifest is not implemented.

Budget reservation/enforcement, source/hash integrity checks, game isolation/parity, storage, scoring, reports, generation, evolution, guided import, and recorded replay are not verified by this increment. All remaining system procedures in the test plan remain Not run. No live requests or tournaments occurred.

## Review and Limitations

Implementation, negative cases and command behavior were reviewed together with the requirements. AI assistance was used in coding and test preparation; there was no independent human code review during this execution. The draft pull request is the review point.

Known-secret-key rejection and hash-format checks do not establish full secret detection, authenticity, valid pricing, or safe generated-code execution. Those boundaries require their own future implementations and tests.
