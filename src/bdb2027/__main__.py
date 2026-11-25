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
    parser.add_argument(
        "--cb-exploratory",
        action="store_true",
        help=(
            "Also write CB-only man/zone tables and the exploratory threat model. "
            "Not pre-registered. The six-test family is unchanged. "
            "The player-level coverage table is not for redistribution."
        ),
    )
    parser.add_argument(
        "--cb-bootstrap-draws",
        type=int,
        default=200,
        help="Cluster-bootstrap draws for the threat-model intervals. Default: 200.",
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
    if args.cb_exploratory:
        if args.cb_bootstrap_draws < 0:
            print("error: --cb-bootstrap-draws must be zero or positive", file=sys.stderr)
            return 1
        from bdb2027.pipeline import run_cb_exploratory

        try:
            cb = run_cb_exploratory(
                data_dir,
                assignments=result["assignments"],
                n_bootstrap=args.cb_bootstrap_draws,
            )
        except (DataLayoutError, SchemaError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        _write_cb_exploratory(output, cb)
    return 0


def _write_cb_exploratory(output: Path, cb: dict) -> None:
    """Write the exploratory CB tables. Play-level matchups are not written."""
    coverage_path = output.with_name(output.stem + "_cb_coverage.csv")
    audit_path = output.with_name(output.stem + "_cb_coverage_audit.csv")
    summary_path = output.with_name(output.stem + "_cb_coverage_summary.csv")
    effects_path = output.with_name(output.stem + "_cb_threat_effects.csv")
    calibration_path = output.with_name(output.stem + "_cb_threat_calibration.csv")
    metrics_path = output.with_name(output.stem + "_cb_threat_metrics.csv")
    cb["coverage"].to_csv(coverage_path, index=False)
    cb["coverage_audit"].to_csv(audit_path, index=False)
    cb["coverage_summary"].to_csv(summary_path, index=False)
    cb["threat_effects"].to_csv(effects_path, index=False)
    cb["threat_calibration"].to_csv(calibration_path, index=False)
    cb["threat_metrics"].to_csv(metrics_path, index=False)
    summary = cb["coverage_summary"].iloc[0]
    print("Exploratory CB coverage (not pre-registered):")
    print(
        "  label source: "
        f"{summary['label_source']}; floor {int(summary['min_targets_floor'])} targets; "
        f"{int(summary['n_cbs_in_table'])} CBs in the table; "
        f"shell agreement {summary['agreement_rate']}"
    )
    print(f"Wrote {coverage_path}")
    print(f"Wrote {audit_path}")
    print(f"Wrote {summary_path}")
    metrics = cb["threat_metrics"].iloc[0]
    print("Exploratory CB threat model (completion, not pre-registered):")
    print(
        "  "
        f"matchups {int(metrics['n_matchups'])}, CBs {int(metrics['n_cbs'])}, "
        f"threat rate {metrics['threat_rate']}, "
        f"grouped-CV Brier {metrics['brier_grouped_cv']} "
        f"vs intercept-only {metrics['brier_baseline_grouped_cv']}"
    )
    effects = cb["threat_effects"]
    if not effects.empty:
        show = effects.loc[:, ["term", "coef", "ci_low", "ci_high", "mean_risk_difference"]]
        print(show.to_string(index=False))
    print(f"Wrote {effects_path}")
    print(f"Wrote {calibration_path}")
    print(f"Wrote {metrics_path}")


if __name__ == "__main__":
    raise SystemExit(main())
