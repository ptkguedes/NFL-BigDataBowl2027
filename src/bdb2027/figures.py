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


def _cb_axis_label(row: pd.Series) -> str:
    name = str(row["display_name"]).strip()
    if not name or name in {"<NA>", "nan", "None"}:
        name = str(int(row["nfl_id"]))
    year = row["draft_year"]
    if pd.notna(year):
        return f"{name} ({int(year)})"
    return name


def figure_cb_coverage(table: pd.DataFrame, ax=None):
    """Exploratory dot plot of shrunk EPA allowed for CBs who meet the target floor.

    Man and zone are separate points. The bar is the plugged-in 95% posterior
    interval. Nothing is written unless the caller saves the figure. One point
    per CB, so do not export it outside the Kaggle notebook.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    if ax is None:
        if table.empty:
            n_cbs = 0
        else:
            meeting = table.loc[table["meets_floor"].astype(bool), "nfl_id"]
            n_cbs = int(meeting.nunique())
        fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.42 * max(n_cbs, 1) + 1.2)))
    else:
        fig = ax.figure
    plot = table.iloc[0:0] if table.empty else table.loc[table["meets_floor"].astype(bool)].copy()
    if plot.empty:
        ax.set_title("Exploratory. No CB met the man/zone target floor")
        ax.set_xlabel("Shrunk EPA allowed per credited target")
        fig.tight_layout()
        return fig

    order: list[tuple[float, int]] = []
    for nfl_id, group in plot.groupby("nfl_id", sort=False):
        man = group.loc[group["coverage"].eq("man"), "epa_shrunk"]
        zone = group.loc[group["coverage"].eq("zone"), "epa_shrunk"]
        anchor = float(man.iloc[0]) if not man.empty else float(zone.iloc[0])
        if not np.isfinite(anchor):
            anchor = float("inf")
        order.append((anchor, int(nfl_id)))
    order.sort()
    colors = {"man": "tab:blue", "zone": "tab:orange"}
    labels = []
    for position, (_, nfl_id) in enumerate(order):
        group = plot.loc[plot["nfl_id"].eq(nfl_id)]
        labels.append(_cb_axis_label(group.iloc[0]))
        endpoints = []
        for _, row in group.iterrows():
            color = colors.get(str(row["coverage"]), "0.4")
            y_value = position
            low = row["epa_ci_low"]
            high = row["epa_ci_high"]
            if np.isfinite(low) and np.isfinite(high):
                ax.plot([low, high], [y_value, y_value], color=color, linewidth=2, alpha=0.85)
            if np.isfinite(row["epa_shrunk"]):
                ax.plot(row["epa_shrunk"], y_value, "o", color=color, markersize=6)
                endpoints.append(float(row["epa_shrunk"]))
        if len(endpoints) == 2:
            ax.plot(endpoints, [position, position], color="0.75", linewidth=1, zorder=0)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Shrunk EPA allowed per credited target")
    ax.set_title("Exploratory. CB EPA allowed in man (blue) and zone (orange)")
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color="tab:blue", label="man", linestyle="None"),
            Line2D([0], [0], marker="o", color="tab:orange", label="zone", linestyle="None"),
        ],
        frameon=False,
    )
    fig.tight_layout()
    return fig


def figure_threat_effects(effects: pd.DataFrame, ax=None):
    """Exploratory forest of threat-model log-odds per 1 SD. The intercept is omitted."""
    import matplotlib.pyplot as plt

    slopes = effects.iloc[0:0] if effects.empty else effects.loc[effects["term"].ne("intercept")]
    slopes = slopes.iloc[::-1].reset_index(drop=True)
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.2, 0.42 * max(len(slopes), 3) + 1.2))
    else:
        fig = ax.figure
    if slopes.empty:
        ax.set_title("Exploratory. Threat model was not fit")
        ax.set_xlabel("Log-odds of a completion per 1 SD")
        fig.tight_layout()
        return fig
    for index, row in slopes.iterrows():
        low = row["ci_low"]
        high = row["ci_high"]
        if np.isfinite(low) and np.isfinite(high):
            ax.plot([low, high], [index, index], color="tab:purple", linewidth=2)
        if np.isfinite(row["coef"]):
            ax.plot(row["coef"], index, "o", color="tab:purple")
    ax.axvline(0, color="0.5", linewidth=0.8)
    ax.set_yticks(range(len(slopes)))
    ax.set_yticklabels(slopes["term"])
    ax.set_xlabel("Log-odds of a completion per 1 SD")
    ax.set_title("Exploratory. CB threat model (not pre-registered)")
    fig.tight_layout()
    return fig
