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
    parser.add_argument(
        "--robustness",
        action="store_true",
        help=(
            "Also write <output>_robustness.csv: aggregate robustness checks for the "
            "DB speed-retention -> EPA-allowed row. Not pre-registered."
        ),
    )
    parser.add_argument(
        "--scenarios",
        action="store_true",
        help=(
            "Also write <output>_scenarios.csv (bootstrap-posterior probabilities and "
            "high-vs-low retention scenarios) and <output>_cushion.csv (alignment check). "
            "Aggregates only. Not pre-registered."
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
    if args.robustness:
        from bdb2027.io import load_players
        from bdb2027.robustness import retention_robustness

        players = load_players(data_dir).drop_duplicates("nfl_id", keep="first")
        robustness = retention_robustness(result, players)
        robustness_path = output.with_name(output.stem + "_robustness.csv")
        robustness.to_csv(robustness_path, index=False)
        print("Robustness checks, DB speed retention -> EPA allowed (not pre-registered):")
        print(robustness.to_string(index=False))
        print(f"Wrote {robustness_path}")
    if args.scenarios:
        from bdb2027.alignment import cushion_check, load_db_cushion
        from bdb2027.io import load_games, load_players
        from bdb2027.scenarios import scenario_report

        players = load_players(data_dir).drop_duplicates("nfl_id", keep="first")
        games = load_games(data_dir)
        scenario_table = scenario_report(result, players, games)
        scenario_path = output.with_name(output.stem + "_scenarios.csv")
        scenario_table.to_csv(scenario_path, index=False)
        print("Scenarios, DB speed retention -> EPA allowed (not pre-registered):")
        print(scenario_table.to_string(index=False))
        print(f"Wrote {scenario_path}")
        db_players = result["db_players"]
        db_ids = set(db_players.loc[db_players["db_break_time_s"].notna(), "nfl_id"])
        cushion_rows = load_db_cushion(data_dir, db_ids, games)
        cushion_table = cushion_check(cushion_rows, db_players, players, result["assignments"])
        cushion_path = output.with_name(output.stem + "_cushion.csv")
        cushion_table.to_csv(cushion_path, index=False)
        print("Alignment check, censored vs detected breakers (not pre-registered):")
        print(cushion_table.to_string(index=False))
        print(f"Wrote {cushion_path}")
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
