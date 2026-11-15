"""In-game outcomes for tight ends and defensive backs.

Tight-end separation and target results come from `player_play.csv`.
Separation allowed, completions allowed, and EPA allowed for defensive backs
are not published columns. Since amendment A2 (2026-11-15) a targeted draftee
receiver is credited to the closest opposing draftee DB with an active
`coverage_assignment` within the pre-registered radius at `pass_forward`.
Only the 510 draftees are tracked in games.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bdb2027.preregistration import (
    COVERAGE_RADIUS_YDS,
    DB_POSITIONS,
    INACTIVE_COVERAGE_ASSIGNMENTS,
    TE_POSITIONS,
)


def _as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    text = series.astype("string").str.strip().str.lower()
    return text.isin(["1", "true", "t", "yes"]).fillna(False)


def _active_plays(player_play: pd.DataFrame) -> pd.DataFrame:
    frame = player_play.copy()
    if "play_nullified_by_penalty" in frame.columns:
        flag = frame["play_nullified_by_penalty"].astype("string").str.upper()
        frame = frame.loc[~flag.eq("Y")]
    return frame


def tight_end_outcomes(
    player_play: pd.DataFrame,
    players: pd.DataFrame,
    *,
    min_targets: int,
) -> pd.DataFrame:
    """One row per tight end with enough targeted, non-nullified plays."""
    columns = [
        "nfl_id",
        "draft_year",
        "n_te_plays",
        "n_targets",
        "te_mean_separation",
        "te_completion_rate",
        "te_mean_epa",
    ]
    te_ids = set(
        players.loc[players["nfl_position"].isin(TE_POSITIONS), "nfl_id"].tolist()
    )
    plays = _active_plays(player_play)
    plays = plays.loc[
        plays["nfl_id"].isin(te_ids) & plays["lined_up_position"].astype("string").eq("TE")
    ]
    if plays.empty:
        return pd.DataFrame(columns=columns)

    plays = plays.copy()
    plays["is_target"] = _as_bool(plays["target"])
    plays["is_completion"] = plays["pass_result"].astype("string").eq("C") & plays["is_target"]
    targets = plays.loc[plays["is_target"]]
    grouped = targets.groupby("nfl_id", as_index=False).agg(
        n_targets=("play_id", "size"),
        te_mean_separation=("separation_at_pass_forward", "mean"),
        n_completions=("is_completion", "sum"),
        te_mean_epa=("expected_points_added", "mean"),
    )
    snap_counts = plays.groupby("nfl_id", as_index=False).agg(n_te_plays=("play_id", "size"))
    grouped = snap_counts.merge(grouped, on="nfl_id", how="left")
    grouped["n_targets"] = grouped["n_targets"].fillna(0).astype(int)
    grouped["te_completion_rate"] = np.where(
        grouped["n_targets"] > 0,
        grouped["n_completions"] / grouped["n_targets"],
        np.nan,
    )
    grouped = grouped.loc[grouped["n_targets"] >= min_targets]
    years = players.loc[:, ["nfl_id", "draft_year"]]
    grouped = grouped.merge(years, on="nfl_id", how="left")
    return grouped.loc[:, columns]


def nearest_defender_on_targets(
    pass_forward: pd.DataFrame,
    player_play: pd.DataFrame,
    players: pd.DataFrame,
) -> pd.DataFrame:
    """Assign each targeted receiver to the closest DB at `pass_forward`.

    Superseded by `coverage_defender_on_targets` (amendment A2) and kept for
    the original-definition comparison. Distance is Euclidean yards in the
    tracking coordinate system. Plays with no receiver coordinate, or no DB
    coordinate, are dropped.
    """
    columns = [
        "game_id",
        "play_id",
        "receiver_nfl_id",
        "defender_nfl_id",
        "separation_allowed",
        "is_completion",
        "expected_points_added",
    ]
    if pass_forward.empty or player_play.empty:
        return pd.DataFrame(columns=columns)

    db_ids = set(players.loc[players["nfl_position"].isin(DB_POSITIONS), "nfl_id"].tolist())
    plays = _active_plays(player_play)
    plays = plays.loc[_as_bool(plays["target"])].copy()
    if plays.empty or not db_ids:
        return pd.DataFrame(columns=columns)
    plays["is_completion"] = plays["pass_result"].astype("string").eq("C")

    locations = pass_forward.loc[:, ["game_id", "play_id", "nfl_id", "x", "y"]].dropna(
        subset=["nfl_id", "x", "y"]
    )
    locations = locations.drop_duplicates(["game_id", "play_id", "nfl_id"], keep="first")
    receiver_xy = locations.rename(
        columns={"nfl_id": "receiver_nfl_id", "x": "rx", "y": "ry"}
    )
    targets = plays.merge(
        receiver_xy,
        left_on=["game_id", "play_id", "nfl_id"],
        right_on=["game_id", "play_id", "receiver_nfl_id"],
        how="inner",
    )
    defenders = locations.loc[locations["nfl_id"].isin(db_ids)].rename(
        columns={"nfl_id": "defender_nfl_id", "x": "dx", "y": "dy"}
    )
    if targets.empty or defenders.empty:
        return pd.DataFrame(columns=columns)

    paired = targets.merge(defenders, on=["game_id", "play_id"], how="inner")
    paired = paired.loc[paired["receiver_nfl_id"] != paired["defender_nfl_id"]]
    if paired.empty:
        return pd.DataFrame(columns=columns)
    paired["separation_allowed"] = np.hypot(
        paired["rx"].to_numpy(dtype=float) - paired["dx"].to_numpy(dtype=float),
        paired["ry"].to_numpy(dtype=float) - paired["dy"].to_numpy(dtype=float),
    )
    paired = paired.sort_values("separation_allowed", kind="mergesort")
    nearest = paired.drop_duplicates(["game_id", "play_id", "receiver_nfl_id"], keep="first")
    return nearest.loc[:, columns]


def _pass_forward_locations(pass_forward: pd.DataFrame) -> pd.DataFrame:
    locations = pass_forward.loc[:, ["game_id", "play_id", "nfl_id", "x", "y"]].dropna(
        subset=["nfl_id", "x", "y"]
    )
    return locations.drop_duplicates(["game_id", "play_id", "nfl_id"], keep="first")


def coverage_defender_on_targets(
    pass_forward: pd.DataFrame,
    player_play: pd.DataFrame,
    players: pd.DataFrame,
    *,
    radius_yds: float = COVERAGE_RADIUS_YDS,
) -> pd.DataFrame:
    """Credit each targeted draftee receiver to an assigned draftee DB.

    Amendment A2. A DB is a candidate on a play when he is in the DB position
    set, plays for the other team, and has an active `coverage_assignment`.
    The credited DB is the candidate closest to the targeted receiver at
    `pass_forward`, if that distance is at most `radius_yds`. Separation
    allowed is the receiver's `separation_at_pass_forward`.

    Only draftees are tracked, so targets of other receivers and coverage by
    other defenders cannot be seen.
    """
    columns = [
        "game_id",
        "play_id",
        "receiver_nfl_id",
        "defender_nfl_id",
        "coverage_assignment",
        "coverage_distance",
        "separation_allowed",
        "is_completion",
        "expected_points_added",
    ]
    if pass_forward.empty or player_play.empty:
        return pd.DataFrame(columns=columns)

    db_ids = set(players.loc[players["nfl_position"].isin(DB_POSITIONS), "nfl_id"].tolist())
    plays = _active_plays(player_play)
    if plays.empty or not db_ids:
        return pd.DataFrame(columns=columns)

    targets = plays.loc[
        _as_bool(plays["target"]),
        [
            "game_id",
            "play_id",
            "nfl_id",
            "team_abbr",
            "pass_result",
            "expected_points_added",
            "separation_at_pass_forward",
        ],
    ].rename(columns={"nfl_id": "receiver_nfl_id", "team_abbr": "receiver_team"})
    targets["is_completion"] = targets["pass_result"].astype("string").eq("C").fillna(False)

    assignment = plays["coverage_assignment"].astype("string").str.strip().str.upper()
    active = (
        plays["nfl_id"].isin(db_ids)
        & assignment.notna()
        & ~assignment.isin(sorted(INACTIVE_COVERAGE_ASSIGNMENTS)).fillna(False)
    )
    coverers = plays.loc[active, ["game_id", "play_id", "nfl_id", "team_abbr"]].copy()
    coverers["coverage_assignment"] = assignment.loc[active]
    coverers = coverers.rename(columns={"nfl_id": "defender_nfl_id", "team_abbr": "defender_team"})
    if targets.empty or coverers.empty:
        return pd.DataFrame(columns=columns)

    locations = _pass_forward_locations(pass_forward)
    targets = targets.merge(
        locations.rename(columns={"nfl_id": "receiver_nfl_id", "x": "rx", "y": "ry"}),
        on=["game_id", "play_id", "receiver_nfl_id"],
        how="inner",
    )
    coverers = coverers.merge(
        locations.rename(columns={"nfl_id": "defender_nfl_id", "x": "dx", "y": "dy"}),
        on=["game_id", "play_id", "defender_nfl_id"],
        how="inner",
    )
    paired = targets.merge(coverers, on=["game_id", "play_id"], how="inner")
    paired = paired.loc[
        (paired["receiver_nfl_id"] != paired["defender_nfl_id"])
        & (paired["receiver_team"].astype("string") != paired["defender_team"].astype("string"))
    ]
    if paired.empty:
        return pd.DataFrame(columns=columns)
    paired = paired.copy()
    paired["coverage_distance"] = np.hypot(
        paired["rx"].to_numpy(dtype=float) - paired["dx"].to_numpy(dtype=float),
        paired["ry"].to_numpy(dtype=float) - paired["dy"].to_numpy(dtype=float),
    )
    paired = paired.loc[paired["coverage_distance"] <= radius_yds]
    paired = paired.sort_values("coverage_distance", kind="mergesort")
    credited = paired.drop_duplicates(["game_id", "play_id", "receiver_nfl_id"], keep="first")
    credited = credited.assign(
        separation_allowed=pd.to_numeric(credited["separation_at_pass_forward"], errors="coerce")
    )
    return credited.loc[:, columns].reset_index(drop=True)


def defensive_back_outcomes(
    assignments: pd.DataFrame,
    players: pd.DataFrame,
    *,
    min_targets_covered: int,
) -> pd.DataFrame:
    """One row per DB with enough targets as the nearest defender."""
    columns = [
        "nfl_id",
        "draft_year",
        "n_targets_covered",
        "db_mean_separation_allowed",
        "db_completion_rate_allowed",
        "db_mean_epa_allowed",
    ]
    if assignments.empty:
        return pd.DataFrame(columns=columns)
    grouped = assignments.groupby("defender_nfl_id", as_index=False).agg(
        n_targets_covered=("play_id", "size"),
        db_mean_separation_allowed=("separation_allowed", "mean"),
        db_completion_rate_allowed=("is_completion", "mean"),
        db_mean_epa_allowed=("expected_points_added", "mean"),
    )
    grouped = grouped.loc[grouped["n_targets_covered"] >= min_targets_covered]
    grouped = grouped.rename(columns={"defender_nfl_id": "nfl_id"})
    years = players.loc[:, ["nfl_id", "draft_year"]]
    grouped = grouped.merge(years, on="nfl_id", how="left")
    return grouped.loc[:, columns]
