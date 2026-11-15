"""Robustness checks for retention -> EPA allowed, on synthetic tables."""

import numpy as np
import pandas as pd

from bdb2027.robustness import (
    bootstrap_interval,
    coverage_split,
    leave_one_class_out,
    leave_one_player_out_range,
    retention_robustness,
)


def _db_players() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    nfl_id = 1
    for year in (2023, 2024, 2025):
        for index in range(6):
            retention = 0.8 + 0.05 * index
            rows.append(
                {
                    "nfl_id": nfl_id,
                    "draft_year": year,
                    "db_speed_retention": retention,
                    "db_mean_epa_allowed": 1.0 - retention + rng.normal(0, 0.01),
                    "n_targets_covered": 5 + 2 * index,
                }
            )
            nfl_id += 1
    return pd.DataFrame(rows)


def test_leave_one_class_out_drops_each_class() -> None:
    rows = leave_one_class_out(_db_players())
    assert [row["detail"] for row in rows] == ["without 2023", "without 2024", "without 2025"]
    assert all(row["n_players"] == 12 for row in rows)
    assert all(row["r"] < -0.9 for row in rows)


def test_bootstrap_is_seeded_and_brackets_the_estimate() -> None:
    frame = _db_players()
    first = bootstrap_interval(frame, draws=200, seed=1)
    second = bootstrap_interval(frame, draws=200, seed=1)
    assert first["ci_low"] == second["ci_low"]
    assert first["ci_low"] <= first["r"] <= first["ci_high"]
    assert first["p_value"] == 0.0


def test_leave_one_player_out_range_contains_the_estimate() -> None:
    row = leave_one_player_out_range(_db_players())
    assert row["ci_low"] <= row["r"] <= row["ci_high"]
    assert row["n_players"] == 18


def test_coverage_split_rebuilds_outcomes_per_coverage_type() -> None:
    db_players = _db_players()
    players = db_players.loc[:, ["nfl_id", "draft_year"]].assign(nfl_position="CB")
    rows = []
    play = 1
    for _, player in db_players.iterrows():
        for assignment in ("MAN", "MAN", "MAN", "CURL_FLAT_LEFT", "CURL_FLAT_LEFT", "HOLE"):
            rows.append(
                {
                    "game_id": 1,
                    "play_id": play,
                    "receiver_nfl_id": 999,
                    "defender_nfl_id": player["nfl_id"],
                    "coverage_assignment": assignment,
                    "separation_allowed": 2.0,
                    "is_completion": True,
                    "expected_points_added": player["db_mean_epa_allowed"],
                }
            )
            play += 1
    split = coverage_split(pd.DataFrame(rows), db_players, players)
    assert [row["detail"].split()[0] for row in split] == ["man", "zone"]
    assert all(row["n_players"] == 18 for row in split)
    assert all(row["r"] < -0.9 for row in split)


def test_retention_robustness_returns_aggregates_only() -> None:
    db_players = _db_players()
    players = db_players.loc[:, ["nfl_id", "draft_year"]].assign(nfl_position="CB")
    table = retention_robustness({"db_players": db_players, "assignments": pd.DataFrame()}, players)
    assert "nfl_id" not in table.columns
    assert set(table["check"]) >= {"main", "spearman", "leave_one_class_out", "bootstrap"}
