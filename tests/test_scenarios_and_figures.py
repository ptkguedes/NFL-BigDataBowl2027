"""Scenario, alignment, and figure helpers on synthetic tables."""

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from bdb2027.alignment import cushion_check  # noqa: E402
from bdb2027.figures import figure_forest, figure_retention_scatter, forest_rows  # noqa: E402
from bdb2027.scenarios import (  # noqa: E402
    observed_targets_per_db_season,
    posterior_draws,
    scenario_summary,
)


def _db_players(noise: float = 0.05) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    nfl_id = 1
    for year in (2023, 2024, 2025):
        for index in range(8):
            retention = 0.9 + 0.03 * index
            rows.append(
                {
                    "nfl_id": nfl_id,
                    "draft_year": year,
                    "db_speed_retention": retention,
                    "db_mean_epa_allowed": 2.0 - 2.0 * retention + rng.normal(0, noise),
                    "db_break_time_s": 4.0 + 0.2 * index,
                    "db_break_censored": index >= 6,
                    "n_targets_covered": 10,
                }
            )
            nfl_id += 1
    return pd.DataFrame(rows)


def test_posterior_recovers_a_negative_slope() -> None:
    draws = posterior_draws(_db_players(), draws=300, seed=3)
    assert len(draws) == 300
    assert -2.3 < draws["slope"].median() < -1.7
    assert (draws["sigma"] > 0).all()


def test_scenario_summary_probabilities_and_signs() -> None:
    table = scenario_summary(
        _db_players(), draws=300, seed=3, observed_targets_per_season=5.0
    ).set_index("quantity")
    assert table.loc["P(slope < 0)", "estimate"] == 1.0
    top = table.loc["P(top-quartile DB allows less EPA/target than class median)", "estimate"]
    bottom = table.loc["P(bottom-quartile DB allows less EPA/target than class median)", "estimate"]
    assert top > 0.9 > 0.1 > bottom
    diff = table.loc["EPA/target difference, high minus low retention"]
    assert diff["low_90"] <= diff["estimate"] <= diff["high_90"] < 0
    season = table.loc["EPA per season difference at 60 targets (assumed)", "estimate"]
    assert abs(season - 60 * diff["estimate"]) < abs(0.2 * season)
    assert "nfl_id" not in table.columns


def test_observed_targets_per_db_season() -> None:
    assignments = pd.DataFrame(
        {"game_id": [1, 1, 2, 3], "play_id": [1, 2, 1, 1], "defender_nfl_id": [7, 7, 7, 8]}
    )
    games = pd.DataFrame({"game_id": [1, 2, 3], "season": [2023, 2024, 2024]})
    assert observed_targets_per_db_season(assignments, games) == 1.0


def test_cushion_check_compares_censored_and_detected() -> None:
    db_players = _db_players()
    players = db_players.loc[:, ["nfl_id", "draft_year"]].assign(nfl_position="CB")
    rows = []
    for _, player in db_players.iterrows():
        depth = 8.0 if player["db_break_censored"] else 5.0
        for play in range(4):
            rows.append(
                {"game_id": 1, "play_id": play, "nfl_id": player["nfl_id"], "cushion": depth}
            )
    table = cushion_check(pd.DataFrame(rows), db_players, players, draws=200, seed=1)
    first = table.iloc[0]
    assert first["n_censored"] == 6
    assert first["n_detected"] == 18
    assert first["within_class_gap"] == 3.0
    assert first["permutation_p"] < 0.05
    assert "nfl_id" not in table.columns


def test_figures_draw_without_writing_files(tmp_path) -> None:
    before = set(tmp_path.iterdir())
    fig1 = figure_retention_scatter(_db_players())
    assert "Figure 1" in fig1.axes[0].get_title()
    effects = pd.DataFrame(
        {
            "test_id": ["db_secondary_retention_epa"],
            "pearson_r": [-0.6],
            "ci_low": [-0.8],
            "ci_high": [-0.25],
        }
    )
    robustness = pd.DataFrame(
        {
            "check": ["main", "bootstrap"],
            "detail": ["", ""],
            "r": [-0.6, -0.6],
            "ci_low": [-0.8, -0.86],
            "ci_high": [-0.25, -0.29],
        }
    )
    assert len(forest_rows(effects, robustness)) == 2
    fig2 = figure_forest(effects, robustness)
    assert "Figure 2" in fig2.axes[0].get_title()
    assert set(tmp_path.iterdir()) == before
