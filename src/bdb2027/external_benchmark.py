"""Optional secondary benchmark against an external rating file.

Default is off. Madden player ratings were not verified to meet Competition
Rules section 2.6 (public, free to every participant, or the host's
Reasonableness Standard). This module never downloads, scrapes, or writes a
rating file. It only reads a local CSV the analyst has already stored outside
the repository.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bdb2027.linkage import within_class_pearson

RATING_COLUMNS: tuple[str, ...] = (
    "speed",
    "acceleration",
    "agility",
    "change_of_direction",
    "route_running",
    "release",
    "man_coverage",
    "zone_coverage",
)

# Sensor metric, rating column, angle. None of these enter the pre-registered family.
BENCHMARK_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("te_skill_decel_magnitude", "route_running", "TE"),
    ("te_skill_decel_magnitude", "release", "TE"),
    ("ten_yd_split", "acceleration", "TE"),
    ("db_break_time_s", "change_of_direction", "DB"),
    ("db_speed_retention", "man_coverage", "DB"),
    ("db_speed_retention", "zone_coverage", "DB"),
)

SKIPPED_REASON = (
    "External benchmark skipped. Enable it only when the rating source is "
    "publicly available to every participant at no cost, or meets the host "
    "Reasonableness Standard in Rules section 2.6. Do not commit or redistribute "
    "Madden ratings."
)


def load_rating_file(path: Path) -> pd.DataFrame:
    """Read a local rating CSV. `nfl_id` plus at least one rating column."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"rating file does not exist: {path}")
    header = pd.read_csv(path, nrows=0)
    if "nfl_id" not in header.columns:
        raise ValueError(f"{path} must include nfl_id")
    present = [column for column in RATING_COLUMNS if column in header.columns]
    if not present:
        raise ValueError(f"{path} has none of the expected rating columns")
    frame = pd.read_csv(path, usecols=["nfl_id", *present])
    frame["nfl_id"] = pd.to_numeric(frame["nfl_id"], errors="coerce")
    return frame.dropna(subset=["nfl_id"])


def compare_ratings(
    predictors: pd.DataFrame,
    ratings: pd.DataFrame,
    players: pd.DataFrame,
) -> pd.DataFrame:
    """Within-draft-class correlations between sensor metrics and ratings.

    Ten-yard split and break time are flipped so a higher value means faster
    or quicker, matching the pre-registered orientation. These rows are not
    part of the multiple-comparison family.
    """
    class_keys = players.loc[:, ["nfl_id", "draft_year"]].drop_duplicates()
    sensor_cols = ["nfl_id", "draft_year"]
    for column, _rating, _angle in BENCHMARK_PAIRS:
        if column in predictors.columns and column not in sensor_cols:
            sensor_cols.append(column)
    base = predictors.loc[:, [col for col in sensor_cols if col in predictors.columns]]
    base = base.merge(class_keys, on=["nfl_id", "draft_year"], how="left")
    joined = base.merge(ratings, on="nfl_id", how="inner")
    rows: list[dict[str, object]] = []
    for predictor, rating, angle in BENCHMARK_PAIRS:
        flipped = {"ten_yd_split", "db_break_time_s", "three_cone"}
        orient = "flip" if predictor in flipped else "as_is"
        stats = within_class_pearson(joined, predictor, rating, orient=orient)
        rows.append(
            {
                "comparison_id": f"{angle}_{predictor}_vs_{rating}",
                "angle": angle,
                "role": "external_secondary",
                "predictor": predictor,
                "rating": rating,
                "orient": orient,
                "in_preregistered_family": False,
                **stats,
            }
        )
    return pd.DataFrame(rows)


def external_benchmark_step(
    predictors: pd.DataFrame,
    players: pd.DataFrame,
    path: Path | None,
    *,
    enabled: bool,
) -> dict[str, object]:
    """Run the optional comparison, or return a skipped record."""
    if not enabled:
        return {"status": "skipped", "reason": SKIPPED_REASON, "comparisons": pd.DataFrame()}
    if path is None:
        return {
            "status": "skipped",
            "reason": SKIPPED_REASON + " No rating path was provided.",
            "comparisons": pd.DataFrame(),
        }
    ratings = load_rating_file(Path(path))
    comparisons = compare_ratings(predictors, ratings, players)
    return {"status": "computed", "reason": "", "comparisons": comparisons}
