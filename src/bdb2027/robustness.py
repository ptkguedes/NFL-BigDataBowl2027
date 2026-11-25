"""Robustness checks for the DB speed-retention -> EPA-allowed association.

Not part of the pre-registered family. Every function returns aggregate
statistics (correlations, intervals, counts), never player rows, so the output
can be shown in a write-up without redistributing competition data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bdb2027.linkage import within_class_pearson
from bdb2027.outcomes import defensive_back_outcomes

PREDICTOR = "db_speed_retention"
OUTCOME = "db_mean_epa_allowed"
BOOTSTRAP_DRAWS: int = 2000
BOOTSTRAP_SEED: int = 2027
SPLIT_MIN_TARGETS: int = 3
STRICT_MIN_TARGETS: int = 10
MAN_ASSIGNMENT = "MAN"

ROW_COLUMNS = [
    "check",
    "detail",
    "method",
    "n_players",
    "class_counts",
    "r",
    "ci_low",
    "ci_high",
    "p_value",
]


def _row(check: str, detail: str, stats: dict[str, object]) -> dict[str, object]:
    return {
        "check": check,
        "detail": detail,
        "method": stats.get("method", "pearson"),
        "n_players": stats.get("n_players", 0),
        "class_counts": stats.get("class_counts", ""),
        "r": stats.get("pearson_r", np.nan),
        "ci_low": stats.get("ci_low", np.nan),
        "ci_high": stats.get("ci_high", np.nan),
        "p_value": stats.get("p_value", np.nan),
    }


def _complete(frame: pd.DataFrame, predictor: str, outcome: str) -> pd.DataFrame:
    working = frame.loc[:, ["draft_year", predictor, outcome]].apply(pd.to_numeric, errors="coerce")
    return working.dropna().reset_index(drop=True)


def leave_one_class_out(
    frame: pd.DataFrame, predictor: str = PREDICTOR, outcome: str = OUTCOME
) -> list[dict[str, object]]:
    rows = []
    for year in sorted(frame["draft_year"].dropna().unique()):
        kept = frame.loc[frame["draft_year"] != year]
        stats = within_class_pearson(kept, predictor, outcome)
        rows.append(_row("leave_one_class_out", f"without {int(year)}", stats))
    return rows


def leave_one_player_out_range(
    frame: pd.DataFrame, predictor: str = PREDICTOR, outcome: str = OUTCOME
) -> dict[str, object]:
    working = _complete(frame, predictor, outcome)
    values = []
    for index in working.index:
        stats = within_class_pearson(working.drop(index=index), predictor, outcome)
        values.append(stats["pearson_r"])
    finite = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    full = within_class_pearson(working, predictor, outcome)
    return {
        "check": "leave_one_player_out",
        "detail": "range of r when any one player is removed",
        "method": "pearson",
        "n_players": full["n_players"],
        "class_counts": full["class_counts"],
        "r": full["pearson_r"],
        "ci_low": float(finite.min()) if finite.size else np.nan,
        "ci_high": float(finite.max()) if finite.size else np.nan,
        "p_value": np.nan,
    }


def bootstrap_interval(
    frame: pd.DataFrame,
    predictor: str = PREDICTOR,
    outcome: str = OUTCOME,
    *,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, object]:
    """Percentile interval from resampling players with replacement inside each class."""
    working = _complete(frame, predictor, outcome)
    full = within_class_pearson(working, predictor, outcome)
    rng = np.random.default_rng(seed)
    groups = [g.index.to_numpy() for _, g in working.groupby("draft_year")]
    estimates = []
    for _ in range(draws):
        picks = np.concatenate([rng.choice(idx, size=idx.size, replace=True) for idx in groups])
        stats = within_class_pearson(working.loc[picks].reset_index(drop=True), predictor, outcome)
        if np.isfinite(stats["pearson_r"]):
            estimates.append(stats["pearson_r"])
    values = np.asarray(estimates, dtype=float)
    share_neg = float((values < 0).mean()) if values.size else np.nan
    return {
        "check": "bootstrap",
        "detail": f"{draws} within-class resamples, seed {seed}; p_value column = share of r >= 0",
        "method": "pearson",
        "n_players": full["n_players"],
        "class_counts": full["class_counts"],
        "r": full["pearson_r"],
        "ci_low": float(np.quantile(values, 0.025)) if values.size else np.nan,
        "ci_high": float(np.quantile(values, 0.975)) if values.size else np.nan,
        "p_value": 1.0 - share_neg if values.size else np.nan,
    }


def coverage_frames(
    assignments: pd.DataFrame,
    db_players: pd.DataFrame,
    players: pd.DataFrame,
    *,
    min_targets_covered: int = SPLIT_MIN_TARGETS,
    predictor: str = PREDICTOR,
) -> dict[str, pd.DataFrame]:
    """Per-DB outcomes rebuilt from man-only and zone-only credited targets."""
    if assignments.empty or "coverage_assignment" not in assignments.columns:
        return {}
    retention = db_players.loc[:, ["nfl_id", "draft_year", predictor]].drop_duplicates("nfl_id")
    is_man = assignments["coverage_assignment"].astype("string").eq(MAN_ASSIGNMENT).fillna(False)
    frames = {}
    for label, subset in (("man", assignments.loc[is_man]), ("zone", assignments.loc[~is_man])):
        outcomes = defensive_back_outcomes(subset, players, min_targets_covered=min_targets_covered)
        frames[label] = retention.merge(
            outcomes.drop(columns=["draft_year"]), on="nfl_id", how="inner"
        )
    return frames


def coverage_split(
    assignments: pd.DataFrame,
    db_players: pd.DataFrame,
    players: pd.DataFrame,
    *,
    min_targets_covered: int = SPLIT_MIN_TARGETS,
    predictor: str = PREDICTOR,
    outcome: str = OUTCOME,
) -> list[dict[str, object]]:
    """Recompute EPA allowed from man-only and zone-only credited targets.

    This robustness check stays an exact ``MAN`` versus everything-else split
    on the credited assignment. The exploratory per-CB table in
    ``cb_coverage`` uses a stricter man/zone/other map and is not this check.
    """
    rows = []
    if assignments.empty or "coverage_assignment" not in assignments.columns:
        return rows
    retention = db_players.loc[:, ["nfl_id", "draft_year", predictor]].drop_duplicates("nfl_id")
    is_man = assignments["coverage_assignment"].astype("string").eq(MAN_ASSIGNMENT).fillna(False)
    for label, subset in (("man", assignments.loc[is_man]), ("zone", assignments.loc[~is_man])):
        outcomes = defensive_back_outcomes(subset, players, min_targets_covered=min_targets_covered)
        merged = retention.merge(outcomes.drop(columns=["draft_year"]), on="nfl_id", how="inner")
        stats = within_class_pearson(merged, predictor, outcome)
        detail = f"{label} targets only, at least {min_targets_covered} per DB"
        rows.append(_row("coverage_split", detail, stats))
    return rows


def retention_robustness(result: dict[str, object], players: pd.DataFrame) -> pd.DataFrame:
    """All checks for the retention -> EPA row, as one aggregate table."""
    db_players = result["db_players"]
    assignments = result["assignments"]
    rows = [
        _row("main", "pre-registered row", within_class_pearson(db_players, PREDICTOR, OUTCOME))
    ]
    rows.append(
        _row(
            "spearman",
            "within-class ranks",
            within_class_pearson(db_players, PREDICTOR, OUTCOME, method="spearman"),
        )
    )
    rows.extend(leave_one_class_out(db_players))
    rows.append(leave_one_player_out_range(db_players))
    rows.append(bootstrap_interval(db_players))
    strict = db_players.loc[pd.to_numeric(db_players["n_targets_covered"]) >= STRICT_MIN_TARGETS]
    rows.append(
        _row(
            "target_floor",
            f"at least {STRICT_MIN_TARGETS} credited targets",
            within_class_pearson(strict, PREDICTOR, OUTCOME),
        )
    )
    rows.extend(coverage_split(assignments, db_players, players))
    return pd.DataFrame(rows, columns=ROW_COLUMNS)
