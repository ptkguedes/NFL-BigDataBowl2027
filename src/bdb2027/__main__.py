"""Run the pre-registered analysis against a local or Kaggle data directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bdb2027.external_benchmark import SKIPPED_REASON
from bdb2027.io import DataLayoutError, SchemaError, default_data_dir
from bdb2027.pipeline import effects_summary, run_analysis
from bdb2027.schema import OFFICIAL_FILENAMES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Link Combine tracking to NFL tight-end and defensive-back outcomes. "
            "Writes an effect-size table, not a prediction submission."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory with the nine competition CSVs. Default: Kaggle input, else data/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/effects.csv"),
        help="Where to write the effect-size table. The parent directory is created.",
    )
    parser.add_argument(
        "--external-benchmark",
        type=Path,
        default=None,
        help="Optional local rating CSV. Not read unless --enable-external-benchmark is set.",
    )
    parser.add_argument(
        "--enable-external-benchmark",
        action="store_true",
        help=(
            "Compare Combine metrics with a local rating file. Leave this off unless "
            "the source meets Rules section 2.6. Ratings are not written back out."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = args.data_dir if args.data_dir is not None else default_data_dir()
    try:
        result = run_analysis(
            data_dir,
            external_benchmark_path=args.external_benchmark,
            external_benchmark_enabled=args.enable_external_benchmark,
        )
    except (DataLayoutError, SchemaError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("Expected competition files:", file=sys.stderr)
        for name in OFFICIAL_FILENAMES:
            print(f"  {name}", file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    effects = result["effects"]
    effects.to_csv(output, index=False)
    print(effects_summary(effects))
    print(f"Wrote {output}")
    sensitivity = result["sensitivity"]
    sensitivity_path = output.with_name(output.stem + "_sensitivity.csv")
    sensitivity.to_csv(sensitivity_path, index=False)
    print("Sensitivity check, DB tests without the 2024 class:")
    print(effects_summary(sensitivity))
    print(f"Wrote {sensitivity_path}")
    external = result["external"]
    if external["status"] == "computed":
        external_path = output.with_name(output.stem + "_external.csv")
        external["comparisons"].to_csv(external_path, index=False)
        print(f"Wrote {external_path}")
    else:
        print(external["reason"] or SKIPPED_REASON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
