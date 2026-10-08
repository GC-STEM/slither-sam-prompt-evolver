# Local Run Storage | Implemented Contract

W-02 now includes validated configuration, frozen run metadata, immutable prompt/sample records, and local integrity inspection. This increment stores supplied text; it does not generate or execute a bot, implement a live provider, or resume a scheduler. [Offline scoring](./13_offline_scoring.md) is implemented separately for declared JSON result bundles.

## Initialize a Run

From the repository root in Bash, using Python 3.12 or later:

```bash
PYTHONPATH=src python -m slither_evolver init \
  --config configs/offline.example.json \
  --provenance synthetic \
  --description "Synthetic configuration fixture; no played games."
```

Expected result: exit `0`, a new `runs/synthetic-config-check/` directory, and a message confirming creation without requests, credentials, or bot execution. The example contains synthetic game identities and limits. Initialization creates an empty evidence store, not a completed experiment. `--runs-dir PATH` changes the parent directory; `runs` is the default.

The provenance kind is required: `synthetic`, `manual`, or `automated`. A nonempty description of at most 2,048 characters is required. These are operator declarations, not independent certification. Never put secrets or participant personal data in notes, prompts, responses, or source artifacts.

An existing run ID is refused, including an incomplete initialization. Open an existing store or use a new run ID rather than overwriting it.

## Inspect Saved Evidence

```bash
PYTHONPATH=src python -m slither_evolver inspect --run runs/synthetic-config-check
```

Expected result: exit `0`, the provenance label, and counts of zero prompts, samples, and artifacts for the empty initialized store. Inspection checks metadata, record relationships, and SHA-256 hashes; it never executes saved JavaScript. It does not prove source authenticity, bot validity, correct game outcomes, or scientific reproducibility.

`validate` retains its existing behavior. `init`/`inspect` return `4` for incompatible/damaged evidence or filesystem failures; malformed configuration returns `2`. Argument errors return `2`; help returns `0`. No command in this increment starts live work.

## Exercise a Complete Synthetic Storage Example

```bash
PYTHONPATH=src python examples/storage_demo.py
```

Expected result: `runs/synthetic-storage-demo/` contains two prompts, two samples, and four unique text artifacts. The script reloads the exact baseline and source text and checks their equality. The raw response/source and empty-response failure are handwritten fixtures. There are no LLM calls, played matches, scores, or experiment findings.

Inspect this example with `PYTHONPATH=src python -m slither_evolver inspect --run runs/synthetic-storage-demo`. Repeating the demo with the same run ID is refused; use `--run-id ANOTHER_ID` or `--runs-dir ANOTHER_DIRECTORY` for a new example.

## Directory and Record Contract

| Location | Contents and checks |
| --- | --- |
| `config.json` | Normalized validated configuration; money uses plain decimal strings, including very small numeric inputs. Frozen once created; byte hash is in the manifest. |
| `manifest.json` | Schema 1, run ID, UTC creation time, configuration hash, fixed source/game/API/system/baseline identities, provider declaration, scoring version, provenance, and manifest hash. Provider may explicitly be null for offline planning. |
| `catalog.json` | Schema 1, manifest hash, prompt/sample IDs and file hashes, and catalog hash. Atomically replaced after each new record; detects missing, altered, or uncommitted record files. Maximum 1 MiB. |
| `prompts/<prompt_id>.json` | Schema envelope, manifest hash, record hash, ID, generation, exact text hash, parent IDs, and operator. Maximum 64 KiB per record. |
| `samples/<sample_id>.json` | Schema envelope, manifest hash, record hash, prompt ID, phase/index, request ID, status/reason, raw response hash, and optional source hash. Maximum 64 KiB per record. |
| `artifacts/<sha256>.txt` | Exact UTF-8 bytes of prompts, responses, and source. Shared identical content is stored once; line endings remain significant. |
| `.write-lock/` | Exclusive lock for cooperating store operations. An existing lock blocks access; it is never automatically removed as stale. |

Prompt/sample IDs use the configuration's 1–64-character ASCII identifier rule, never caller-supplied paths. Managed directories/files must be ordinary filesystem entries; symbolic links are rejected. The store assumes a trusted local parent directory and cooperating callers. This check is not an adversarial filesystem sandbox.

Schema fields are closed; duplicate JSON keys and nonfinite constants are rejected. Configuration/manifest/catalog files are capped at 1 MiB. Artifact limits come from the frozen configuration: prompt characters, source bytes, and response bytes. UTF-8 encoding determines byte sizes.

## Python Interface

```python
from slither_evolver.config import load_config
from slither_evolver.storage import RunStore

config = load_config("my-experiment.json")
store = RunStore.create(
    "runs", config, provenance="synthetic", description="Handwritten test evidence."
)
store.add_prompt("seed0", "Avoid walls and prefer open space.")
record = store.get_prompt("seed0")
reopened = RunStore.open(store.path, expected_config=config)
summary = reopened.verify()
```

`RunStore.create()` revalidates the supplied `RunConfig`, even if a caller manually constructed a dataclass. `open(..., expected_config=config)` requires exact normalized configuration equality, including model/settings, scoring, context, and seeds. `manifest()`, `get_prompt()`, and `get_sample()` return detached dictionaries. `verify()` returns counts and provenance after checking the entire current store. Contract/integrity/I/O failures raise `StorageError`.

`add_prompt(prompt_id, text, generation=0, parents=(), operator="seed")` supports these operators:

| Operator | Stored lineage rule |
| --- | --- |
| `baseline` | Generation zero, no parents, exact configured baseline text hash, one baseline identity per run. |
| `seed` | Generation zero, no parents. |
| `mutation` | One existing parent from an earlier generation. |
| `crossover` | Two distinct existing parents from earlier generations. |

Generations range from zero through `generation_count - 1`. These records describe supplied lineage; no population/search algorithm runs. Equal text under different IDs can share an artifact; population-level distinctness is a future search responsibility. An existing ID accepts an exact repeat idempotently and refuses different content.

To add the real baseline later, supply its exact `text_hash()` as `fixed_context.baseline_prompt_hash` before initialization. The offline configuration example's all-zero placeholder is not a real baseline identity. No fixed context can change inside an existing run.

`add_sample(sample_id, prompt_id, phase=..., sample_index=..., request_id=..., response=..., source=..., status="unvalidated", reason=None)` preserves a caller-supplied result. The prompt must exist. Phase is `optimization` or `holdout`; the zero-based index is less than `samples_per_prompt`. A prompt/phase/index combination and a request ID each have at most one sample record. Exact repetition of the same ID/content is idempotent. Request IDs here do not implement a reservation or retry ledger.

Status `unvalidated` requires nonempty source and no reason. Status `invalid` requires a nonempty reason; source may be null and the raw response may be empty. The store deliberately cannot certify a `valid` bot. The separate scorer accepts declared generation statuses without upgrading these stored records or independently validating source. Phase labels also do not enforce selection freeze or holdout scheduling; those are future coordinator gates.

## Publication and Interrupted Writes

One operation acquires the run lock, verifies current evidence, writes each sibling temporary file, flushes it with `fsync`, and publishes it using filesystem replacement. Initialization publishes the manifest last. Record writes publish referenced artifacts first, then the record, then the catalog as the final commit marker.

An exception before publication removes temporary files when cleanup is possible. A killed process can leave `.pending-*` ordinary files; these unpublished bytes are not counted as evidence. Fully published but unreferenced artifacts can remain after an interrupted write; their hashes are still checked. Original records are never silently repaired or discarded.

A missing manifest, active/stale lock, missing catalog entry, or catalog/record discrepancy blocks verification. Inspect the interrupted run before deciding on repair; this increment supplies no automatic recovery command. It never retries a paid request. Fault tests inject write/flush failures; full process-kill recovery, events, match slots, checkpoint/resume, and request reservation logic remain pending.

File replacement requires a supporting local filesystem. Flushed file data and atomic replacement are tested on the declared Linux environment; complete power-loss durability of directory entries and Windows/macOS execution are not claimed.

## Integrity and Remaining Work

Hashes detect accidental changes, missing indexed records, and incompatible context. They are not signatures: someone who changes both data and hashes can construct a different consistent archive. Source commit/game/API/system identities are declared configuration; only stored baseline text and local artifact bytes are matched in this increment. Actual repository/game provenance verification and full live-generation metadata remain future work.

Offline fitness calculation now exists separately, with JSON output to standard output. [Report exports](./14_reports.md) now archive declared result bundles separately. Provider secret lookup, source execution, request/event/slot ledgers, checkpointing, scheduler resume, holdout freeze, and live cost enforcement remain unimplemented. Raw text is local and unreviewed; the existing `runs/` ignore rule applies to the default path. A custom output path must be kept out of commits by the operator.

See [execution evidence](./42_storage_validation.md) and [the broader test plan](./40_testing.md) for actual results and partial requirement coverage.
