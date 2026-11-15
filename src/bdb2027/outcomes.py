"""In-game outcomes for tight ends and defensive backs.

Tight-end separation and target results come from `player_play.csv`.
Separation allowed, completions allowed, and EPA allowed for defensive backs
are not published columns. They are assigned by finding the nearest player in
the pre-registered DB position set at the `pass_forward` tracking frame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bdb2027.preregistration import DB_POSITIONS, TE_POSITIONS


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

    Distance is Euclidean yards in the tracking coordinate system. Plays with
    no receiver coordinate, or no DB coordinate, are dropped.
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
