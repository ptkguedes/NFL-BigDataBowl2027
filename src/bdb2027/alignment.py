"""Alignment check: are DBs with no break by 5.5 s lined up deeper?

Not pre-registered. Compares `cushion` (published pre-snap distance between
the defender and the receiver he is aligned over) for the DBs in the break
tests, split by `db_break_censored`. Outputs are aggregates only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bdb2027.io import read_csv_columns
from bdb2027.preregistration import REGULAR_SEASON_TYPE

PERMUTATIONS: int = 5000
PERMUTATION_SEED: int = 2027
SAFETY_POSITIONS = frozenset({"SS", "FS", "S"})
CUSHION_COLUMNS = (
    "game_id",
    "play_id",
    "nfl_id",
    "cushion",
    "lined_up_position",
    "play_nullified_by_penalty",
)


def load_db_cushion(data_dir: Path, db_ids: set[int], games: pd.DataFrame) -> pd.DataFrame:
    reg = set(games.loc[games["season_type"].astype("string").eq(REGULAR_SEASON_TYPE), "game_id"])

    def keep(chunk: pd.DataFrame) -> pd.DataFrame:
        flag = chunk["play_nullified_by_penalty"].astype("string").str.upper().eq("Y")
        mask = chunk["nfl_id"].isin(db_ids) & chunk["game_id"].isin(reg) & ~flag.fillna(False)
        return chunk.loc[mask & chunk["cushion"].notna()]

    return read_csv_columns(Path(data_dir) / "player_play.csv", CUSHION_COLUMNS, predicate=keep)


def _within_class_gap(frame: pd.DataFrame, value: str) -> float:
    dev = frame[value] - frame.groupby("draft_year")[value].transform("mean")
    censored = frame["censored"].to_numpy(dtype=bool)
    if censored.all() or (~censored).all():
        return float("nan")
    return float(dev[censored].mean() - dev[~censored].mean())


def _permutation_p(frame: pd.DataFrame, value: str, *, draws: int, seed: int) -> float:
    observed = _within_class_gap(frame, value)
    if not np.isfinite(observed):
        return float("nan")
    rng = np.random.default_rng(seed)
    shuffled = frame.copy()
    hits = 0
    for _ in range(draws):
        shuffled["censored"] = (
            frame.groupby("draft_year")["censored"]
            .transform(lambda s: rng.permutation(s.to_numpy()))
            .astype(bool)
        )
        if abs(_within_class_gap(shuffled, value)) >= abs(observed) - 1e-12:
            hits += 1
    return (hits + 1) / (draws + 1)


def cushion_check(
    cushion_rows: pd.DataFrame,
    db_players: pd.DataFrame,
    players: pd.DataFrame,
    assignments: pd.DataFrame | None = None,
    *,
    draws: int = PERMUTATIONS,
    seed: int = PERMUTATION_SEED,
) -> pd.DataFrame:
    """Mean cushion and safety share for censored vs detected breakers."""
    base = db_players.loc[
        db_players["db_break_time_s"].notna() & db_players["db_break_censored"].notna(),
        ["nfl_id", "draft_year", "db_break_censored"],
    ].drop_duplicates("nfl_id")
    base = base.rename(columns={"db_break_censored": "censored"})
    base["censored"] = base["censored"].astype(bool)
    position = players.drop_duplicates("nfl_id").set_index("nfl_id")["nfl_position"]
    base["is_safety"] = base["nfl_id"].map(position).isin(SAFETY_POSITIONS).astype(float)

    per_db = cushion_rows.groupby("nfl_id").agg(
        mean_cushion=("cushion", "mean"), n_plays=("cushion", "size")
    )
    frames = {"all regular-season snaps with a cushion": per_db}
    if assignments is not None and not assignments.empty:
        credited = cushion_rows.merge(
            assignments.loc[:, ["game_id", "play_id", "defender_nfl_id"]],
            left_on=["game_id", "play_id", "nfl_id"],
            right_on=["game_id", "play_id", "defender_nfl_id"],
            how="inner",
        )
        frames["credited targets only"] = credited.groupby("nfl_id").agg(
            mean_cushion=("cushion", "mean"), n_plays=("cushion", "size")
        )

    rows = []
    for label, stats in frames.items():
        merged = base.merge(stats, left_on="nfl_id", right_index=True, how="inner")
        rows.append(_summary_row(label, "mean_cushion", merged, draws=draws, seed=seed))
    rows.append(_summary_row("share of safeties", "is_safety", base, draws=draws, seed=seed))
    return pd.DataFrame(rows)


def _summary_row(
    label: str, value: str, merged: pd.DataFrame, *, draws: int, seed: int
) -> dict[str, object]:
    censored = merged["censored"].to_numpy(dtype=bool)
    return {
        "measure": label,
        "value": value,
        "n_censored": int(censored.sum()),
        "n_detected": int((~censored).sum()),
        "mean_censored": float(merged.loc[censored, value].mean()),
        "mean_detected": float(merged.loc[~censored, value].mean()),
        "within_class_gap": _within_class_gap(merged, value),
        "permutation_p": _permutation_p(merged, value, draws=draws, seed=seed),
    }
