"""Run the implemented offline validation command."""

import argparse
import sys

from slither_evolver.config import ConfigError, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m slither_evolver",
        description="Validate Slither Sam experiment configuration.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Check JSON without making requests or running bots.")
    validate.add_argument("--config", required=True, help="Path to schema-version-1 experiment JSON.")
    validate.add_argument("--live", action="store_true",
                          help="Require future live-request controls; does not start live work.")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config, live=args.live)
    except ConfigError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    check = "live-readiness fields" if args.live else "offline configuration"
    print(f"Valid {check}: {config.run_id} (schema {config.schema_version}).")
    print("No requests made, credentials read, or bot code executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
