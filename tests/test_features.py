"""Movement-feature tests on constructed 10 Hz sequences."""

import numpy as np
import pandas as pd

from bdb2027.combine_features import features_for_attempt, movement_features


def test_brake_and_break_magnitudes() -> None:
    times = np.arange(0.0, 0.9, 0.1)
    speed = np.array([2, 4, 6, 8, 8, 3, 3, 3, 3], dtype=float)
    direction = np.array([0, 0, 0, 0, 0, 80, 80, 80, 80], dtype=float)
    features = features_for_attempt(times, speed, direction)
    assert features["accel_peak"] == pytest_approx(20.0)
    assert features["decel_peak"] == pytest_approx(-50.0)
    assert features["decel_magnitude"] == pytest_approx(50.0)
    assert features["time_to_break_s"] == pytest_approx(0.5)
    assert features["speed_retention"] == pytest_approx(0.375)


def test_ball_rows_do_not_enter_the_attempt() -> None:
    rows = []
    for index, (speed, direction) in enumerate(
        zip([2, 4, 6, 8, 8, 3, 3, 3, 3], [0, 0, 0, 0, 0, 80, 80, 80, 80], strict=True)
    ):
        rows.append(_row(index, "PLAYER", speed, direction, nfl_id=7))
    rows.append(_row(3, "BALL", speed=40, direction=180, nfl_id=7))
    features = movement_features(pd.DataFrame(rows))
    assert len(features) == 1
    assert features.loc[0, "decel_magnitude"] == pytest_approx(50.0)


def test_no_break_leaves_time_missing_but_keeps_the_brake() -> None:
    times = np.arange(0.0, 0.6, 0.1)
    speed = np.array([2, 4, 6, 5, 4, 3], dtype=float)
    direction = np.zeros(6)
    features = features_for_attempt(times, speed, direction)
    assert np.isnan(features["time_to_break_s"])
    assert features["decel_magnitude"] == pytest_approx(10.0)


def _row(index: int, entity: str, speed: float, direction: float, nfl_id: int) -> dict[str, object]:
    return {
        "draft_year": 2023,
        "event_id": "attempt-1",
        "nfl_id": nfl_id,
        "entity_type": entity,
        "time": f"2023-03-01T00:00:00.{index * 100:03d}Z",
        "drill_type": "SKILL_DRILLS_TE",
        "drill_name": "TE_ROUTE",
        "attempt": 1,
        "x": float(index),
        "y": 10.0,
        "s": speed,
        "a": 0.0,
        "dir": direction,
    }


def pytest_approx(value: float) -> object:
    import pytest

    return pytest.approx(value)
