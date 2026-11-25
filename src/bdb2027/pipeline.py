"""Link Combine movement to NFL tight-end and defensive-back outcomes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bdb2027.cb_coverage import (
    cb_coverage_audit,
    cb_coverage_summary,
    cb_coverage_table,
    filter_cornerback_assignments,
)
from bdb2027.combine_features import movement_features, predictor_table
from bdb2027.external_benchmark import external_benchmark_step
from bdb2027.io import (
    load_career,
    load_combine_results,
    load_combine_tracking,
    load_combine_traits,
    load_games,
    load_pass_forward_tracking,
    load_play_kinematics,
    load_play_shell,
    load_player_play,
    load_players,
    require_official_files,
)
from bdb2027.linkage import evaluate_tests
from bdb2027.outcomes import (
    coverage_defender_on_targets,
    defensive_back_outcomes,
    tight_end_outcomes,
)
from bdb2027.preregistration import (
    MIN_DB_TARGETS_COVERED,
    MIN_TE_TARGETS,
    PREREGISTERED_TESTS,
    REGULAR_SEASON_ONLY,
    REGULAR_SEASON_TYPE,
    SENSITIVITY_DROP_CLASS,
)
from bdb2027.threat import BOOTSTRAP_DRAWS, BOOTSTRAP_SEED, build_matchups, fit_threat_model


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
    regular_season_only: bool = REGULAR_SEASON_ONLY,
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
    pass_forward = load_pass_forward_tracking(data_dir, chunksize=chunksize)
    if regular_season_only:
        # Amendment A1: games.csv also has PRE and POST games.
        season_type = games["season_type"].astype("string").str.upper()
        reg_ids = set(games.loc[season_type.eq(REGULAR_SEASON_TYPE), "game_id"].tolist())
        player_play = player_play.loc[player_play["game_id"].isin(reg_ids)]
        pass_forward = pass_forward.loc[pass_forward["game_id"].isin(reg_ids)]
    te_outcomes = tight_end_outcomes(player_play, players, min_targets=min_te_targets)
    assignments = coverage_defender_on_targets(
        pass_forward,
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
    # Amendment A3 sensitivity check: DB tests without the truncated 2024 class.
    db_tests = tuple(test for test in PREREGISTERED_TESTS if test.angle == "DB")
    db_without_class = db_frame.loc[db_frame["draft_year"] != SENSITIVITY_DROP_CLASS]
    sensitivity = evaluate_tests({"DB": db_without_class}, tests=db_tests)
    sensitivity.insert(0, "sensitivity", f"drop_draft_year_{SENSITIVITY_DROP_CLASS}")
    external = external_benchmark_step(
        predictors,
        players,
        external_benchmark_path,
        enabled=external_benchmark_enabled,
    )
    return {
        "effects": effects,
        "sensitivity": sensitivity,
        "te_players": te_frame,
        "db_players": db_frame,
        "attempts": attempts,
        "assignments": assignments,
        "career": career,
        "n_games": int(len(games)),
        "external": external,
    }


def _regular_game_ids(games: pd.DataFrame) -> set[int]:
    season_type = games["season_type"].astype("string").str.upper()
    ids = pd.to_numeric(games.loc[season_type.eq(REGULAR_SEASON_TYPE), "game_id"], errors="coerce")
    return {int(value) for value in ids.dropna().tolist()}


def _play_keys(frame: pd.DataFrame) -> set[tuple[int, int]]:
    if frame.empty or "game_id" not in frame.columns or "play_id" not in frame.columns:
        return set()
    games = pd.to_numeric(frame["game_id"], errors="coerce")
    plays = pd.to_numeric(frame["play_id"], errors="coerce")
    keys: set[tuple[int, int]] = set()
    for game_id, play_id in zip(games.tolist(), plays.tolist(), strict=True):
        if pd.isna(game_id) or pd.isna(play_id):
            continue
        keys.add((int(game_id), int(play_id)))
    return keys


def _keep_regular_season(frame: pd.DataFrame, regular_ids: set[int]) -> pd.DataFrame:
    if frame.empty:
        return frame
    game_ids = pd.to_numeric(frame["game_id"], errors="coerce")
    return frame.loc[game_ids.isin(regular_ids)].copy()


def run_cb_exploratory(
    data_dir: Path,
    *,
    assignments: pd.DataFrame | None = None,
    players: pd.DataFrame | None = None,
    n_bootstrap: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
    chunksize: int = 250_000,
    regular_season_only: bool = REGULAR_SEASON_ONLY,
) -> dict[str, pd.DataFrame]:
    """CB man/zone table and the exploratory threat model.

    The pre-registered family is not changed. Pass ``assignments`` from
    ``run_analysis`` to reuse the credited targets. Otherwise this rebuilds
    them with the same regular-season filter and coverage-credit rule, then
    keeps ``nfl_position == CB``.

    ``matchups`` is play-level and is returned for figures and tests. Do not
    write it out or commit it.
    """
    data_dir = require_official_files(Path(data_dir))
    if players is None:
        players = load_players(data_dir).drop_duplicates("nfl_id", keep="first")
    games = load_games(data_dir)
    regular_ids = _regular_game_ids(games)
    if assignments is None:
        player_play = load_player_play(data_dir, chunksize=chunksize)
        pass_forward = load_pass_forward_tracking(data_dir, chunksize=chunksize)
        if regular_season_only:
            player_play = _keep_regular_season(player_play, regular_ids)
            pass_forward = _keep_regular_season(pass_forward, regular_ids)
        assignments = coverage_defender_on_targets(pass_forward, player_play, players)
    elif regular_season_only:
        assignments = _keep_regular_season(assignments, regular_ids)
    cb_assignments = filter_cornerback_assignments(assignments, players)
    shell = load_play_shell(data_dir, chunksize=chunksize)
    coverage = cb_coverage_table(cb_assignments, players, shell)
    audit = cb_coverage_audit(cb_assignments, shell)
    summary = cb_coverage_summary(cb_assignments, coverage, shell)
    traits = load_combine_traits(data_dir)
    tracking = load_play_kinematics(
        data_dir,
        _play_keys(cb_assignments),
        chunksize=chunksize,
    )
    matchups = build_matchups(tracking, cb_assignments, traits)
    model = fit_threat_model(
        matchups,
        n_assignments=int(len(cb_assignments)),
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    return {
        "coverage": coverage,
        "coverage_audit": audit,
        "coverage_summary": summary,
        "threat_effects": model["effects"],
        "threat_calibration": model["calibration"],
        "threat_metrics": model["metrics"],
        "matchups": matchups,
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
            "method",
            "pearson_r",
            "ci_low",
            "ci_high",
            "p_value",
            "n_censored",
            "small_n",
            "underpowered",
            "class_counts",
        ],
    ]
    return show.to_string(index=False)
