"""Within-class correlations, coverage assignment, and the external gate."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bdb2027.external_benchmark import external_benchmark_step
from bdb2027.linkage import within_class_pearson
from bdb2027.outcomes import (
    coverage_defender_on_targets,
    defensive_back_outcomes,
    nearest_defender_on_targets,
)


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
            "team_abbr": ["OFF"],
            "coverage_assignment": [None],
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


def test_fisher_interval_spends_class_means() -> None:
    frame = pd.DataFrame(
        {
            "draft_year": [2023] * 4 + [2024] * 4 + [2025] * 4,
            "x": [1, 2, 3, 4, 2, 1, 4, 3, 1, 3, 2, 4],
            "y": [1, 3, 2, 4, 1, 2, 4, 3, 2, 3, 1, 4],
        }
    )
    stats = within_class_pearson(frame, "x", "y")
    r = stats["pearson_r"]
    se = 1.0 / math.sqrt(12 - 3 - 2)
    assert stats["n_classes"] == 3
    assert stats["ci_low"] == pytest.approx(math.tanh(math.atanh(r) - 1.96 * se))
    assert stats["ci_high"] == pytest.approx(math.tanh(math.atanh(r) + 1.96 * se))


def test_spearman_ties_censored_players_at_the_slowest_rank() -> None:
    # Within each class, censored players (time 5.5) tie at the slowest rank.
    frame = pd.DataFrame(
        {
            "draft_year": [2023] * 5 + [2024] * 5,
            "db_break_time_s": [3.0, 4.0, 4.5, 5.5, 5.5, 3.5, 4.0, 5.0, 5.5, 5.5],
            "sep": [1.0, 1.5, 2.0, 9.0, 3.0, 2.0, 2.5, 2.6, 30.0, 4.0],
            "db_break_censored": [False, False, False, True, True] * 2,
        }
    )
    rank = within_class_pearson(
        frame,
        "db_break_time_s",
        "sep",
        method="spearman",
        censored_col="db_break_censored",
    )
    linear = within_class_pearson(frame, "db_break_time_s", "sep")
    assert rank["method"] == "spearman"
    assert rank["n_censored"] == 4
    assert rank["n_players"] == 10
    # The rank method is not driven by the 30-yard outlier.
    x = np.array([1, 2, 3, 4.5, 4.5] * 2) - 3.0
    y = np.array([1, 2, 3, 5, 4] * 2) - 3.0
    assert rank["pearson_r"] == pytest.approx(float(np.corrcoef(x, y)[0, 1]))
    assert rank["pearson_r"] > linear["pearson_r"]
    se = math.sqrt(1.06 / (10 - 3 - 1))
    r = rank["pearson_r"]
    assert rank["ci_high"] == pytest.approx(math.tanh(math.atanh(r) + 1.96 * se))
    assert 0 < rank["p_value"] < 0.05
    with pytest.raises(ValueError):
        within_class_pearson(frame, "db_break_time_s", "sep", method="kendall")


def _coverage_case() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    players = pd.DataFrame(
        {
            "nfl_id": [1, 7, 8, 9, 10],
            "draft_year": [2023] * 5,
            "nfl_position": ["WR", "CB", "CB", "FS", "CB"],
        }
    )
    rows = [
        # play 10: receiver 1 targeted; 8 is closest but has NO_ASSIGNMENT,
        # 10 is close but on the offense, 7 is assigned and 2 yd away,
        # 9 is assigned but 12 yd away.
        (10, 1, "OFF", True, None, "C", 1.5, 3.0),
        (10, 7, "DEF", False, "MAN", "C", 1.5, None),
        (10, 8, "DEF", False, "NO_ASSIGNMENT", "C", 1.5, None),
        (10, 9, "DEF", False, "DEEP_FREE", "C", 1.5, None),
        (10, 10, "OFF", False, "MAN", "C", 1.5, None),
        # play 11: only assigned DB is 9, 8 yd away, outside the radius.
        (11, 1, "OFF", True, None, "I", -0.5, 6.0),
        (11, 9, "DEF", False, "CURL_FLAT_LEFT", "I", -0.5, None),
    ]
    plays = pd.DataFrame(
        [
            {
                "game_id": 1,
                "play_id": play,
                "nfl_id": nfl_id,
                "team_abbr": team,
                "lined_up_position": "WR",
                "target": target,
                "coverage_assignment": assignment,
                "pass_result": result,
                "play_nullified_by_penalty": "N",
                "expected_points_added": epa,
                "separation_at_pass_forward": separation,
            }
            for play, nfl_id, team, target, assignment, result, epa, separation in rows
        ]
    )
    locations = [
        (10, 1, 20.0),
        (10, 7, 22.0),
        (10, 8, 21.0),
        (10, 9, 32.0),
        (10, 10, 20.5),
        (11, 1, 20.0),
        (11, 9, 28.0),
    ]
    tracking = pd.DataFrame(
        {
            "game_id": [1] * len(locations),
            "play_id": [play for play, _, _ in locations],
            "nfl_id": [nfl_id for _, nfl_id, _ in locations],
            "x": [50.0] * len(locations),
            "y": [y for _, _, y in locations],
            "event": ["pass_forward"] * len(locations),
        }
    )
    return players, plays, tracking


def test_coverage_credit_needs_an_active_assignment_and_the_radius() -> None:
    players, plays, tracking = _coverage_case()
    credited = coverage_defender_on_targets(tracking, plays, players, radius_yds=5.0)
    assert len(credited) == 1
    row = credited.iloc[0]
    assert row["play_id"] == 10
    assert row["defender_nfl_id"] == 7
    assert row["coverage_assignment"] == "MAN"
    assert row["coverage_distance"] == pytest.approx(2.0)
    # Separation allowed is the receiver's published separation, not the distance.
    assert row["separation_allowed"] == pytest.approx(3.0)
    assert bool(row["is_completion"]) is True

    wider = coverage_defender_on_targets(tracking, plays, players, radius_yds=10.0)
    assert set(zip(wider["play_id"], wider["defender_nfl_id"], strict=True)) == {(10, 7), (11, 9)}


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
