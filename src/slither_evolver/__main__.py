"""Validate configuration and initialize/inspect offline evidence stores."""

import argparse
import sys

from slither_evolver.config import ConfigError, load_config
from slither_evolver.storage import RunStore, StorageError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m slither_evolver",
        description="Validate settings and preserve local Slither Sam evidence.",
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
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            summary = RunStore.open(args.run).verify()
            print(f"Integrity checks passed: {summary['run_id']} ({summary['provenance']}).")
            print(f"Records: {summary['prompts']} prompts, {summary['samples']} samples, {summary['artifacts']} artifacts.")
        else:
            config = load_config(args.config, live=args.command == "validate" and args.live)
            if args.command == "init":
                store = RunStore.create(args.runs_dir, config, provenance=args.provenance,
                                        description=args.description)
                print(f"Created local run: {store.path}")
            else:
                check = "live-readiness fields" if args.live else "offline configuration"
                print(f"Valid {check}: {config.run_id} (schema {config.schema_version}).")
    except ConfigError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    except StorageError as error:
        print(f"Storage error: {error}", file=sys.stderr)
        return 4
    print("No requests made, credentials read, or bot code executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
