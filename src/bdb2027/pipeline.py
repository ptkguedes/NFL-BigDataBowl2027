"""Link Combine movement to NFL tight-end and defensive-back outcomes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bdb2027.combine_features import movement_features, predictor_table
from bdb2027.external_benchmark import external_benchmark_step
from bdb2027.io import (
    load_career,
    load_combine_results,
    load_combine_tracking,
    load_games,
    load_pass_forward_tracking,
    load_player_play,
    load_players,
    require_official_files,
)
from bdb2027.linkage import evaluate_tests
from bdb2027.outcomes import (
    defensive_back_outcomes,
    nearest_defender_on_targets,
    tight_end_outcomes,
)
from bdb2027.preregistration import MIN_DB_TARGETS_COVERED, MIN_TE_TARGETS


def _without_year(frame: pd.DataFrame) -> pd.DataFrame:
    if "draft_year" not in frame.columns:
        return frame
    return frame.drop(columns=["draft_year"])


def run_analysis(
    data_dir: Path,
    *,
    external_benchmark_path: Path | None = None,
    external_benchmark_enabled: bool = False,
    min_te_targets: int = MIN_TE_TARGETS,
    min_db_targets_covered: int = MIN_DB_TARGETS_COVERED,
    chunksize: int = 250_000,
) -> dict[str, object]:
    """Run the pre-registered TE and DB analyses.

    `external_benchmark_enabled` defaults to false. The core tests never read
    an external rating file.
    """
    data_dir = require_official_files(data_dir)
    players = load_players(data_dir).drop_duplicates("nfl_id", keep="first")
    combine_results = load_combine_results(data_dir)
    games = load_games(data_dir)
    career = load_career(data_dir)
    tracking = load_combine_tracking(data_dir, chunksize=chunksize)
    attempts = movement_features(tracking)
    predictors = predictor_table(attempts, combine_results)
    player_play = load_player_play(data_dir, chunksize=chunksize)
    te_outcomes = tight_end_outcomes(player_play, players, min_targets=min_te_targets)
    assignments = nearest_defender_on_targets(
        load_pass_forward_tracking(data_dir, chunksize=chunksize),
        player_play,
        players,
    )
    db_outcomes = defensive_back_outcomes(
        assignments,
        players,
        min_targets_covered=min_db_targets_covered,
    )
    te_frame = predictors.merge(_without_year(te_outcomes), on="nfl_id", how="inner")
    db_frame = predictors.merge(_without_year(db_outcomes), on="nfl_id", how="inner")
    effects = evaluate_tests({"TE": te_frame, "DB": db_frame})
    external = external_benchmark_step(
        predictors,
        players,
        external_benchmark_path,
        enabled=external_benchmark_enabled,
    )
    return {
        "effects": effects,
        "te_players": te_frame,
        "db_players": db_frame,
        "attempts": attempts,
        "assignments": assignments,
        "career": career,
        "n_games": int(len(games)),
        "external": external,
    }


def effects_summary(effects: pd.DataFrame) -> str:
    """Plain-text table of the pre-registered effect sizes."""
    if effects.empty:
        return "No pre-registered tests were evaluated."
    show = effects.loc[
        :,
        [
            "test_id",
            "role",
            "n_players",
            "n_classes",
            "pearson_r",
            "ci_low",
            "ci_high",
            "small_n",
            "class_counts",
        ],
    ]
    return show.to_string(index=False)
