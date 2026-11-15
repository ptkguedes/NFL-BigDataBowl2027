"""Within-draft-class correlations, effect sizes, and Fisher intervals.

The effect size is the Pearson correlation of within-class deviations. Class
means are removed before the correlation, so a year that was timed or coded
differently cannot create the association by itself. The interval treats
players as independent after that demeaning; it is not a cluster-robust interval.
Since amendment A4 (2026-11-15) the Fisher standard error is
1 / sqrt(n - 3 - (k - 1)) for k draft classes.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from bdb2027.preregistration import (
    MIN_CLASS_PLAYERS,
    PREREGISTERED_TESTS,
    SMALL_N_THRESHOLD,
    UNDERPOWERED_TESTS,
    PreRegisteredTest,
    bonferroni_alpha,
    family_size,
)


def _fisher_interval(
    correlation: float,
    n_players: int,
    z_critical: float = 1.96,
    n_classes: int = 1,
) -> tuple[float, float]:
    extra_means = max(int(n_classes) - 1, 0)
    dof = n_players - 3 - extra_means
    if dof <= 0 or not np.isfinite(correlation):
        return (np.nan, np.nan)
    clipped = float(np.clip(correlation, -0.999999, 0.999999))
    z_value = np.arctanh(clipped)
    standard_error = 1.0 / math.sqrt(dof)
    low = math.tanh(z_value - z_critical * standard_error)
    high = math.tanh(z_value + z_critical * standard_error)
    return (float(low), float(high))


def within_class_pearson(
    frame: pd.DataFrame,
    predictor: str,
    outcome: str,
    *,
    class_col: str = "draft_year",
    orient: str = "as_is",
    min_class_players: int = MIN_CLASS_PLAYERS,
) -> dict[str, object]:
    """Pooled within-class Pearson r and a 95% Fisher interval."""
    result: dict[str, object] = {
        "n_players": 0,
        "n_classes": 0,
        "class_counts": "",
        "pearson_r": np.nan,
        "ci_low": np.nan,
        "ci_high": np.nan,
        "small_n": True,
    }
    if frame.empty or predictor not in frame.columns or outcome not in frame.columns:
        return result

    working = frame.loc[:, [class_col, predictor, outcome]].copy()
    working[predictor] = pd.to_numeric(working[predictor], errors="coerce")
    working[outcome] = pd.to_numeric(working[outcome], errors="coerce")
    if orient == "flip":
        working[predictor] = -working[predictor]
    elif orient != "as_is":
        raise ValueError(f"unknown orient: {orient}")
    working = working.dropna()
    if working.empty:
        return result

    counts = working.groupby(class_col)[predictor].transform("size")
    working = working.loc[counts >= min_class_players]
    if working.empty:
        return result

    class_sizes = working.groupby(class_col).size()
    working["x_dev"] = working[predictor] - working.groupby(class_col)[predictor].transform("mean")
    working["y_dev"] = working[outcome] - working.groupby(class_col)[outcome].transform("mean")
    x_dev = working["x_dev"].to_numpy(dtype=float)
    y_dev = working["y_dev"].to_numpy(dtype=float)
    n_players = int(len(working))
    if n_players < 3 or np.std(x_dev) == 0 or np.std(y_dev) == 0:
        correlation = np.nan
    else:
        correlation = float(np.corrcoef(x_dev, y_dev)[0, 1])
    ci_low, ci_high = _fisher_interval(correlation, n_players, n_classes=int(class_sizes.shape[0]))
    result.update(
        {
            "n_players": n_players,
            "n_classes": int(class_sizes.shape[0]),
            "class_counts": ",".join(f"{year}:{int(size)}" for year, size in class_sizes.items()),
            "pearson_r": correlation,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "small_n": n_players < SMALL_N_THRESHOLD,
        }
    )
    return result


def evaluate_tests(
    frames: dict[str, pd.DataFrame],
    tests: tuple[PreRegisteredTest, ...] = PREREGISTERED_TESTS,
) -> pd.DataFrame:
    """Evaluate the pre-registered family. `frames` is keyed by angle, `TE` or `DB`."""
    rows: list[dict[str, object]] = []
    adjusted = bonferroni_alpha()
    for test in tests:
        stats = within_class_pearson(
            frames.get(test.angle, pd.DataFrame()),
            test.predictor,
            test.outcome,
            orient=test.orient,
        )
        rows.append(
            {
                "test_id": test.test_id,
                "angle": test.angle,
                "role": test.role,
                "predictor": test.predictor,
                "outcome": test.outcome,
                "orient": test.orient,
                "expected_sign": test.expected_sign,
                "question": test.question,
                "family_size": family_size(),
                "bonferroni_alpha": adjusted,
                "underpowered": test.test_id in UNDERPOWERED_TESTS,
                **stats,
            }
        )
    return pd.DataFrame(rows)
