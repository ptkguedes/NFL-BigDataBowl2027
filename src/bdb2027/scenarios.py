"""Probabilities and scenario profiles for speed retention -> EPA allowed.

Not pre-registered. The posterior is a within-class bootstrap approximation
(flat prior, players resampled with replacement inside each draft class). Each
draw fits the pooled within-class slope of EPA allowed per credited target on
speed retention, plus the residual spread. Outputs are aggregate numbers only.

Assumptions, stated so the write-up can repeat them:
- The slope is linear in the observed retention range and is the same in all
  draft classes.
- A "season" is ASSUMED_TARGETS_PER_SEASON targets in coverage. That is an
  assumption about a full-time starting DB, not a count from these files,
  which only credit targets between draftees. The observed median of credited
  targets per DB-season is reported next to it.
- Scenario profiles use the observed 25th and 75th percentiles of
  within-class retention deviations, so they stay inside the data.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

PREDICTOR = "db_speed_retention"
OUTCOME = "db_mean_epa_allowed"
POSTERIOR_DRAWS: int = 4000
POSTERIOR_SEED: int = 2027
ASSUMED_TARGETS_PER_SEASON: int = 60
LOW_QUANTILE: float = 0.25
HIGH_QUANTILE: float = 0.75


def _normal_cdf(value: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(value, dtype=float) / math.sqrt(2.0)))


def deviation_frame(
    frame: pd.DataFrame, predictor: str = PREDICTOR, outcome: str = OUTCOME
) -> pd.DataFrame:
    """Within-class deviations for players with both values."""
    working = frame.loc[:, ["draft_year", predictor, outcome]].apply(pd.to_numeric, errors="coerce")
    working = working.dropna().reset_index(drop=True)
    working["x_dev"] = working[predictor] - working.groupby("draft_year")[predictor].transform(
        "mean"
    )
    working["y_dev"] = working[outcome] - working.groupby("draft_year")[outcome].transform("mean")
    return working


def _fit(working: pd.DataFrame, predictor: str, outcome: str) -> tuple[float, float, float]:
    """Slope, residual sd, and median outcome deviation, after re-demeaning."""
    x = working[predictor] - working.groupby("draft_year")[predictor].transform("mean")
    y = working[outcome] - working.groupby("draft_year")[outcome].transform("mean")
    x = x.to_numpy(dtype=float)
    y = y.to_numpy(dtype=float)
    sxx = float(np.sum(x * x))
    if sxx <= 0:
        return (np.nan, np.nan, np.nan)
    slope = float(np.sum(x * y) / sxx)
    n_classes = working["draft_year"].nunique()
    dof = max(len(x) - n_classes - 1, 1)
    sigma = float(math.sqrt(np.sum((y - slope * x) ** 2) / dof))
    return (slope, sigma, float(np.median(y)))


def posterior_draws(
    frame: pd.DataFrame,
    predictor: str = PREDICTOR,
    outcome: str = OUTCOME,
    *,
    draws: int = POSTERIOR_DRAWS,
    seed: int = POSTERIOR_SEED,
) -> pd.DataFrame:
    working = deviation_frame(frame, predictor, outcome)
    rng = np.random.default_rng(seed)
    groups = [g.index.to_numpy() for _, g in working.groupby("draft_year")]
    rows = []
    for _ in range(draws):
        picks = np.concatenate([rng.choice(idx, size=idx.size, replace=True) for idx in groups])
        slope, sigma, median_dev = _fit(working.loc[picks], predictor, outcome)
        if np.isfinite(slope):
            rows.append((slope, sigma, median_dev))
    return pd.DataFrame(rows, columns=["slope", "sigma", "median_dev"])


def _band(values: np.ndarray) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return (np.nan, np.nan, np.nan)
    return (
        float(np.median(values)),
        float(np.quantile(values, 0.05)),
        float(np.quantile(values, 0.95)),
    )


def scenario_summary(
    frame: pd.DataFrame,
    *,
    label: str = "all credited targets",
    targets_per_season: int = ASSUMED_TARGETS_PER_SEASON,
    observed_targets_per_season: float | None = None,
    draws: int = POSTERIOR_DRAWS,
    seed: int = POSTERIOR_SEED,
    predictor: str = PREDICTOR,
    outcome: str = OUTCOME,
) -> pd.DataFrame:
    """One aggregate table: probabilities and high-vs-low scenario differences.

    Bands are 90% (5th to 95th percentile of the bootstrap posterior).
    """
    working = deviation_frame(frame, predictor, outcome)
    columns = ["subset", "quantity", "estimate", "low_90", "high_90", "n_players", "note"]
    if len(working) < 5:
        return pd.DataFrame(columns=columns)
    post = posterior_draws(frame, predictor, outcome, draws=draws, seed=seed)
    x_low = float(np.quantile(working["x_dev"], LOW_QUANTILE))
    x_high = float(np.quantile(working["x_dev"], HIGH_QUANTILE))
    raw_low = float(np.quantile(working[predictor], LOW_QUANTILE))
    raw_high = float(np.quantile(working[predictor], HIGH_QUANTILE))
    slope = post["slope"].to_numpy()
    sigma = post["sigma"].to_numpy()
    median_dev = post["median_dev"].to_numpy()
    n = len(working)

    def row(quantity: str, values: np.ndarray, note: str) -> dict[str, object]:
        estimate, low, high = _band(values)
        return {
            "subset": label,
            "quantity": quantity,
            "estimate": estimate,
            "low_90": low,
            "high_90": high,
            "n_players": n,
            "note": note,
        }

    rows = [
        {
            "subset": label,
            "quantity": "P(slope < 0)",
            "estimate": float(np.mean(slope < 0)),
            "low_90": np.nan,
            "high_90": np.nan,
            "n_players": n,
            "note": "share of posterior draws",
        },
        row(
            "P(top-quartile DB allows less EPA/target than class median)",
            _normal_cdf((median_dev - slope * x_high) / sigma),
            "posterior predictive for a new DB at the within-class 75th percentile",
        ),
        row(
            "P(bottom-quartile DB allows less EPA/target than class median)",
            _normal_cdf((median_dev - slope * x_low) / sigma),
            "posterior predictive for a new DB at the within-class 25th percentile",
        ),
        row(
            "EPA/target difference, high minus low retention",
            slope * (x_high - x_low),
            f"profiles at within-class p75 and p25 (raw retention about {raw_high:.2f} "
            f"vs {raw_low:.2f})",
        ),
        row(
            f"EPA per season difference at {targets_per_season} targets (assumed)",
            slope * (x_high - x_low) * targets_per_season,
            "assumption: full-time starter target volume, not from these files",
        ),
    ]
    if observed_targets_per_season is not None and np.isfinite(observed_targets_per_season):
        rows.append(
            row(
                "EPA per season difference at observed credited volume",
                slope * (x_high - x_low) * observed_targets_per_season,
                f"median credited targets per DB-season = {observed_targets_per_season:.1f} "
                "(draftee-on-draftee only)",
            )
        )
    return pd.DataFrame(rows, columns=columns)


def observed_targets_per_db_season(assignments: pd.DataFrame, games: pd.DataFrame) -> float:
    if assignments.empty:
        return float("nan")
    seasons = games.loc[:, ["game_id", "season"]].drop_duplicates("game_id")
    merged = assignments.merge(seasons, on="game_id", how="left")
    counts = merged.groupby(["defender_nfl_id", "season"]).size()
    return float(counts.median()) if len(counts) else float("nan")


def scenario_report(
    result: dict[str, object],
    players: pd.DataFrame,
    games: pd.DataFrame,
    *,
    draws: int = POSTERIOR_DRAWS,
    seed: int = POSTERIOR_SEED,
) -> pd.DataFrame:
    """Scenarios on all credited targets, then man-only and zone-only."""
    from bdb2027.robustness import coverage_frames

    observed = observed_targets_per_db_season(result["assignments"], games)
    parts = [
        scenario_summary(
            result["db_players"],
            label="all credited targets",
            observed_targets_per_season=observed,
            draws=draws,
            seed=seed,
        )
    ]
    for label, frame in coverage_frames(
        result["assignments"], result["db_players"], players
    ).items():
        parts.append(scenario_summary(frame, label=f"{label} targets only", draws=draws, seed=seed))
    parts = [part for part in parts if not part.empty]
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)
