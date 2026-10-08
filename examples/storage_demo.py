"""Save explicitly synthetic evidence; never request a model or execute bots."""

import argparse
import json
from pathlib import Path
import sys

from slither_evolver.config import ConfigError, validate_config
from slither_evolver.storage import RunStore, StorageError, text_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--run-id", default="synthetic-storage-demo")
    args = parser.parse_args()
    baseline = "Synthetic baseline: prefer open space.\n"
    source = "function playerAI(player) { return 'UP'; }\n"
    example = Path(__file__).resolve().parents[1] / "configs" / "offline.example.json"
    try:
        document = json.loads(example.read_text(encoding="utf-8"))
        document["run_id"] = args.run_id
        document["fixed_context"]["baseline_prompt_hash"] = text_hash(baseline)
        store = RunStore.create(
            args.runs_dir, validate_config(document), provenance="synthetic",
            description="Handwritten fixture prompts and sample text; no LLM requests or played games.",
        )
        store.add_prompt("baseline", baseline, operator="baseline")
        store.add_prompt("child", "Synthetic variant: avoid walls first.\n",
                         generation=1, parents=["baseline"], operator="mutation")
        store.add_sample("sample0", "baseline", phase="optimization", sample_index=0,
                         request_id="synthetic-request0", response=source, source=source)
        store.add_sample("sample1", "baseline", phase="optimization", sample_index=1,
                         request_id="synthetic-request1", response="", source=None,
                         status="invalid", reason="Synthetic empty-response fixture")
        reopened = RunStore.open(store.path, expected_config=store.config)
        assert reopened.get_prompt("baseline")["text"] == baseline
        assert reopened.get_sample("sample0")["source"] == source
        print(f"Saved and reloaded synthetic evidence: {store.path}")
        print(json.dumps(reopened.verify(), sort_keys=True))
        print("No model requests, bot execution, matches, scores, or experiment findings.")
    except (ConfigError, StorageError, OSError) as error:
        print(f"Demo error: {error}", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
