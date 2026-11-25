"""Per-CB man and zone coverage results. Exploratory, not pre-registered.

The pre-registered family still pools CB, SS, FS, DB, and S. This module
keeps only players whose ``nfl_position`` is CB and splits the targets the
existing credit rule already assigned to them.

Label
-----
The split uses the CB's own ``coverage_assignment``, not
``team_coverage_man_zone``.

The corner's assignment is the job he was given on that play. The team column
is the defensive shell, and it is the same for every defender on the play. A
Cover-1 shell is man with a deep zone behind it. A Cover-3 shell is zone, and
the two corners on the field are not doing the same job. Labeling both with
the shell would mix those responsibilities. The credit rule (amendment A2)
already requires an active ``coverage_assignment``, so the split uses the same
column that made the CB eligible.

``team_coverage_man_zone`` is loaded only for an agreement audit. Strings that
name both man and zone, or that match neither list, are ``other`` and stay out
of the man and zone rows. The audit counts them. The older retention
robustness check is a different rule: exact ``MAN`` versus everything else.
This module does not change that check.

Uncertainty
-----------
Each CB-coverage cell reports the raw mean and an empirical-Bayes shrinkage
estimate. Completion uses a beta-binomial model. EPA and separation use a
normal-normal model with a DerSimonian-Laird estimate of the between-CB
variance. Intervals are 95% posterior intervals with the hyperparameters
plugged in. They do not include uncertainty in the prior itself. A cell with
fewer than ``MIN_CB_COVERAGE_TARGETS`` credited targets is kept in the table
and flagged ``meets_floor=False``. ``small_n`` uses the same player-count
threshold as the pre-registered tables.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from bdb2027.preregistration import SMALL_N_THRESHOLD

MIN_CB_COVERAGE_TARGETS: int = 5
INTERVAL_METHOD: str = "empirical_bayes_plug_in_95"
LABEL_SOURCE: str = "coverage_assignment"
LABEL_ALTERNATIVE: str = "team_coverage_man_zone"
LABEL_REASON: str = (
    "The CB's coverage_assignment is his own job on the play. "
    "team_coverage_man_zone is the defensive shell and is shared by every "
    "defender on that play, so two corners in the same shell can have "
    "different jobs. The credit rule already requires an active "
    "coverage_assignment. The team shell is an agreement audit only."
)
Z_95: float = 1.96

# Zone responsibilities seen in the coverage-credit fixtures and in public
# NGS assignment strings. A token is zone when it contains one of these and
# does not also contain MAN. Unrecognized tokens stay "other".
_ZONE_MARKERS: tuple[str, ...] = (
    "ZONE",
    "DEEP",
    "CURL",
    "FLAT",
    "HOOK",
    "SEAM",
    "QUARTER",
    "HALF",
    "THIRD",
    "BRACKET",
    "PALM",
)
_EMPTY_TOKENS: frozenset[str] = frozenset({"", "<NA>", "NAN", "NONE", "NAT", "NO_ASSIGNMENT"})

COVERAGE_COLUMNS: tuple[str, ...] = (
    "nfl_id",
    "display_name",
    "draft_year",
    "coverage",
    "n_targets",
    "n_completions",
    "completion_rate",
    "completion_shrunk",
    "completion_ci_low",
    "completion_ci_high",
    "n_epa",
    "mean_epa",
    "epa_shrunk",
    "epa_ci_low",
    "epa_ci_high",
    "n_separation",
    "mean_separation",
    "separation_shrunk",
    "separation_ci_low",
    "separation_ci_high",
    "meets_floor",
    "small_n",
    "label_source",
    "interval_method",
    "exploratory",
    "preregistered",
)

AUDIT_COLUMNS: tuple[str, ...] = (
    "coverage_assignment",
    "player_label",
    "n_targets",
    "n_team_man",
    "n_team_zone",
    "n_team_other",
    "n_agree",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "label_source",
    "alternative_not_used",
    "reason",
    "min_targets_floor",
    "small_n_threshold",
    "interval_method",
    "position",
    "n_cbs_credited",
    "n_cbs_in_table",
    "n_man_rows",
    "n_zone_rows",
    "n_man_meet_floor",
    "n_zone_meet_floor",
    "n_credited_targets",
    "n_man_targets",
    "n_zone_targets",
    "n_other_targets",
    "n_both_labeled",
    "n_label_agree",
    "agreement_rate",
    "exploratory",
    "preregistered",
)


def classify_coverage_assignment(value: object) -> str:
    """Map one assignment string to ``man``, ``zone``, or ``other``."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "other"
    try:
        if pd.isna(value):
            return "other"
    except TypeError:
        pass
    text = str(value).strip().upper()
    if text in _EMPTY_TOKENS:
        return "other"
    has_man = "MAN" in text
    has_zone = any(marker in text for marker in _ZONE_MARKERS)
    if has_man and has_zone:
        return "other"
    if has_man:
        return "man"
    if has_zone:
        return "zone"
    return "other"


def cornerback_ids(players: pd.DataFrame) -> set[int]:
    """``nfl_position == CB`` only. Safeties and generic DB labels are excluded."""
    if players.empty or "nfl_position" not in players.columns:
        return set()
    position = players["nfl_position"].astype("string").str.strip().str.upper()
    ids = pd.to_numeric(players.loc[position.eq("CB"), "nfl_id"], errors="coerce").dropna()
    return {int(value) for value in ids.tolist()}


def _coerce_ids(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            continue
        out[column] = pd.to_numeric(out[column], errors="coerce")
    present = [column for column in columns if column in out.columns]
    out = out.dropna(subset=present)
    for column in present:
        out[column] = out[column].astype(np.int64)
    return out


def filter_cornerback_assignments(
    assignments: pd.DataFrame,
    players: pd.DataFrame,
) -> pd.DataFrame:
    """Keep credited targets whose defender is a CB."""
    if assignments.empty:
        return assignments.copy()
    ids = cornerback_ids(players)
    work = _coerce_ids(assignments, ("defender_nfl_id",))
    if not ids or work.empty:
        return work.iloc[0:0].copy()
    return work.loc[work["defender_nfl_id"].isin(ids)].reset_index(drop=True)


def _beta_prior(successes: np.ndarray, trials: np.ndarray) -> tuple[float, float]:
    """Method-of-moments Beta(alpha, beta) on CB completion rates.

    Prior strength is clipped to [2, 200]. The floor stops a tiny sample from
    pretending the prior is flat. The ceiling stops a sample with no extra
    variation from using an infinite prior.
    """
    if trials.size < 2 or float(np.sum(trials)) <= 0:
        return (1.0, 1.0)
    rates = successes / trials
    mu = float(np.average(rates, weights=trials))
    mu = float(np.clip(mu, 1e-3, 1.0 - 1e-3))
    weighted_var = float(np.average((rates - mu) ** 2, weights=trials))
    sampling = float(np.average(mu * (1.0 - mu) / trials, weights=trials))
    excess = weighted_var - sampling
    if excess <= 1e-8:
        strength = 200.0
    else:
        strength = mu * (1.0 - mu) / excess - 1.0
        strength = float(np.clip(strength, 2.0, 200.0))
    return (mu * strength, (1.0 - mu) * strength)


def _beta_posterior(
    successes: float,
    trials: float,
    alpha: float,
    beta: float,
) -> tuple[float, float, float]:
    posterior_a = alpha + successes
    posterior_b = beta + (trials - successes)
    mean = posterior_a / (posterior_a + posterior_b)
    variance = posterior_a * posterior_b / (
        (posterior_a + posterior_b) ** 2 * (posterior_a + posterior_b + 1.0)
    )
    sd = math.sqrt(max(variance, 0.0))
    low = float(np.clip(mean - Z_95 * sd, 0.0, 1.0))
    high = float(np.clip(mean + Z_95 * sd, 0.0, 1.0))
    return (float(mean), low, high)


def _normal_hyperparameters(groups: list[np.ndarray]) -> tuple[float, float, float]:
    """Return (mu0, tau2, sigma2) for the CB means in one coverage type."""
    means = np.asarray([float(np.mean(values)) for values in groups], dtype=float)
    ns = np.asarray([float(len(values)) for values in groups], dtype=float)
    sse = 0.0
    dof = 0
    for values in groups:
        if len(values) >= 2:
            sse += float(np.sum((values - np.mean(values)) ** 2))
            dof += len(values) - 1
    if dof > 0:
        sigma2 = sse / dof
    elif means.size > 1:
        sigma2 = float(np.var(means, ddof=1))
    else:
        sigma2 = 1.0
    if not np.isfinite(sigma2) or sigma2 <= 1e-12:
        sigma2 = 1e-8
    k = int(means.size)
    if k == 0:
        return (float("nan"), float("nan"), sigma2)
    if k == 1:
        return (float(means[0]), sigma2, sigma2)
    weights = ns / sigma2
    mu = float(np.sum(weights * means) / np.sum(weights))
    q_stat = float(np.sum(weights * (means - mu) ** 2))
    c_term = float(np.sum(weights) - np.sum(weights**2) / np.sum(weights))
    if c_term <= 0:
        tau2 = 0.0
    else:
        tau2 = max(0.0, (q_stat - (k - 1)) / c_term)
    precision = 1.0 / (tau2 + sigma2 / ns)
    mu0 = float(np.sum(precision * means) / np.sum(precision))
    return (mu0, float(tau2), sigma2)


def _normal_posterior(
    values: np.ndarray,
    mu0: float,
    tau2: float,
    sigma2: float,
) -> tuple[float, float, float, float]:
    raw = float(np.mean(values))
    n_obs = float(len(values))
    if not np.isfinite(mu0) or n_obs <= 0:
        return (raw, float("nan"), float("nan"), float("nan"))
    sampling_var = sigma2 / n_obs
    if tau2 <= 1e-12:
        shrunk = mu0
        sd = math.sqrt(sampling_var)
    else:
        shrink = sampling_var / (sampling_var + tau2)
        shrunk = (1.0 - shrink) * raw + shrink * mu0
        sd = math.sqrt(1.0 / (n_obs / sigma2 + 1.0 / tau2))
    return (raw, float(shrunk), float(shrunk - Z_95 * sd), float(shrunk + Z_95 * sd))


def _shrink_rates(successes: list[float], trials: list[float]) -> list[tuple[float, float, float]]:
    if not trials:
        return []
    success_arr = np.asarray(successes, dtype=float)
    trial_arr = np.asarray(trials, dtype=float)
    alpha, beta = _beta_prior(success_arr, trial_arr)
    return [
        _beta_posterior(success, trial, alpha, beta)
        for success, trial in zip(success_arr, trial_arr, strict=True)
    ]


def _shrink_means(groups: list[np.ndarray]) -> list[tuple[float, float, float, float]]:
    """Raw mean, shrunk mean, low, high. Empty groups yield NaNs."""
    usable = [values for values in groups if values.size]
    if not usable:
        return [(float("nan"), float("nan"), float("nan"), float("nan"))] * len(groups)
    mu0, tau2, sigma2 = _normal_hyperparameters(usable)
    # When tau2 is 0, recompute the shared-mean standard error from every play.
    if tau2 <= 1e-12 and usable:
        total_n = float(sum(len(values) for values in usable))
        shared_sd = math.sqrt(sigma2 / total_n) if total_n else float("nan")
        results = []
        for values in groups:
            if values.size == 0:
                results.append((float("nan"), float("nan"), float("nan"), float("nan")))
                continue
            raw = float(np.mean(values))
            results.append(
                (raw, float(mu0), float(mu0 - Z_95 * shared_sd), float(mu0 + Z_95 * shared_sd))
            )
        return results
    results = []
    for values in groups:
        if values.size == 0:
            results.append((float("nan"), float("nan"), float("nan"), float("nan")))
            continue
        results.append(_normal_posterior(values, mu0, tau2, sigma2))
    return results


def _player_lookup(players: pd.DataFrame) -> pd.DataFrame:
    columns = ["nfl_id", "display_name", "draft_year"]
    if players.empty:
        return pd.DataFrame(columns=columns)
    work = players.copy()
    if "display_name" not in work.columns:
        work["display_name"] = ""
    if "draft_year" not in work.columns:
        work["draft_year"] = np.nan
    work["nfl_id"] = pd.to_numeric(work["nfl_id"], errors="coerce")
    work = work.dropna(subset=["nfl_id"]).drop_duplicates("nfl_id", keep="first")
    work["nfl_id"] = work["nfl_id"].astype(np.int64)
    work["display_name"] = work["display_name"].astype("string").fillna("")
    return work.loc[:, columns]


def _labeled_assignments(assignments: pd.DataFrame, shell: pd.DataFrame | None) -> pd.DataFrame:
    work = _coerce_ids(assignments, ("game_id", "play_id", "defender_nfl_id"))
    if work.empty:
        work["player_label"] = pd.Series(dtype="string")
        work["team_label"] = pd.Series(dtype="string")
        return work
    if "coverage_assignment" not in work.columns:
        work["coverage_assignment"] = pd.NA
    work["player_label"] = work["coverage_assignment"].map(classify_coverage_assignment)
    if shell is not None and not shell.empty and "team_coverage_man_zone" in shell.columns:
        # The shell table is the source of the team label. Drop a copy that
        # arrived on the assignment rows so the merge does not suffix both.
        if "team_coverage_man_zone" in work.columns:
            work = work.drop(columns=["team_coverage_man_zone"])
        shell_keys = _coerce_ids(shell, ("game_id", "play_id"))
        shell_keys = shell_keys.drop_duplicates(["game_id", "play_id"], keep="first")
        work = work.merge(
            shell_keys.loc[:, ["game_id", "play_id", "team_coverage_man_zone"]],
            on=["game_id", "play_id"],
            how="left",
        )
    elif "team_coverage_man_zone" not in work.columns:
        work["team_coverage_man_zone"] = pd.NA
    work["team_label"] = work["team_coverage_man_zone"].map(classify_coverage_assignment)
    return work


def _completion_flag(frame: pd.DataFrame) -> pd.Series:
    if "is_completion" not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame["is_completion"].fillna(False).astype(bool)


def cb_coverage_table(
    assignments: pd.DataFrame,
    players: pd.DataFrame,
    shell: pd.DataFrame | None = None,
    *,
    min_targets: int = MIN_CB_COVERAGE_TARGETS,
) -> pd.DataFrame:
    """One row per CB and coverage type (man or zone) with a credited target.

    ``assignments`` must already be CB-only. Call ``filter_cornerback_assignments``
    first when the frame still contains other defensive backs.
    """
    if assignments.empty:
        return pd.DataFrame(columns=list(COVERAGE_COLUMNS))
    labeled = _labeled_assignments(assignments, shell)
    labeled = labeled.loc[labeled["player_label"].isin(["man", "zone"])].copy()
    if labeled.empty:
        return pd.DataFrame(columns=list(COVERAGE_COLUMNS))
    labeled["is_completion"] = _completion_flag(labeled)
    if "expected_points_added" in labeled.columns:
        labeled["epa"] = pd.to_numeric(labeled["expected_points_added"], errors="coerce")
    else:
        labeled["epa"] = np.nan
    if "separation_allowed" in labeled.columns:
        labeled["separation"] = pd.to_numeric(labeled["separation_allowed"], errors="coerce")
    else:
        labeled["separation"] = np.nan

    cells: list[tuple[int, str, pd.DataFrame]] = []
    grouped = labeled.groupby(["defender_nfl_id", "player_label"], sort=True)
    for (nfl_id, coverage), group in grouped:
        cells.append((int(nfl_id), str(coverage), group))

    by_coverage: dict[str, list[int]] = {"man": [], "zone": []}
    for index, (_, coverage, _) in enumerate(cells):
        by_coverage[coverage].append(index)

    completion_out: list[tuple[float, float, float] | None] = [None] * len(cells)
    epa_out: list[tuple[float, float, float, float] | None] = [None] * len(cells)
    sep_out: list[tuple[float, float, float, float] | None] = [None] * len(cells)
    for coverage, indexes in by_coverage.items():
        if not indexes:
            continue
        successes = [float(cells[index][2]["is_completion"].sum()) for index in indexes]
        trials = [float(len(cells[index][2])) for index in indexes]
        for index, posterior in zip(indexes, _shrink_rates(successes, trials), strict=True):
            completion_out[index] = posterior
        epa_groups = [
            cells[index][2]["epa"].dropna().to_numpy(dtype=float) for index in indexes
        ]
        sep_groups = [
            cells[index][2]["separation"].dropna().to_numpy(dtype=float) for index in indexes
        ]
        for index, posterior in zip(indexes, _shrink_means(epa_groups), strict=True):
            epa_out[index] = posterior
        for index, posterior in zip(indexes, _shrink_means(sep_groups), strict=True):
            sep_out[index] = posterior

    lookup = _player_lookup(players).set_index("nfl_id")
    rows: list[dict[str, object]] = []
    for index, (nfl_id, coverage, group) in enumerate(cells):
        n_targets = int(len(group))
        n_completions = int(group["is_completion"].sum())
        rate = n_completions / n_targets if n_targets else float("nan")
        shrunk_rate, rate_low, rate_high = completion_out[index] or (float("nan"),) * 3
        epa_raw, epa_shrunk, epa_low, epa_high = epa_out[index] or (float("nan"),) * 4
        sep_raw, sep_shrunk, sep_low, sep_high = sep_out[index] or (float("nan"),) * 4
        name = ""
        draft_year: object = np.nan
        if nfl_id in lookup.index:
            name = str(lookup.at[nfl_id, "display_name"])
            draft_year = lookup.at[nfl_id, "draft_year"]
        rows.append(
            {
                "nfl_id": nfl_id,
                "display_name": name,
                "draft_year": draft_year,
                "coverage": coverage,
                "n_targets": n_targets,
                "n_completions": n_completions,
                "completion_rate": rate,
                "completion_shrunk": shrunk_rate,
                "completion_ci_low": rate_low,
                "completion_ci_high": rate_high,
                "n_epa": int(group["epa"].notna().sum()),
                "mean_epa": epa_raw,
                "epa_shrunk": epa_shrunk,
                "epa_ci_low": epa_low,
                "epa_ci_high": epa_high,
                "n_separation": int(group["separation"].notna().sum()),
                "mean_separation": sep_raw,
                "separation_shrunk": sep_shrunk,
                "separation_ci_low": sep_low,
                "separation_ci_high": sep_high,
                "meets_floor": n_targets >= min_targets,
                "small_n": n_targets < SMALL_N_THRESHOLD,
                "label_source": LABEL_SOURCE,
                "interval_method": INTERVAL_METHOD,
                "exploratory": True,
                "preregistered": False,
            }
        )
    return pd.DataFrame(rows, columns=list(COVERAGE_COLUMNS))


def cb_coverage_audit(
    assignments: pd.DataFrame,
    shell: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Aggregate map from raw assignment strings to man, zone, or other.

    No player identifiers. ``n_agree`` counts targets whose player label and
    team-shell label are the same man or zone value.
    """
    if assignments.empty:
        return pd.DataFrame(columns=list(AUDIT_COLUMNS))
    labeled = _labeled_assignments(assignments, shell)
    if labeled.empty:
        return pd.DataFrame(columns=list(AUDIT_COLUMNS))
    assignment = labeled["coverage_assignment"].astype("string").str.strip().str.upper()
    assignment = assignment.mask(assignment.isin(["<NA>", "NAN", "NONE"]), "MISSING")
    labeled = labeled.assign(coverage_assignment=assignment.fillna("MISSING"))
    player_known = labeled["player_label"].isin(["man", "zone"])
    team_known = labeled["team_label"].isin(["man", "zone"])
    both = player_known & team_known
    agree = both & labeled["player_label"].eq(labeled["team_label"])
    labeled = labeled.assign(_agree=agree, _both=both)
    rows = []
    for name, group in labeled.groupby("coverage_assignment", sort=True):
        label = classify_coverage_assignment(name if name != "MISSING" else None)
        team = group["team_label"]
        rows.append(
            {
                "coverage_assignment": name,
                "player_label": label,
                "n_targets": int(len(group)),
                "n_team_man": int(team.eq("man").sum()),
                "n_team_zone": int(team.eq("zone").sum()),
                "n_team_other": int(team.eq("other").sum()),
                "n_agree": int(group["_agree"].sum()),
            }
        )
    return pd.DataFrame(rows, columns=list(AUDIT_COLUMNS))


def cb_coverage_summary(
    assignments: pd.DataFrame,
    table: pd.DataFrame,
    shell: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """One row documenting the label choice, the floor, and the agreement rate."""
    if assignments.empty:
        labeled = assignments
        n_credited = 0
        n_cbs = 0
    else:
        labeled = _labeled_assignments(assignments, shell)
        n_credited = int(len(labeled))
        n_cbs = int(labeled["defender_nfl_id"].nunique()) if n_credited else 0
    if n_credited:
        labels = labeled["player_label"]
        both = labels.isin(["man", "zone"]) & labeled["team_label"].isin(["man", "zone"])
        n_agree = int((both & labels.eq(labeled["team_label"])).sum())
        n_both = int(both.sum())
        n_man = int(labels.eq("man").sum())
        n_zone = int(labels.eq("zone").sum())
        n_other = int(labels.eq("other").sum())
    else:
        n_agree = n_both = n_man = n_zone = n_other = 0
    if table.empty:
        n_in_table = n_man_rows = n_zone_rows = n_man_floor = n_zone_floor = 0
    else:
        n_in_table = int(table["nfl_id"].nunique())
        n_man_rows = int(table["coverage"].eq("man").sum())
        n_zone_rows = int(table["coverage"].eq("zone").sum())
        floor = table["meets_floor"].astype(bool)
        n_man_floor = int((table["coverage"].eq("man") & floor).sum())
        n_zone_floor = int((table["coverage"].eq("zone") & floor).sum())
    agreement = n_agree / n_both if n_both else float("nan")
    row = {
        "label_source": LABEL_SOURCE,
        "alternative_not_used": LABEL_ALTERNATIVE,
        "reason": LABEL_REASON,
        "min_targets_floor": MIN_CB_COVERAGE_TARGETS,
        "small_n_threshold": SMALL_N_THRESHOLD,
        "interval_method": INTERVAL_METHOD,
        "position": "CB",
        "n_cbs_credited": n_cbs,
        "n_cbs_in_table": n_in_table,
        "n_man_rows": n_man_rows,
        "n_zone_rows": n_zone_rows,
        "n_man_meet_floor": n_man_floor,
        "n_zone_meet_floor": n_zone_floor,
        "n_credited_targets": n_credited,
        "n_man_targets": n_man,
        "n_zone_targets": n_zone,
        "n_other_targets": n_other,
        "n_both_labeled": n_both,
        "n_label_agree": n_agree,
        "agreement_rate": agreement,
        "exploratory": True,
        "preregistered": False,
    }
    return pd.DataFrame([row], columns=list(SUMMARY_COLUMNS))
