"""Exploratory probability that a credited CB matchup ends in a completion.

Not part of the pre-registered family. The DB-group tests are unchanged.

Threat
------
A matchup is a threat when the targeted receiver's ``pass_result`` is ``C``
on a target the coverage rule already credited to that CB. Completion is the
event the rep is asked to prevent, and it is observed after the throw.

Positive EPA was not used. It mixes yards after the catch and game state the
CB does not control. A separation threshold at the catch was not used either.
Separation at the catch is measured after the throw, and it restates the same
geometry the kinematic features are meant to describe.

Features
--------
Kinematics are taken from the CB and the credited receiver at ``pass_forward``,
plus the change in CB speed from about 0.5 seconds before the throw. Combine
traits are wing span, broad jump, and vertical. Height, weight, and arm length
are left out so wing span is not split with arm length.

Leakage
-------
A play with no ``pass_forward`` timestamp is dropped, because the throw time
cannot be established. Frames whose event is a post-outcome name (the catch,
the incompletion, the tackle, and the same family) are dropped. Every other
frame is kept only when its timestamp is at or before ``pass_forward``.

Model
-----
L2-penalized logistic regression with a player intercept per CB. The intercepts
are the MAP of a normal random effect under a flat prior on the slopes. Combine
traits do not vary within a CB, so an unpenalized intercept per CB would
swallow them. The penalty is chosen by grouped cross-validation that scores
held-out CBs with their intercept set to zero. That score keeps trait
coefficients that predict a CB the fit did not see.

Slopes are on the log-odds scale per 1 SD of the estimation sample. Intervals
are percentile intervals from a cluster bootstrap that resamples CBs and refits
at the penalty chosen on the original sample. Calibration is the grouped
cross-validation, not the in-sample fit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from bdb2027.combine_features import heading_delta_deg

THREAT_DEFINITION: str = "completion"
THREAT_RULE: str = (
    "A credited CB matchup is a threat when pass_result on the targeted "
    "receiver is C. Positive EPA was set aside because it mixes yards after "
    "the catch. A separation cutoff at the catch was set aside because that "
    "frame is after the throw and restates the tracking geometry."
)
LEAKAGE_RULE: str = (
    "Plays without a pass_forward timestamp are dropped. Post-outcome event "
    "names are dropped. Other frames are kept only at or before pass_forward. "
    "The throw state is the pass_forward sample, or the closest CB and receiver "
    "sample within 0.15 s before it. CB speed change uses a frame about 0.5 s earlier."
)
MODEL_NAME: str = "l2_logistic_player_intercept"

LOOKBACK_S: float = 0.5
MAX_LOOKBACK_GAP_S: float = 1.0
THROW_TOLERANCE_S: float = 0.15
LAMBDA_GRID: tuple[float, ...] = (0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
DEFAULT_LAMBDA: float = 4.0
MIN_MATCHUPS: int = 8
MIN_CBS_FOR_CV: int = 4
SLOPE_RIDGE: float = 1e-4
BOOTSTRAP_DRAWS: int = 200
BOOTSTRAP_SEED: int = 2027
PROBABILITY_CLIP: float = 1e-6

KINEMATIC_FEATURES: tuple[str, ...] = (
    "separation_at_throw",
    "closing_speed",
    "hip_error_deg",
    "motion_error_deg",
    "cb_speed",
    "cb_accel",
    "cb_speed_change",
)
TRAIT_FEATURES: tuple[str, ...] = ("wing_span", "broad_jump", "vertical")
THREAT_FEATURES: tuple[str, ...] = KINEMATIC_FEATURES + TRAIT_FEATURES

POST_THROW_EVENTS: frozenset[str] = frozenset(
    {
        "pass_arrived",
        "pass_tipped",
        "dropped_pass",
        "interception",
        "tackle",
        "touchdown",
        "out_of_bounds",
        "fumble",
        "fumble_defense_recovered",
        "fumble_offense_recovered",
        "qb_sack",
        "qb_strip_sack",
        "safety",
        "touchback",
    }
)

EFFECT_COLUMNS: tuple[str, ...] = (
    "term",
    "coef",
    "odds_ratio",
    "ci_low",
    "ci_high",
    "or_ci_low",
    "or_ci_high",
    "mean_risk_difference",
    "risk_ci_low",
    "risk_ci_high",
    "feature_mean",
    "feature_sd",
    "lambda",
    "n_matchups",
    "n_cbs",
    "threat_definition",
    "model",
    "exploratory",
    "preregistered",
)

CALIBRATION_COLUMNS: tuple[str, ...] = (
    "bin",
    "n",
    "mean_predicted",
    "observed_rate",
)

METRIC_COLUMNS: tuple[str, ...] = (
    "threat_definition",
    "threat_rule",
    "leakage_rule",
    "model",
    "lambda",
    "cv_status",
    "n_assignments",
    "n_with_kinematics",
    "n_matchups",
    "n_cbs",
    "n_threats",
    "threat_rate",
    "n_dropped_incomplete",
    "dropped_features",
    "brier_grouped_cv",
    "brier_baseline_grouped_cv",
    "log_loss_grouped_cv",
    "log_loss_baseline_grouped_cv",
    "ece_grouped_cv",
    "n_cv_predictions",
    "player_intercept_sd",
    "n_bootstrap",
    "bootstrap_seed",
    "exploratory",
    "preregistered",
)


def is_post_outcome_event(value: object) -> bool:
    """True for event names that record the result of the throw."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    text = str(value).strip().lower()
    if not text or text in {"nan", "<na>", "none", "nat"}:
        return False
    if text.startswith("pass_outcome"):
        return True
    return text in POST_THROW_EVENTS


def _epoch_seconds(parsed: pd.Series) -> np.ndarray:
    """Seconds since the Unix epoch. Uses timedelta, not the integer storage unit.

    Pandas 2 stores ``datetime64[ns]`` and pandas 3 stores ``datetime64[us]``.
    Dividing the integer view by 1e9 treats microseconds as nanoseconds, so a
    0.1 s frame gap becomes 0.0001 s and the 0.5 s lookback falls outside the play.
    """
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    return (parsed - epoch).dt.total_seconds().to_numpy(dtype=float)


def frame_seconds(time_values: pd.Series) -> np.ndarray:
    """Seconds since the Unix epoch, for ordering frames inside a play.

    Numeric timestamps are already seconds and are kept. Datetime values,
    including a ``datetime64[us]`` column, are converted with
    ``Series.dt.total_seconds``.
    """
    if time_values.empty:
        return np.asarray([], dtype=float)
    if pd.api.types.is_datetime64_any_dtype(time_values):
        parsed = pd.to_datetime(time_values, utc=True, errors="coerce")
        return _epoch_seconds(parsed)
    numeric = pd.to_numeric(time_values, errors="coerce")
    if float(numeric.notna().mean()) >= 0.8:
        return numeric.to_numpy(dtype=float)
    parsed = pd.to_datetime(time_values, utc=True, errors="coerce")
    if parsed.notna().any():
        return _epoch_seconds(parsed)
    return np.full(len(time_values), np.nan)


def _velocity(speed: float, direction_deg: float) -> tuple[float, float]:
    """NGS direction: 0 degrees is +y, 90 degrees is +x."""
    radians = math.radians(direction_deg)
    return (speed * math.sin(radians), speed * math.cos(radians))


def closing_speed(
    cb_speed: float,
    cb_dir: float,
    receiver_speed: float,
    receiver_dir: float,
    dx: float,
    dy: float,
) -> float:
    """Positive when the CB-receiver gap is shrinking.

    ``dx`` and ``dy`` point from the CB to the receiver.
    """
    distance = math.hypot(dx, dy)
    if distance < 1e-6:
        return float("nan")
    cb_vx, cb_vy = _velocity(cb_speed, cb_dir)
    rec_vx, rec_vy = _velocity(receiver_speed, receiver_dir)
    return ((cb_vx - rec_vx) * dx + (cb_vy - rec_vy) * dy) / distance


def _near_throw(player_frames: pd.DataFrame, t_throw: float) -> pd.Series | None:
    if player_frames.empty:
        return None
    delta = (player_frames["t"] - t_throw).abs()
    close = player_frames.loc[delta <= THROW_TOLERANCE_S + 1e-9]
    if close.empty:
        return None
    event = close["event"].astype("string").str.strip().str.lower()
    tagged = close.loc[event.eq("pass_forward")]
    use = tagged if not tagged.empty else close
    distance = (use["t"] - t_throw).abs()
    return use.loc[distance.idxmin()]


def _speed_change(cb_frames: pd.DataFrame, t_throw: float, speed_at_throw: float) -> float:
    target = t_throw - LOOKBACK_S
    earlier = cb_frames.loc[cb_frames["t"] <= target + 1e-9]
    if earlier.empty:
        return float("nan")
    row = earlier.loc[earlier["t"].idxmax()]
    if t_throw - float(row["t"]) > MAX_LOOKBACK_GAP_S + 1e-9:
        return float("nan")
    previous = float(row["s"])
    if not np.isfinite(previous) or not np.isfinite(speed_at_throw):
        return float("nan")
    return speed_at_throw - previous


def matchup_features(
    frames: pd.DataFrame,
    defender_id: int,
    receiver_id: int,
) -> dict[str, float] | None:
    """Kinematic features for one credited matchup, or None when the throw is unusable.

    Post-outcome event names are dropped. Frames after ``pass_forward`` are
    ignored. ``time`` is converted to seconds when ``t`` is not already present.
    """
    if frames.empty or "event" not in frames.columns:
        return None
    frames = frames.loc[~frames["event"].map(is_post_outcome_event).fillna(False)].copy()
    if frames.empty:
        return None
    if "t" not in frames.columns:
        if "time" not in frames.columns:
            return None
        frames["t"] = frame_seconds(frames["time"])
    frames["nfl_id"] = pd.to_numeric(frames["nfl_id"], errors="coerce")
    for column in ("x", "y", "s", "a", "o", "dir", "t"):
        frames[column] = pd.to_numeric(frames[column], errors="coerce")
    event = frames["event"].astype("string").str.strip().str.lower()
    throw = frames.loc[event.eq("pass_forward") & frames["t"].notna()]
    if throw.empty:
        return None
    t_throw = float(throw["t"].min())
    pre = frames.loc[frames["t"] <= t_throw + 1e-9]
    cb = pre.loc[pre["nfl_id"] == defender_id]
    receiver = pre.loc[pre["nfl_id"] == receiver_id]
    cb_state = _near_throw(cb, t_throw)
    receiver_state = _near_throw(receiver, t_throw)
    if cb_state is None or receiver_state is None:
        return None
    cx = float(cb_state["x"])
    cy = float(cb_state["y"])
    rx = float(receiver_state["x"])
    ry = float(receiver_state["y"])
    if not all(math.isfinite(value) for value in (cx, cy, rx, ry)):
        return None
    dx = rx - cx
    dy = ry - cy
    separation = float(math.hypot(dx, dy))
    if separation < 1e-6:
        return None
    bearing = float(np.rad2deg(np.arctan2(dx, dy)) % 360.0)
    needed = {
        "cb_speed": float(cb_state["s"]),
        "cb_accel": float(cb_state["a"]),
        "cb_dir": float(cb_state["dir"]),
        "cb_o": float(cb_state["o"]),
        "rec_speed": float(receiver_state["s"]),
        "rec_dir": float(receiver_state["dir"]),
    }
    if not all(math.isfinite(value) for value in needed.values()):
        return None
    speed_change = _speed_change(cb, t_throw, needed["cb_speed"])
    if not math.isfinite(speed_change):
        return None
    hip = float(heading_delta_deg(np.array([needed["cb_o"]]), bearing)[0])
    motion = float(heading_delta_deg(np.array([needed["cb_dir"]]), bearing)[0])
    gap_rate = closing_speed(
        needed["cb_speed"],
        needed["cb_dir"],
        needed["rec_speed"],
        needed["rec_dir"],
        dx,
        dy,
    )
    return {
        "separation_at_throw": separation,
        "closing_speed": gap_rate,
        "hip_error_deg": hip,
        "motion_error_deg": motion,
        "cb_speed": needed["cb_speed"],
        "cb_accel": needed["cb_accel"],
        "cb_speed_change": speed_change,
    }


def _prepare_tracking(tracking: pd.DataFrame) -> dict[tuple[int, int], pd.DataFrame]:
    if tracking.empty:
        return {}
    work = tracking.copy()
    if "event" not in work.columns:
        work["event"] = ""
    for column in ("x", "y", "s", "a", "o", "dir"):
        if column not in work.columns:
            work[column] = np.nan
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work["game_id"] = pd.to_numeric(work["game_id"], errors="coerce")
    work["play_id"] = pd.to_numeric(work["play_id"], errors="coerce")
    work["nfl_id"] = pd.to_numeric(work["nfl_id"], errors="coerce")
    work["t"] = frame_seconds(work["time"]) if "time" in work.columns else np.nan
    work = work.dropna(subset=["game_id", "play_id", "nfl_id", "t"])
    if work.empty:
        return {}
    keep = ~work["event"].map(is_post_outcome_event)
    work = work.loc[keep.fillna(False)]
    work["game_id"] = work["game_id"].astype(np.int64)
    work["play_id"] = work["play_id"].astype(np.int64)
    work["nfl_id"] = work["nfl_id"].astype(np.int64)
    grouped: dict[tuple[int, int], pd.DataFrame] = {}
    for (game_id, play_id), group in work.groupby(["game_id", "play_id"], sort=False):
        grouped[(int(game_id), int(play_id))] = group.sort_values("t", kind="mergesort")
    return grouped


def _trait_table(traits: pd.DataFrame) -> pd.DataFrame:
    columns = ["nfl_id", *TRAIT_FEATURES]
    if traits.empty:
        return pd.DataFrame(columns=columns)
    work = traits.copy()
    work["nfl_id"] = pd.to_numeric(work["nfl_id"], errors="coerce")
    for column in TRAIT_FEATURES:
        if column not in work.columns:
            work[column] = np.nan
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=["nfl_id"]).drop_duplicates("nfl_id", keep="first")
    work["nfl_id"] = work["nfl_id"].astype(np.int64)
    return work.loc[:, columns]


def build_matchups(
    tracking: pd.DataFrame,
    assignments: pd.DataFrame,
    traits: pd.DataFrame,
) -> pd.DataFrame:
    """One row per credited CB target with kinematics and Combine traits.

    Rows that fail the leakage rules or lack a throw sample are omitted.
    Trait gaps are left as missing so the model can count them.
    """
    base_columns = [
        "game_id",
        "play_id",
        "defender_nfl_id",
        "threat",
        *THREAT_FEATURES,
    ]
    if assignments.empty:
        return pd.DataFrame(columns=base_columns)
    grouped = _prepare_tracking(tracking)
    trait_rows = _trait_table(traits).set_index("nfl_id")
    records: list[dict[str, object]] = []
    work = assignments.copy()
    work["game_id"] = pd.to_numeric(work["game_id"], errors="coerce")
    work["play_id"] = pd.to_numeric(work["play_id"], errors="coerce")
    work["defender_nfl_id"] = pd.to_numeric(work["defender_nfl_id"], errors="coerce")
    work["receiver_nfl_id"] = pd.to_numeric(work["receiver_nfl_id"], errors="coerce")
    work = work.dropna(subset=["game_id", "play_id", "defender_nfl_id", "receiver_nfl_id"])
    if "is_completion" in work.columns:
        flag = work["is_completion"]
        if flag.dtype == bool:
            work["threat"] = flag.fillna(False).astype(int)
        else:
            text = flag.astype("string").str.strip().str.lower()
            work["threat"] = text.isin(["1", "true", "t", "yes"]).fillna(False).astype(int)
    else:
        work["threat"] = 0
    for row in work.itertuples(index=False):
        key = (int(row.game_id), int(row.play_id))
        frames = grouped.get(key)
        if frames is None:
            continue
        features = matchup_features(frames, int(row.defender_nfl_id), int(row.receiver_nfl_id))
        if features is None:
            continue
        record: dict[str, object] = {
            "game_id": key[0],
            "play_id": key[1],
            "defender_nfl_id": int(row.defender_nfl_id),
            "threat": int(row.threat),
        }
        record.update(features)
        defender = int(row.defender_nfl_id)
        if defender in trait_rows.index:
            for column in TRAIT_FEATURES:
                record[column] = float(trait_rows.at[defender, column])
        else:
            for column in TRAIT_FEATURES:
                record[column] = float("nan")
        records.append(record)
    if not records:
        return pd.DataFrame(columns=base_columns)
    return pd.DataFrame(records, columns=base_columns)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _log_loss(y: np.ndarray, probability: np.ndarray) -> float:
    p = np.clip(probability, PROBABILITY_CLIP, 1.0 - PROBABILITY_CLIP)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def _brier(y: np.ndarray, probability: np.ndarray) -> float:
    return float(np.mean((probability - y) ** 2))


@dataclass
class LogisticFit:
    beta: np.ndarray
    player_ids: np.ndarray
    player_effects: np.ndarray
    converged: bool

    def predict(self, features: np.ndarray, player_ids: np.ndarray | None = None) -> np.ndarray:
        linear = self.beta[0] + features @ self.beta[1:]
        if player_ids is None or self.player_ids.size == 0:
            return _sigmoid(linear)
        lookup = dict(zip(self.player_ids.tolist(), self.player_effects.tolist(), strict=True))
        effects = np.array([lookup.get(int(player), 0.0) for player in player_ids], dtype=float)
        return _sigmoid(linear + effects)


def fit_logistic(
    features: np.ndarray,
    y: np.ndarray,
    player_ids: np.ndarray | None = None,
    lam: float = DEFAULT_LAMBDA,
    *,
    max_iter: int = 30,
) -> LogisticFit:
    """Penalized logistic regression. ``features`` has no intercept column.

    ``player_ids`` None fits a population logistic regression. Otherwise each
    distinct id gets an intercept penalized by ``lam``.
    """
    features = np.asarray(features, dtype=float)
    y = np.asarray(y, dtype=float)
    n_rows, n_slopes = features.shape
    design = np.column_stack([np.ones(n_rows), features])
    if player_ids is None:
        codes = np.zeros(n_rows, dtype=int)
        unique_ids = np.asarray([], dtype=int)
        n_players = 0
    else:
        unique_ids, codes = np.unique(np.asarray(player_ids), return_inverse=True)
        codes = codes.astype(int)
        n_players = int(unique_ids.size)
    n_beta = n_slopes + 1
    theta = np.zeros(n_beta + n_players)
    penalty = np.zeros(theta.size)
    penalty[1:n_beta] = SLOPE_RIDGE
    if n_players:
        penalty[n_beta:] = lam

    def unpack(vector: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        beta = vector[:n_beta]
        effects = vector[n_beta:]
        eta = design @ beta
        if n_players:
            eta = eta + effects[codes]
        return beta, effects, eta

    def objective(vector: np.ndarray) -> float:
        beta, effects, eta = unpack(vector)
        probability = np.clip(_sigmoid(eta), PROBABILITY_CLIP, 1.0 - PROBABILITY_CLIP)
        log_lik = float(np.sum(y * np.log(probability) + (1.0 - y) * np.log(1.0 - probability)))
        return log_lik - 0.5 * float(np.sum(penalty * vector * vector))

    converged = False
    for _ in range(max_iter):
        beta, effects, eta = unpack(theta)
        probability = _sigmoid(eta)
        weights = np.clip(probability * (1.0 - probability), 1e-6, None)
        residual = y - probability
        gradient = np.zeros_like(theta)
        gradient[:n_beta] = design.T @ residual
        if n_players:
            gradient[n_beta:] = np.bincount(codes, weights=residual, minlength=n_players)
        gradient -= penalty * theta
        hessian = np.zeros((theta.size, theta.size))
        weighted_design = design * weights[:, None]
        hessian[:n_beta, :n_beta] = design.T @ weighted_design
        if n_players:
            # Cross term: column j sums w_i x_i over rows of player j.
            cross = np.zeros((n_beta, n_players))
            for player in range(n_players):
                mask = codes == player
                cross[:, player] = weighted_design[mask].sum(axis=0)
            hessian[:n_beta, n_beta:] = cross
            hessian[n_beta:, :n_beta] = cross.T
            player_weight = np.bincount(codes, weights=weights, minlength=n_players)
            hessian[n_beta:, n_beta:] = np.diag(player_weight)
        hessian.flat[:: hessian.shape[0] + 1] += penalty
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            hessian.flat[:: hessian.shape[0] + 1] += 1e-6
            try:
                step = np.linalg.solve(hessian, gradient)
            except np.linalg.LinAlgError:
                break
        if not np.all(np.isfinite(step)):
            break
        current = objective(theta)
        accepted = theta
        improved = False
        for shrink in (1.0, 0.5, 0.25, 0.125):
            candidate = theta + shrink * step
            if not np.all(np.isfinite(candidate)):
                continue
            if objective(candidate) >= current - 1e-10:
                accepted = candidate
                improved = True
                break
        if not improved:
            converged = bool(float(np.max(np.abs(gradient))) < 1e-3)
            break
        delta = accepted - theta
        theta = accepted
        if float(np.max(np.abs(gradient))) < 1e-6 or float(np.max(np.abs(delta))) < 1e-6:
            converged = True
            break
    beta, effects, _ = unpack(theta)
    if not np.all(np.isfinite(beta)):
        converged = False
    return LogisticFit(
        beta=beta,
        player_ids=unique_ids.astype(int),
        player_effects=effects if n_players else np.asarray([], dtype=float),
        converged=converged,
    )


def _player_folds(player_ids: np.ndarray, *, n_folds: int, seed: int) -> list[np.ndarray]:
    players = np.unique(player_ids)
    rng = np.random.default_rng(seed)
    rng.shuffle(players)
    return [fold for fold in np.array_split(players, n_folds) if len(fold)]


def _grouped_predictions(
    features: np.ndarray,
    y: np.ndarray,
    player_ids: np.ndarray,
    lam: float,
    *,
    seed: int,
) -> dict[str, np.ndarray | float]:
    """Held-out predictions. Held-out CBs are scored with a zero player effect."""
    folds = _player_folds(player_ids, n_folds=min(5, len(np.unique(player_ids))), seed=seed)
    predicted = np.full(len(y), np.nan)
    baseline = np.full(len(y), np.nan)
    for fold in folds:
        hold = np.isin(player_ids, fold)
        train = ~hold
        if hold.sum() == 0 or train.sum() < MIN_MATCHUPS:
            continue
        if np.unique(y[train]).size < 2:
            continue
        fit = fit_logistic(features[train], y[train], player_ids[train], lam)
        if not np.all(np.isfinite(fit.beta)):
            continue
        predicted[hold] = fit.predict(features[hold])
        baseline[hold] = float(np.mean(y[train]))
    scored = np.isfinite(predicted)
    return {
        "predicted": predicted,
        "baseline": baseline,
        "scored": scored,
    }


def _choose_lambda(
    features: np.ndarray,
    y: np.ndarray,
    player_ids: np.ndarray,
    *,
    seed: int,
) -> tuple[float, dict[str, np.ndarray | float], str]:
    n_players = int(np.unique(player_ids).size)
    if n_players < MIN_CBS_FOR_CV:
        empty = _grouped_predictions(features, y, player_ids, DEFAULT_LAMBDA, seed=seed)
        return (DEFAULT_LAMBDA, empty, "skipped_small_n")
    best_lambda = DEFAULT_LAMBDA
    best_loss = math.inf
    best_pred: dict[str, np.ndarray | float] | None = None
    for lam in LAMBDA_GRID:
        pred = _grouped_predictions(features, y, player_ids, lam, seed=seed)
        scored = np.asarray(pred["scored"], dtype=bool)
        if not scored.any():
            continue
        loss = _log_loss(y[scored], np.asarray(pred["predicted"])[scored])
        if loss < best_loss:
            best_loss = loss
            best_lambda = float(lam)
            best_pred = pred
    if best_pred is None:
        best_pred = _grouped_predictions(features, y, player_ids, DEFAULT_LAMBDA, seed=seed)
        return (DEFAULT_LAMBDA, best_pred, "skipped_small_n")
    return (best_lambda, best_pred, "grouped_player")


def _reliability(y: np.ndarray, probability: np.ndarray) -> pd.DataFrame:
    if y.size == 0:
        return pd.DataFrame(columns=list(CALIBRATION_COLUMNS))
    n_bins = 10 if y.size >= 50 else 4
    n_bins = min(n_bins, y.size)
    order = np.argsort(probability, kind="mergesort")
    chunks = np.array_split(order, n_bins)
    rows = []
    for index, chunk in enumerate(chunks, start=1):
        if chunk.size == 0:
            continue
        rows.append(
            {
                "bin": index,
                "n": int(chunk.size),
                "mean_predicted": float(np.mean(probability[chunk])),
                "observed_rate": float(np.mean(y[chunk])),
            }
        )
    return pd.DataFrame(rows, columns=list(CALIBRATION_COLUMNS))


def _risk_difference(features: np.ndarray, beta: np.ndarray, term_index: int) -> float:
    """Mean change in probability when standardized feature ``term_index`` rises by 1."""
    base = _sigmoid(beta[0] + features @ beta[1:])
    bumped = features.copy()
    bumped[:, term_index] += 1.0
    alternate = _sigmoid(beta[0] + bumped @ beta[1:])
    return float(np.mean(alternate - base))


def _empty_model(
    n_assignments: int,
    n_with_kinematics: int,
    n_dropped: int,
) -> dict[str, pd.DataFrame]:
    metrics = {
        "threat_definition": THREAT_DEFINITION,
        "threat_rule": THREAT_RULE,
        "leakage_rule": LEAKAGE_RULE,
        "model": MODEL_NAME,
        "lambda": np.nan,
        "cv_status": "not_fit",
        "n_assignments": n_assignments,
        "n_with_kinematics": n_with_kinematics,
        "n_matchups": 0,
        "n_cbs": 0,
        "n_threats": 0,
        "threat_rate": np.nan,
        "n_dropped_incomplete": n_dropped,
        "dropped_features": "",
        "brier_grouped_cv": np.nan,
        "brier_baseline_grouped_cv": np.nan,
        "log_loss_grouped_cv": np.nan,
        "log_loss_baseline_grouped_cv": np.nan,
        "ece_grouped_cv": np.nan,
        "n_cv_predictions": 0,
        "player_intercept_sd": np.nan,
        "n_bootstrap": 0,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "exploratory": True,
        "preregistered": False,
    }
    return {
        "effects": pd.DataFrame(columns=list(EFFECT_COLUMNS)),
        "calibration": pd.DataFrame(columns=list(CALIBRATION_COLUMNS)),
        "metrics": pd.DataFrame([metrics], columns=list(METRIC_COLUMNS)),
    }


def _scale(features: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    means = features.mean(axis=0)
    sds = features.std(axis=0, ddof=0)
    keep = sds > 1e-8
    kept = features[:, keep]
    kept_sd = sds[keep]
    scaled = (kept - means[keep]) / kept_sd
    return scaled, means, sds, keep


def _bootstrap_betas(
    features: np.ndarray,
    y: np.ndarray,
    player_ids: np.ndarray,
    lam: float,
    *,
    draws: int,
    seed: int,
) -> np.ndarray:
    if draws <= 0:
        return np.zeros((0, features.shape[1] + 1))
    rng = np.random.default_rng(seed)
    players = np.unique(player_ids)
    betas = []
    for _ in range(draws):
        drawn = rng.choice(players, size=players.size, replace=True)
        parts_x = []
        parts_y = []
        parts_id = []
        for new_id, player in enumerate(drawn):
            mask = player_ids == player
            parts_x.append(features[mask])
            parts_y.append(y[mask])
            parts_id.append(np.full(int(mask.sum()), new_id, dtype=int))
        y_boot = np.concatenate(parts_y)
        if np.unique(y_boot).size < 2:
            continue
        fit = fit_logistic(np.vstack(parts_x), y_boot, np.concatenate(parts_id), lam)
        if fit.converged and np.all(np.isfinite(fit.beta)):
            betas.append(fit.beta)
    if not betas:
        return np.zeros((0, features.shape[1] + 1))
    return np.vstack(betas)


def fit_threat_model(
    matchups: pd.DataFrame,
    *,
    n_assignments: int | None = None,
    n_bootstrap: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, pd.DataFrame]:
    """Fit the exploratory threat model on a matchup table from ``build_matchups``."""
    n_with = int(len(matchups))
    if n_assignments is None:
        n_assignments = n_with
    if matchups.empty:
        return _empty_model(n_assignments, n_with, 0)
    work = matchups.copy()
    work["threat"] = pd.to_numeric(work["threat"], errors="coerce")
    for column in THREAT_FEATURES:
        if column not in work.columns:
            work[column] = np.nan
        work[column] = pd.to_numeric(work[column], errors="coerce")
    complete = work.dropna(subset=["threat", "defender_nfl_id", *THREAT_FEATURES])
    n_dropped = n_with - int(len(complete))
    y_all = complete["threat"].to_numpy(dtype=float) if not complete.empty else np.asarray([])
    n_cbs = int(complete["defender_nfl_id"].nunique()) if not complete.empty else 0
    too_small = (
        complete.empty
        or len(complete) < MIN_MATCHUPS
        or n_cbs < 2
        or np.unique(y_all).size < 2
    )
    if too_small:
        return _empty_model(n_assignments, n_with, n_dropped)

    raw = complete.loc[:, list(THREAT_FEATURES)].to_numpy(dtype=float)
    scaled, means, sds, keep = _scale(raw)
    kept_names = [name for name, flag in zip(THREAT_FEATURES, keep, strict=True) if flag]
    dropped_names = [name for name, flag in zip(THREAT_FEATURES, keep, strict=True) if not flag]
    if not kept_names:
        return _empty_model(n_assignments, n_with, n_dropped)
    y = complete["threat"].to_numpy(dtype=float)
    player_ids = complete["defender_nfl_id"].to_numpy(dtype=int)
    lam, cv_pred, cv_status = _choose_lambda(scaled, y, player_ids, seed=seed)
    # Fewer than two players is already rejected. One shared intercept still
    # needs a penalty when several CBs are present.
    use_players = n_cbs >= 2
    fit = fit_logistic(scaled, y, player_ids if use_players else None, lam)
    boot = _bootstrap_betas(
        scaled,
        y,
        player_ids,
        lam,
        draws=n_bootstrap,
        seed=seed,
    )
    scored = np.asarray(cv_pred["scored"], dtype=bool)
    predicted = np.asarray(cv_pred["predicted"], dtype=float)
    baseline = np.asarray(cv_pred["baseline"], dtype=float)
    if scored.any():
        brier = _brier(y[scored], predicted[scored])
        brier_base = _brier(y[scored], baseline[scored])
        loss = _log_loss(y[scored], predicted[scored])
        loss_base = _log_loss(y[scored], baseline[scored])
        calibration = _reliability(y[scored], predicted[scored])
        gaps = (calibration["mean_predicted"] - calibration["observed_rate"]).abs()
        ece = float(np.sum(calibration["n"] * gaps) / calibration["n"].sum())
        n_cv = int(scored.sum())
    else:
        brier = brier_base = loss = loss_base = ece = float("nan")
        calibration = pd.DataFrame(columns=list(CALIBRATION_COLUMNS))
        n_cv = 0

    terms = ["intercept", *kept_names]
    rows = []
    for index, term in enumerate(terms):
        coef = float(fit.beta[index]) if index < fit.beta.size else float("nan")
        if boot.shape[0] >= 20 and index < boot.shape[1]:
            low = float(np.quantile(boot[:, index], 0.025))
            high = float(np.quantile(boot[:, index], 0.975))
        else:
            low = high = float("nan")
        if term == "intercept":
            risk = risk_low = risk_high = float("nan")
            feature_mean = feature_sd = float("nan")
        else:
            feature_index = index - 1
            risk = _risk_difference(scaled, fit.beta, feature_index)
            if boot.shape[0] >= 20:
                risks = np.array([_risk_difference(scaled, beta, feature_index) for beta in boot])
                risk_low = float(np.quantile(risks, 0.025))
                risk_high = float(np.quantile(risks, 0.975))
            else:
                risk_low = risk_high = float("nan")
            raw_index = THREAT_FEATURES.index(term)
            feature_mean = float(means[raw_index])
            feature_sd = float(sds[raw_index])
        rows.append(
            {
                "term": term,
                "coef": coef,
                "odds_ratio": float(np.exp(coef)) if np.isfinite(coef) else np.nan,
                "ci_low": low,
                "ci_high": high,
                "or_ci_low": float(np.exp(low)) if np.isfinite(low) else np.nan,
                "or_ci_high": float(np.exp(high)) if np.isfinite(high) else np.nan,
                "mean_risk_difference": risk,
                "risk_ci_low": risk_low,
                "risk_ci_high": risk_high,
                "feature_mean": feature_mean,
                "feature_sd": feature_sd,
                "lambda": lam,
                "n_matchups": int(len(complete)),
                "n_cbs": n_cbs,
                "threat_definition": THREAT_DEFINITION,
                "model": MODEL_NAME,
                "exploratory": True,
                "preregistered": False,
            }
        )
    player_sd = float(np.std(fit.player_effects, ddof=0)) if fit.player_effects.size else 0.0
    metrics = {
        "threat_definition": THREAT_DEFINITION,
        "threat_rule": THREAT_RULE,
        "leakage_rule": LEAKAGE_RULE,
        "model": MODEL_NAME,
        "lambda": lam,
        "cv_status": cv_status,
        "n_assignments": int(n_assignments),
        "n_with_kinematics": n_with,
        "n_matchups": int(len(complete)),
        "n_cbs": n_cbs,
        "n_threats": int(y.sum()),
        "threat_rate": float(np.mean(y)),
        "n_dropped_incomplete": int(n_dropped),
        "dropped_features": ",".join(dropped_names),
        "brier_grouped_cv": brier,
        "brier_baseline_grouped_cv": brier_base,
        "log_loss_grouped_cv": loss,
        "log_loss_baseline_grouped_cv": loss_base,
        "ece_grouped_cv": ece,
        "n_cv_predictions": n_cv,
        "player_intercept_sd": player_sd,
        "n_bootstrap": int(boot.shape[0]),
        "bootstrap_seed": seed,
        "exploratory": True,
        "preregistered": False,
    }
    return {
        "effects": pd.DataFrame(rows, columns=list(EFFECT_COLUMNS)),
        "calibration": calibration,
        "metrics": pd.DataFrame([metrics], columns=list(METRIC_COLUMNS)),
    }
