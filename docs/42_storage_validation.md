# Local Run Storage | Execution Evidence

**Increment:** W-02, local storage after configuration validation.

**Execution date:** October 7, 2026.

**Inspected repository baseline:** `77a7ee2985f55c8b23273540cec1805d515b1b49`, including the operator's Markdown lint corrections and removal of the unused program template. This baseline is the source before the storage change, not a commit containing this implementation. The delivered file manifest identifies the new bytes.

## Environment and Procedure

* Ubuntu 24.04.3 LTS, Linux x86_64, Python 3.12.14.
* Standard-library implementation and `unittest`; no third-party runtime or test dependencies.
* Temporary local directories and explicitly synthetic fixtures; no provider credentials, model requests, or bot execution.
* Windows/macOS execution, network filesystem behavior, and power-loss durability: unverified.

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

**Actual result:** 61 tests passed, zero failures, zero errors, and zero skipped tests. This is 26 configuration tests plus 35 storage tests, with additional subcases. These are component tests, not 61 completed system acceptance procedures.

## Verified Storage Behavior

* Configuration is revalidated, saved, and reloaded as an immutable record; the manifest preserves declared fixed context, provider settings or explicit null, scoring version, and evidence provenance.
* Existing run IDs are refused. Prompt/sample IDs accept exact repeats and refuse conflicting content.
* Exact Unicode text, raw responses, source, and line endings survive save/reload. Identical artifacts are stored once.
* Baseline text must match its frozen hash. Prompt generations and parent/operator relationships are checked, including mutation and crossover lineage.
* Sample records require an existing prompt, known phase, bounded index, unique prompt/phase/index and request ID, supported unvalidated/invalid status, and appropriate source/failure reason.
* Prompt character limits and UTF-8 source/response byte limits are enforced before new records are published.
* Changed/missing artifacts, missing indexed prompt/sample records, altered metadata, cross-manifest records, unknown fields/schema versions, and malformed/oversized JSON block verification.
* Changed context, scoring, or model declaration rejects `open(expected_config=...)`.
* Managed symbolic-link artifacts are rejected; the test ran successfully on the declared Linux environment.
* Active/stale locks block access. Injected flush/publication failures do not certify partial bytes. Failure between record publication and catalog commit blocks inspection rather than inventing completion.
* Manifest snapshots and returned records are detached from stored records.
* Mocked environment lookup, socket construction, and subprocess execution remain unused while saving/reloading supplied bot text.
* Small numeric monetary inputs round-trip as plain decimal strings. This increment fixes the prior serializer's exponent-string mismatch with its own configuration contract.

## Command and Demo Checks

The synthetic demo ran in a disposable directory and then passed inspection:

```bash
PYTHONPATH=src python examples/storage_demo.py --runs-dir TEMP_DIRECTORY
PYTHONPATH=src python -m slither_evolver inspect --run TEMP_DIRECTORY/synthetic-storage-demo
```

Actual results: both commands returned `0`. The demo reloaded the exact baseline and source text. Inspection reported **2 prompts, 2 samples, and 4 artifacts**, with provenance **synthetic**. The dummy source was not executed, and these counts contain no played-game results.

CLI component tests also verified initialization `0`, inspection `0`, repeated initialization `4`, and invalid configuration `2`. Original validation-command tests continue to pass.

## Requirement and System-Test Status

| Requirement / Procedure | Actual evidence and remaining boundary |
| --- | --- |
| FR-001 / TC-001 | Validation and local normalized manifest creation passed. Enforcing validation at future execution/request entry points remains pending. |
| FR-002 / TC-002 | Offline validate/init/inspect contracts passed. Pilot/evolve/guided/replay/report/resume commands remain pending. |
| FR-003 / TC-003 | Frozen baseline text, supplied lineage, and incompatible store-open rejection passed. Scheduler resume and actual game/model context provenance remain pending. |
| FR-021 / TC-021 | Local manifest/config/artifact/catalog hashes, required fields and record relationships passed. Actual provider usage/request provenance and repository/game source verification remain pending. |
| NFR-002 / TC-024 | Injected initialization/flush/record/catalog fault handling and idempotent component writes passed. Process-kill, event/slot/checkpoint recovery and uncertain paid-request reconciliation remain pending. |

Other system test procedures remain Not run. W-02 still needs the scorer and fixture report. No live experiments, tournaments, provider integration, game isolation/parity, holdout comparison, or system acceptance took place.

## Review and Limitations

Implementation and negative/fault cases were reviewed together with the frozen design. AI assistance was used for code and test preparation; no independent human code review is claimed. Full files are supplied for review and local integration.

Integrity inspection is not authentication, source validation, export secret scanning, or a game safety boundary. Operator-provided provenance labels and configured source hashes are declarations. Raw text remains unreviewed local evidence.

No automatic repair or recovery command exists. Missing manifest/catalog entries and stale locks require investigation. Atomic file publication and flushed data are tested; multi-file transaction recovery and complete power-loss durability are not established. An interrupted run must not be described as complete.
