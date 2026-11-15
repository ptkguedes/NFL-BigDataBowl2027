"""Figures 1 and 2 for the write-up, drawn at runtime from the analysis result.

Nothing here writes a file unless the caller saves the figure. Figure 1 shows
one point per DB, so render it inside the Kaggle notebook and do not commit an
exported image of it to this repository.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bdb2027.scenarios import OUTCOME, PREDICTOR, deviation_frame

TEST_LABELS = {
    "te_primary_decel_separation": "TE brake -> separation",
    "te_secondary_ten_yd_separation": "TE 10-yd split -> separation",
    "te_secondary_three_cone_completion": "TE 3-cone -> completion (underpowered)",
    "db_primary_break_separation": "DB quicker break -> separation allowed",
    "db_secondary_retention_epa": "DB speed retention -> EPA allowed",
    "db_secondary_break_completion": "DB quicker break -> completion allowed",
}


def figure_retention_scatter(db_players: pd.DataFrame, ax=None):
    """Figure 1: within-class deviations, retention vs EPA allowed per target."""
    import matplotlib.pyplot as plt

    working = deviation_frame(db_players, PREDICTOR, OUTCOME)
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 4.4))
    else:
        fig = ax.figure
    for year, group in working.groupby("draft_year"):
        ax.scatter(group["x_dev"], group["y_dev"], label=str(int(year)), alpha=0.85)
    if len(working) >= 3 and float(np.sum(working["x_dev"] ** 2)) > 0:
        slope = float(np.sum(working["x_dev"] * working["y_dev"]) / np.sum(working["x_dev"] ** 2))
        grid = np.linspace(working["x_dev"].min(), working["x_dev"].max(), 50)
        ax.plot(grid, slope * grid, color="0.2", linewidth=1.2)
    ax.axhline(0, color="0.6", linewidth=0.8)
    ax.axvline(0, color="0.6", linewidth=0.8)
    ax.set_xlabel("Speed retention through the break (within draft class)")
    ax.set_ylabel("EPA allowed per credited target (within draft class)")
    ax.set_title(f"Figure 1. Speed retention and EPA allowed (n = {len(working)})")
    ax.legend(title="Draft class", frameon=False)
    fig.tight_layout()
    return fig


def _check_label(check: str, detail: str) -> str:
    if check == "leave_one_class_out":
        return detail
    if check == "coverage_split":
        return detail.split(" targets")[0] + " targets only"
    if check == "leave_one_player_out":
        return "drop any one player (range)"
    if check == "target_floor":
        return "at least 10 targets"
    return check.replace("_", " ")


def forest_rows(effects: pd.DataFrame, robustness: pd.DataFrame | None = None) -> pd.DataFrame:
    """Aggregate rows for Figure 2: label, estimate, interval, group."""
    rows = []
    for _, row in effects.iterrows():
        rows.append(
            {
                "label": TEST_LABELS.get(row["test_id"], row["test_id"]),
                "estimate": row["pearson_r"],
                "low": row["ci_low"],
                "high": row["ci_high"],
                "group": "family",
            }
        )
    if robustness is not None and not robustness.empty:
        for _, row in robustness.iterrows():
            if row["check"] == "main":
                continue
            rows.append(
                {
                    "label": "retention: " + _check_label(row["check"], str(row["detail"])),
                    "estimate": row["r"],
                    "low": row["ci_low"],
                    "high": row["ci_high"],
                    "group": "robustness",
                }
            )
    return pd.DataFrame(rows, columns=["label", "estimate", "low", "high", "group"])


def figure_forest(effects: pd.DataFrame, robustness: pd.DataFrame | None = None, ax=None):
    """Figure 2: intervals for the family of six and the retention robustness checks."""
    import matplotlib.pyplot as plt

    rows = forest_rows(effects, robustness).iloc[::-1].reset_index(drop=True)
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 0.38 * max(len(rows), 4) + 1.2))
    else:
        fig = ax.figure
    colors = {"family": "tab:blue", "robustness": "tab:orange"}
    for index, row in rows.iterrows():
        color = colors.get(row["group"], "0.3")
        ax.plot([row["low"], row["high"]], [index, index], color=color, linewidth=2)
        ax.plot(row["estimate"], index, "o", color=color)
    ax.axvline(0, color="0.5", linewidth=0.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows["label"])
    ax.set_xlim(-1, 1)
    ax.set_xlabel("Within-class correlation with interval")
    ax.set_title("Figure 2. Pre-registered family (blue) and retention checks (orange)")
    fig.tight_layout()
    return fig
