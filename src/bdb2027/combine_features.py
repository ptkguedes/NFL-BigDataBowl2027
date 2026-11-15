"""Movement features from 10 Hz Combine tracking.

Breaks are not labeled in `combine_tracking.csv`. A break is the first frame,
after the athlete is moving, where heading has changed by at least
`BREAK_HEADING_DEG` from the opening heading. Deceleration is the drop in
speed per second, not the published `a` column: the data page does not say
that `a` is signed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bdb2027.preregistration import (
    BREAK_HEADING_DEG,
    DB_BACKPEDAL_DRILL_NAME,
    FALLBACK_DT_SECONDS,
    INITIAL_HEADING_FRAMES,
    MAX_BREAK_TIME_S,
    MIN_ATTEMPT_FRAMES,
    RETENTION_WINDOW_SECONDS,
    START_SPEED_YPS,
    TE_SKILL_DRILL_TYPE,
    THREE_CONE_DRILL_TYPE,
)

ATTEMPT_KEYS: tuple[str, ...] = (
    "draft_year",
    "event_id",
    "nfl_id",
    "drill_type",
    "drill_name",
    "attempt",
)

FEATURE_COLUMNS: tuple[str, ...] = (
    *ATTEMPT_KEYS,
    "n_frames",
    "accel_peak",
    "decel_peak",
    "decel_magnitude",
    "time_to_break_s",
    "speed_before_break",
    "speed_after_break",
    "speed_retention",
)


def circular_mean_deg(degrees: np.ndarray) -> float:
    radians = np.deg2rad(np.asarray(degrees, dtype=float))
    return float(np.rad2deg(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def heading_delta_deg(direction: np.ndarray, origin: float) -> np.ndarray:
    delta = (np.asarray(direction, dtype=float) - origin + 180.0) % 360.0 - 180.0
    return np.abs(delta)


def features_for_attempt(
    times_s: np.ndarray,
    speed: np.ndarray,
    direction: np.ndarray,
    *,
    start_speed: float = START_SPEED_YPS,
    break_heading_deg: float = BREAK_HEADING_DEG,
    retention_window_s: float = RETENTION_WINDOW_SECONDS,
    initial_heading_frames: int = INITIAL_HEADING_FRAMES,
    min_frames: int = MIN_ATTEMPT_FRAMES,
    max_break_time_s: float | None = MAX_BREAK_TIME_S,
) -> dict[str, float]:
    """Kinematic summary for one drill attempt, already sorted by time.

    A break is only searched for within `max_break_time_s` of the attempt's
    first frame (amendment A3). `None` turns the cap off.
    """
    empty = {
        "n_frames": float(len(times_s)),
        "accel_peak": np.nan,
        "decel_peak": np.nan,
        "decel_magnitude": np.nan,
        "time_to_break_s": np.nan,
        "speed_before_break": np.nan,
        "speed_after_break": np.nan,
        "speed_retention": np.nan,
    }
    if len(times_s) < min_frames:
        return empty

    dt = np.diff(times_s, prepend=np.nan)
    bad_dt = ~np.isfinite(dt) | (dt <= 0)
    dt = dt.copy()
    dt[bad_dt] = np.nan
    signed_accel = np.diff(speed, prepend=np.nan) / dt

    finite_accel = signed_accel[np.isfinite(signed_accel)]
    if finite_accel.size:
        empty["accel_peak"] = float(np.max(finite_accel))
        empty["decel_peak"] = float(np.min(finite_accel))
        empty["decel_magnitude"] = float(max(0.0, -empty["decel_peak"]))

    moving = np.isfinite(speed) & (speed >= start_speed)
    if not moving.any():
        return empty
    start_index = int(np.flatnonzero(moving)[0])
    heading_slice = direction[start_index : start_index + initial_heading_frames]
    heading_slice = heading_slice[np.isfinite(heading_slice)]
    if heading_slice.size == 0:
        return empty
    origin = circular_mean_deg(heading_slice)
    delta = heading_delta_deg(direction, origin)
    after_start = np.arange(len(delta)) >= start_index
    in_window = np.ones(len(delta), dtype=bool)
    if max_break_time_s is not None:
        elapsed = np.asarray(times_s, dtype=float) - float(np.nanmin(times_s))
        in_window = elapsed <= max_break_time_s + 1e-9
    break_candidates = np.flatnonzero((delta >= break_heading_deg) & after_start & in_window)
    if break_candidates.size == 0:
        return empty

    break_index = int(break_candidates[0])
    break_time = float(times_s[break_index])
    empty["time_to_break_s"] = break_time - float(times_s[start_index])

    before = (times_s >= break_time - retention_window_s) & (times_s < break_time)
    after = (times_s > break_time) & (times_s <= break_time + retention_window_s)
    before_speed = speed[before & np.isfinite(speed)]
    after_speed = speed[after & np.isfinite(speed)]
    if before_speed.size:
        empty["speed_before_break"] = float(np.median(before_speed))
    if after_speed.size:
        empty["speed_after_break"] = float(np.median(after_speed))
    if (
        np.isfinite(empty["speed_before_break"])
        and empty["speed_before_break"] > 0
        and np.isfinite(empty["speed_after_break"])
    ):
        empty["speed_retention"] = empty["speed_after_break"] / empty["speed_before_break"]
    return empty


def _seconds_from_start(time_values: pd.Series) -> np.ndarray:
    parsed = pd.to_datetime(time_values, utc=True, errors="coerce")
    if parsed.notna().sum() >= 2:
        origin = parsed.min()
        return (parsed - origin).dt.total_seconds().to_numpy(dtype=float)
    return np.arange(len(time_values), dtype=float) * FALLBACK_DT_SECONDS


def movement_features(tracking: pd.DataFrame) -> pd.DataFrame:
    """One row per drill attempt for player entities."""
    if tracking.empty:
        return pd.DataFrame(columns=list(FEATURE_COLUMNS))

    frame = tracking.copy()
    if "entity_type" in frame.columns:
        entity = frame["entity_type"].astype("string").str.upper()
        frame = frame.loc[entity.eq("PLAYER") | entity.isna()]
    frame = frame.loc[frame["nfl_id"].notna()]
    if frame.empty:
        return pd.DataFrame(columns=list(FEATURE_COLUMNS))

    rows: list[dict[str, object]] = []
    grouped = frame.groupby(list(ATTEMPT_KEYS), dropna=False, sort=False)
    for key, group in grouped:
        ordered = group.sort_values("time", kind="mergesort")
        features = features_for_attempt(
            _seconds_from_start(ordered["time"]),
            ordered["s"].to_numpy(dtype=float),
            ordered["dir"].to_numpy(dtype=float),
        )
        if not isinstance(key, tuple):
            key = (key,)
        row: dict[str, object] = dict(zip(ATTEMPT_KEYS, key, strict=True))
        row.update(features)
        rows.append(row)
    return pd.DataFrame(rows, columns=list(FEATURE_COLUMNS))


def _median_by_player(attempts: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    value_columns = list(columns.values())
    if attempts.empty:
        return pd.DataFrame(columns=["nfl_id", "draft_year", *value_columns])
    named = attempts.rename(columns=columns)
    medians = named.groupby(["nfl_id", "draft_year"], as_index=False)[value_columns].median()
    return medians.loc[:, ["nfl_id", "draft_year", *value_columns]]


def predictor_table(attempts: pd.DataFrame, combine_results: pd.DataFrame) -> pd.DataFrame:
    """Player-by-draft-year predictors used by the pre-registered tests."""
    if attempts.empty:
        skill = attempts
        cone = attempts
        backpedal = attempts
    else:
        skill = attempts.loc[attempts["drill_type"].eq(TE_SKILL_DRILL_TYPE)]
        cone = attempts.loc[attempts["drill_type"].eq(THREE_CONE_DRILL_TYPE)]
        backpedal = attempts.loc[attempts["drill_name"].eq(DB_BACKPEDAL_DRILL_NAME)]
    te = _median_by_player(
        skill,
        {
            "decel_magnitude": "te_skill_decel_magnitude",
            "speed_retention": "te_skill_speed_retention",
        },
    )
    cone_features = _median_by_player(cone, {"decel_magnitude": "three_cone_decel_magnitude"})
    db = _median_by_player(
        backpedal,
        {
            "time_to_break_s": "db_break_time_s",
            "speed_retention": "db_speed_retention",
            "decel_magnitude": "db_decel_magnitude",
        },
    )
    stopwatch_cols = [
        "nfl_id",
        "draft_year",
        "ten_yd_split",
        "three_cone",
        "forty",
        "combine_position",
    ]
    available = [col for col in stopwatch_cols if col in combine_results.columns]
    stopwatch = combine_results.loc[:, available]
    merged = stopwatch
    for part in (te, cone_features, db):
        if part.empty:
            continue
        merged = merged.merge(part, on=["nfl_id", "draft_year"], how="outer")
    return merged
