"""Command-line interface for AviaHCI modelling analyses."""

import argparse
import json
from pathlib import Path

import pandas as pd

from aviahci.provenance import build_provenance, write_provenance

from aviahci.scenarios import (
    background_sampling_sensitivity,
    repeated_spatial_validation,
)


def _read_csv(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {path}")
    return pd.read_csv(path)


def _write_results(results, output, input_paths, parameters):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)

    record = build_provenance(
        input_paths=input_paths,
        parameters=parameters,
        output_path=output,
    )
    provenance_path = write_provenance(record, output)

    print(json.dumps({
        "status": "success",
        "output_csv": str(output.resolve()),
        "provenance_json": str(provenance_path.resolve()),
        "rows_written": int(len(results)),
        "columns": list(results.columns),
    }, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="aviahci-analysis",
        description="Run reproducible AviaHCI modelling and robustness analyses.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    spatial = commands.add_parser(
        "spatial-validation",
        help="Repeat spatially separated train/test evaluation.",
    )
    spatial.add_argument("input_csv", help="CSV containing predictors, labels, longitude and latitude.")
    spatial.add_argument("--predictors", nargs="+", required=True)
    spatial.add_argument("--target", default="label")
    spatial.add_argument("--model", choices=["logistic_regression", "random_forest"],
                         default="logistic_regression")
    spatial.add_argument("--repeats", type=int, default=10)
    spatial.add_argument("--test-size", type=float, default=0.2)
    spatial.add_argument("--block-degrees", type=float, default=0.2)
    spatial.add_argument("--seed", type=int, default=42)
    spatial.add_argument("--n-estimators", type=int, default=500)
    spatial.add_argument("--output", required=True)

    background = commands.add_parser(
        "background-sensitivity",
        help="Compare results across background sample sizes and draws.",
    )
    background.add_argument("presence_csv")
    background.add_argument("background_csv")
    background.add_argument("--predictors", nargs="+", required=True)
    background.add_argument("--background-sizes", nargs="+", type=int, required=True)
    background.add_argument("--repeats", type=int, default=5)
    background.add_argument("--model", choices=["logistic_regression", "random_forest"],
                            default="logistic_regression")
    background.add_argument("--test-size", type=float, default=0.2)
    background.add_argument("--block-degrees", type=float, default=0.2)
    background.add_argument("--seed", type=int, default=42)
    background.add_argument("--n-estimators", type=int, default=500)
    background.add_argument("--output", required=True)

    args = parser.parse_args(argv)

    try:
        if args.command == "spatial-validation":
            data = _read_csv(args.input_csv)
            results = repeated_spatial_validation(
                data=data,
                predictor_cols=args.predictors,
                target_col=args.target,
                model_name=args.model,
                repeats=args.repeats,
                test_size=args.test_size,
                block_degrees=args.block_degrees,
                random_state=args.seed,
                n_estimators=args.n_estimators,
            )
            _write_results(
                results,
                args.output,
                input_paths=[args.input_csv],
                parameters={
                    "command": args.command,
                    "predictors": args.predictors,
                    "target": args.target,
                    "model": args.model,
                    "repeats": args.repeats,
                    "test_size": args.test_size,
                    "block_degrees": args.block_degrees,
                    "seed": args.seed,
                    "n_estimators": args.n_estimators,
                },
            )

        elif args.command == "background-sensitivity":
            presence = _read_csv(args.presence_csv)
            background_data = _read_csv(args.background_csv)
            results = background_sampling_sensitivity(
                X_presence=presence,
                X_background=background_data,
                predictor_cols=args.predictors,
                n_background_values=args.background_sizes,
                repeats=args.repeats,
                model_name=args.model,
                test_size=args.test_size,
                block_degrees=args.block_degrees,
                random_state=args.seed,
                n_estimators=args.n_estimators,
            )
            _write_results(
                results,
                args.output,
                input_paths=[args.presence_csv, args.background_csv],
                parameters={
                    "command": args.command,
                    "predictors": args.predictors,
                    "background_sizes": args.background_sizes,
                    "repeats": args.repeats,
                    "model": args.model,
                    "test_size": args.test_size,
                    "block_degrees": args.block_degrees,
                    "seed": args.seed,
                    "n_estimators": args.n_estimators,
                },
            )

    except (FileNotFoundError, ValueError, ImportError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
