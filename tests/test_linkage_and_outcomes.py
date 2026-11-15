"""Within-class correlations, coverage assignment, and the external gate."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bdb2027.external_benchmark import external_benchmark_step
from bdb2027.linkage import within_class_pearson
from bdb2027.outcomes import defensive_back_outcomes, nearest_defender_on_targets


def test_within_class_correlation_ignores_year_means() -> None:
    frame = pd.DataFrame(
        {
            "draft_year": [2023, 2023, 2023, 2024, 2024, 2024],
            "ten_yd_split": [1, 2, 3, 10, 11, 12],
            "te_mean_separation": [2, 4, 6, 1, 2, 3],
        }
    )
    pooled = within_class_pearson(frame, "ten_yd_split", "te_mean_separation")
    raw = float(np.corrcoef(frame["ten_yd_split"], frame["te_mean_separation"])[0, 1])
    assert raw < 0
    assert pooled["pearson_r"] > 0.8
    assert pooled["ci_low"] < pooled["pearson_r"] < pooled["ci_high"]
    assert pooled["n_players"] == 6
    assert pooled["n_classes"] == 2
    assert pooled["small_n"] is True


def test_nearest_defender_is_the_closer_back() -> None:
    players = pd.DataFrame(
        {"nfl_id": [1, 7, 8], "draft_year": [2023, 2023, 2023], "nfl_position": ["WR", "CB", "CB"]}
    )
    plays = pd.DataFrame(
        {
            "game_id": [1],
            "play_id": [10],
            "nfl_id": [1],
            "lined_up_position": ["WR"],
            "pass_result": ["C"],
            "play_nullified_by_penalty": ["N"],
            "target": [True],
            "expected_points_added": [1.5],
            "separation_at_pass_forward": [9.0],
        }
    )
    tracking = pd.DataFrame(
        {
            "game_id": [1, 1, 1],
            "play_id": [10, 10, 10],
            "nfl_id": [1, 7, 8],
            "x": [50.0, 50.0, 50.0],
            "y": [20.0, 22.0, 30.0],
            "event": ["pass_forward", "pass_forward", "pass_forward"],
        }
    )
    assigned = nearest_defender_on_targets(tracking, plays, players)
    assert assigned.loc[0, "defender_nfl_id"] == 7
    assert assigned.loc[0, "separation_allowed"] == pytest.approx(2.0)
    outcomes = defensive_back_outcomes(assigned, players, min_targets_covered=1)
    assert outcomes.loc[0, "nfl_id"] == 7
    assert outcomes.loc[0, "db_completion_rate_allowed"] == 1
    assert outcomes.loc[0, "db_mean_epa_allowed"] == 1.5


def test_external_benchmark_stays_off_and_does_not_write(tmp_path: Path) -> None:
    predictors = pd.DataFrame(
        {
            "nfl_id": [1, 2, 3, 4, 5, 6],
            "draft_year": [2023, 2023, 2023, 2024, 2024, 2024],
            "te_skill_decel_magnitude": [1, 2, 3, 1, 2, 3],
        }
    )
    players = predictors.loc[:, ["nfl_id", "draft_year"]].copy()
    before = set(tmp_path.iterdir())
    skipped = external_benchmark_step(predictors, players, tmp_path / "ratings.csv", enabled=False)
    assert skipped["status"] == "skipped"
    assert set(tmp_path.iterdir()) == before

    ratings = tmp_path / "ratings.csv"
    pd.DataFrame(
        {"nfl_id": [1, 2, 3, 4, 5, 6], "route_running": [10, 20, 30, 12, 22, 32]}
    ).to_csv(ratings, index=False)
    computed = external_benchmark_step(predictors, players, ratings, enabled=True)
    assert computed["status"] == "computed"
    comparisons = computed["comparisons"]
    route = comparisons.loc[comparisons["rating"].eq("route_running")].iloc[0]
    assert route["role"] == "external_secondary"
    assert bool(route["in_preregistered_family"]) is False
    assert route["pearson_r"] > 0.8
    assert list(tmp_path.iterdir()) == [ratings]
