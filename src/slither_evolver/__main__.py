"""Validate settings, preserve evidence, score results, and export local reports."""

import argparse
import json
import sys

from slither_evolver.config import ConfigError, load_config
from slither_evolver.storage import RunStore, StorageError
from slither_evolver.scoring import IncompleteEvidence, ScoringError, load_results, score_results
from slither_evolver.reports import ReportError, export_report, verify_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m slither_evolver",
        description="Validate, preserve, score, and report local Slither Sam evidence.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Check JSON without making requests or running bots.")
    validate.add_argument("--config", required=True, help="Path to schema-version-1 experiment JSON.")
    validate.add_argument("--live", action="store_true",
                          help="Require future live-request controls; does not start live work.")
    initialize = commands.add_parser("init", help="Create a frozen local run; no requests or bot execution.")
    initialize.add_argument("--config", required=True, help="Path to schema-version-1 experiment JSON.")
    initialize.add_argument("--runs-dir", default="runs", help="Parent directory for local runs (default: runs).")
    initialize.add_argument("--provenance", required=True, choices=("synthetic", "manual", "automated"),
                            help="Declare the origin of the evidence; this label is not independent verification.")
    initialize.add_argument("--description", required=True, help="Short provenance note; never include secrets.")
    inspect = commands.add_parser("inspect", help="Verify stored hashes/relationships without running bots.")
    inspect.add_argument("--run", required=True, help="Path to an existing run directory.")
    score = commands.add_parser("score", help="Score a complete declared result schedule; no bot execution.")
    score.add_argument("--config", required=True, help="Path to the frozen experiment configuration.")
    score.add_argument("--results", required=True, help="Path to a schema-version-1 results bundle.")
    report = commands.add_parser("report", help="Export declared evidence as Markdown, JSON, and CSV.")
    report.add_argument("--config", required=True, help="Frozen experiment configuration.")
    report.add_argument("--results", required=True, action="append", help="Results bundle; repeat for each prompt/phase.")
    report.add_argument("--baseline", required=True, help="Frozen baseline prompt identifier.")
    report.add_argument("--selected", required=True, help="Selected prompt identifier.")
    report.add_argument("--output", required=True, help="New report directory; existing paths are never overwritten.")
    verify = commands.add_parser("verify-report", help="Check hashes and recompute all exported formats.")
    verify.add_argument("--report", required=True, help="Existing report directory.")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify-report":
            summary = verify_report(args.report)
            print(f"Report checks passed: {summary['run_id']} ({summary['provenance']}; {summary['status']} declared evidence).")
        elif args.command == "inspect":
            summary = RunStore.open(args.run).verify()
            print(f"Integrity checks passed: {summary['run_id']} ({summary['provenance']}).")
            print(f"Records: {summary['prompts']} prompts, {summary['samples']} samples, {summary['artifacts']} artifacts.")
        else:
            config = load_config(args.config, live=args.command == "validate" and args.live)
            if args.command == "score":
                result = score_results(config, load_results(args.results))
                print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, allow_nan=False))
                return 0
            elif args.command == "report":
                summary = export_report(args.output, config, [load_results(path) for path in args.results],
                                        baseline_id=args.baseline, selected_id=args.selected)
                print(f"Exported report: {summary['path']} ({summary['provenance']}; {summary['status']} declared evidence).")
            elif args.command == "init":
                store = RunStore.create(args.runs_dir, config, provenance=args.provenance,
                                        description=args.description)
                print(f"Created local run: {store.path}")
            else:
                check = "live-readiness fields" if args.live else "offline configuration"
                print(f"Valid {check}: {config.run_id} (schema {config.schema_version}).")
    except ConfigError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    except IncompleteEvidence as error:
        print(f"Scoring blocked: {error}", file=sys.stderr)
        return 5
    except ScoringError as error:
        print(f"Scoring error: {error}", file=sys.stderr)
        return 2
    except StorageError as error:
        print(f"Storage error: {error}", file=sys.stderr)
        return 4
    except ReportError as error:
        print(f"Report error: {error}", file=sys.stderr)
        return 4
    print("No requests made, credentials read, or bot code executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
