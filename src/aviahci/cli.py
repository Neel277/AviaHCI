"""Command-line interface for AviaHCI."""

import argparse
import json
import sys

from aviahci import (
    inspect_raster,
    validate_occurrence_csv,
    validate_raster_alignment,
)


def _print_json(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        prog="aviahci",
        description="Validate inputs for reproducible habitat analysis.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    occurrence_parser = commands.add_parser(
        "check-occurrences",
        help="Validate an occurrence CSV or tab-delimited file.",
    )
    occurrence_parser.add_argument("path")
    occurrence_parser.add_argument("--longitude-col", default="longitude")
    occurrence_parser.add_argument("--latitude-col", default="latitude")
    occurrence_parser.add_argument("--date-col", default=None)
    occurrence_parser.add_argument("--species-col", default=None)

    raster_parser = commands.add_parser(
        "check-rasters",
        help="Check metadata and grid alignment for raster files.",
    )
    raster_parser.add_argument("paths", nargs="+")

    inspect_parser = commands.add_parser(
        "inspect-raster",
        help="Print metadata for one raster.",
    )
    inspect_parser.add_argument("path")

    args = parser.parse_args()

    try:
        if args.command == "check-occurrences":
            report = validate_occurrence_csv(
                args.path,
                longitude_col=args.longitude_col,
                latitude_col=args.latitude_col,
                date_col=args.date_col,
                species_col=args.species_col,
            )
            _print_json(report.to_dict())
            return 0 if report.valid else 1

        if args.command == "check-rasters":
            report = validate_raster_alignment(args.paths)
            _print_json(report.to_dict())
            return 0 if report.valid else 1

        if args.command == "inspect-raster":
            _print_json(inspect_raster(args.path))
            return 0

    except (FileNotFoundError, ImportError, ValueError) as exc:
        print(f"AviaHCI error: {exc}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
