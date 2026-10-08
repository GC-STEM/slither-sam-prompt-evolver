"""Export and verify handwritten synthetic comparisons; no game is played."""

import argparse
import json
from pathlib import Path

from slither_evolver.config import load_config
from slither_evolver.reports import build_report, export_report, verify_report
from slither_evolver.scoring import load_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="runs/synthetic-report-demo",
                        help="New directory; use a different name when repeating the demo.")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parents[1] / "fixtures/reporting"
    config = load_config(directory / "comparison.config.json")
    bundles = [load_results(directory / f"{phase}-{role}.results.json")
               for phase in ("optimization", "holdout") for role in ("baseline", "selected")]
    expected = json.loads((directory / "comparison.expected.json").read_text(encoding="utf-8"))
    report = build_report(config, bundles, baseline_id="baseline", selected_id="selected")
    for entry in report["entries"]:
        key = f"{entry['phase']}-{entry['prompt_id']}"
        if entry["score"]["fitness_fraction"] != expected["fitness_fractions"][key]:
            raise ValueError("Synthetic fitness expectation failed")
    for row in report["comparisons"]:
        if row["fitness_delta_fraction"] != expected["delta_fractions"][row["phase"]]:
            raise ValueError("Synthetic comparison expectation failed")
    export_report(args.output, config, bundles, baseline_id="baseline", selected_id="selected")
    verified = verify_report(args.output)
    if verified["status"] != expected["status"] or verified["provenance"] != expected["provenance_kind"]:
        raise ValueError("Synthetic export verification failed")
    print(f"Synthetic report exported and recalculated: {args.output}")
    print("Handwritten deltas: optimization 11/40; holdout 7/80. No actual experiment findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
