"""Exploratory CB man/zone table and threat model, on synthetic rows only."""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from bdb2027.cb_coverage import (  # noqa: E402
    MIN_CB_COVERAGE_TARGETS,
    cb_coverage_audit,
    cb_coverage_summary,
    cb_coverage_table,
    classify_coverage_assignment,
    filter_cornerback_assignments,
)
from bdb2027.figures import figure_cb_coverage, figure_threat_effects  # noqa: E402
from bdb2027.threat import (  # noqa: E402
    build_matchups,
    closing_speed,
    fit_logistic,
    fit_threat_model,
    frame_seconds,
    is_post_outcome_event,
    matchup_features,
)

PLAYERS = pd.DataFrame(
    {
        "nfl_id": [7, 8, 9],
        "display_name": ["Man Zone", "Safety", "Other"],
        "draft_year": [2023, 2023, 2024],
        "nfl_position": ["CB", "SS", "CB"],
    }
)


def test_assignment_labels_keep_ambiguous_strings_out() -> None:
    assert classify_coverage_assignment("MAN") == "man"
    assert classify_coverage_assignment(" man ") == "man"
    assert classify_coverage_assignment("MAN_MATCH") == "man"
    assert classify_coverage_assignment("2_MAN") == "man"
    assert classify_coverage_assignment("ZONE") == "zone"
    assert classify_coverage_assignment("DEEP_FREE") == "zone"
    assert classify_coverage_assignment("CURL_FLAT_LEFT") == "zone"
    assert classify_coverage_assignment("MAN_ZONE") == "other"
    assert classify_coverage_assignment("NO_ASSIGNMENT") == "other"
    assert classify_coverage_assignment("COVER_3") == "other"
    assert classify_coverage_assignment(None) == "other"
    assert classify_coverage_assignment(float("nan")) == "other"
    assert is_post_outcome_event("pass_outcome_caught")
    assert is_post_outcome_event("pass_arrived")
    assert not is_post_outcome_event("pass_forward")
    assert not is_post_outcome_event("ball_snap")
    assert not is_post_outcome_event(None)


def _credited_targets() -> pd.DataFrame:
    rows = []
    # Two CBs in man, so the man prior has someone to shrink toward.
    man_epa_7 = (1.0, 1.2, 0.8, 1.1, 0.9, 1.0)
    for play, epa in enumerate(man_epa_7):
        rows.append(_target(play, 7, "MAN", True, epa, 1.0 + 0.1 * play, "ZONE"))
    man_epa_9 = (-1.0, -0.8, -1.2, -0.9, -1.1, -1.0)
    for play, epa in enumerate(man_epa_9):
        rows.append(_target(100 + play, 9, "MAN", False, epa, 3.0, "MAN"))
    rows.append(_target(6, 7, "ZONE", False, -0.4, 4.0, "ZONE"))
    rows.append(_target(7, 7, "DEEP_FREE", False, -0.2, 3.5, "ZONE"))
    for play in range(5):
        rows.append(_target(10 + play, 9, "ZONE", False, -0.5, 3.0, "MAN"))
    rows.append(_target(20, 9, "MAN_ZONE", True, 2.0, 6.0, "MAN"))
    # Safety: must not appear even with a man assignment.
    rows.append(_target(30, 8, "MAN", True, 3.0, 1.0, "MAN"))
    return pd.DataFrame(rows)


def _target(
    play_id: int,
    defender: int,
    assignment: str,
    complete: bool,
    epa: float,
    separation: float,
    shell: str,
) -> dict[str, object]:
    return {
        "game_id": 1,
        "play_id": play_id,
        "receiver_nfl_id": 100,
        "defender_nfl_id": defender,
        "coverage_assignment": assignment,
        "is_completion": complete,
        "expected_points_added": epa,
        "separation_allowed": separation,
        "team_coverage_man_zone": shell,
    }


def test_cb_table_shrinks_and_drops_safeties() -> None:
    raw = _credited_targets()
    shell = raw.loc[:, ["game_id", "play_id", "team_coverage_man_zone"]]
    kept = filter_cornerback_assignments(raw, PLAYERS)
    assert set(kept["defender_nfl_id"]) == {7, 9}
    table = cb_coverage_table(kept, PLAYERS, shell).set_index(["nfl_id", "coverage"])
    assert (7, "man") in table.index
    assert (7, "zone") in table.index
    assert (9, "zone") in table.index
    assert (9, "man") in table.index
    assert (8, "man") not in table.index

    man = table.loc[(7, "man")]
    assert man["n_targets"] == 6
    assert man["meets_floor"] == (6 >= MIN_CB_COVERAGE_TARGETS)
    assert man["small_n"]
    assert man["completion_rate"] == 1
    assert 0.5 < man["completion_shrunk"] < 1
    assert 0 <= man["completion_ci_low"] <= man["completion_shrunk"]
    assert man["completion_shrunk"] <= man["completion_ci_high"] <= 1
    assert man["mean_epa"] == pytest.approx(1.0)
    # Partial pooling pulls the high-EPA corner toward the other man corner.
    assert 0 < man["epa_shrunk"] < man["mean_epa"]
    assert man["epa_ci_low"] < man["epa_shrunk"] < man["epa_ci_high"]
    assert man["epa_pooling"] == "partial"
    assert man["mean_epa"] != man["epa_shrunk"]
    assert man["exploratory"]
    assert not man["preregistered"]
    assert man["label_source"] == "coverage_assignment"
    assert man["display_name"] == "Man Zone"

    zone = table.loc[(7, "zone")]
    assert zone["n_targets"] == 2
    assert not zone["meets_floor"]

    audit = cb_coverage_audit(kept, shell).set_index("coverage_assignment")
    assert audit.loc["MAN", "player_label"] == "man"
    assert audit.loc["MAN", "n_team_zone"] == 6
    assert audit.loc["MAN", "n_agree"] == 6
    assert audit.loc["MAN_ZONE", "player_label"] == "other"
    summary = cb_coverage_summary(kept, table.reset_index(), shell).iloc[0]
    assert summary["n_other_targets"] == 1
    assert summary["n_cbs_credited"] == 2
    assert summary["alternative_not_used"] == "team_coverage_man_zone"
    assert "coverage_assignment" in summary["reason"]
    assert not summary["preregistered"]


def test_closing_speed_uses_ngs_axes_and_ignores_later_frames() -> None:
    # CB at the origin, facing and running toward +y. Receiver is 10 yards upfield, still.
    assert closing_speed(5.0, 0.0, 0.0, 0.0, 0.0, 10.0) == pytest.approx(5.0)
    assert closing_speed(5.0, 180.0, 0.0, 0.0, 0.0, 10.0) == pytest.approx(-5.0)

    frames = pd.DataFrame(
        [
            _frame(1, 7, 0.0, 0.0, 2.0, "ball_snap", 0.5),
            _frame(1, 100, 0.0, 10.0, 0.0, "ball_snap", 0.5),
            _frame(1, 7, 0.0, 0.0, 5.0, "pass_forward", 1.0),
            _frame(1, 100, 0.0, 10.0, 0.0, "pass_forward", 1.0),
            # After the throw, and a result tagged on the throw timestamp.
            _frame(1, 7, 0.0, 9.0, 99.0, "", 1.4),
            _frame(1, 7, 5.0, 5.0, 40.0, "pass_outcome_caught", 1.0),
            _frame(1, 100, 0.0, 10.0, 0.0, "pass_outcome_caught", 1.2),
        ]
    )
    features = matchup_features(frames, 7, 100)
    assert features is not None
    assert features["cb_speed"] == pytest.approx(5.0)
    assert features["separation_at_throw"] == pytest.approx(10.0)
    assert features["closing_speed"] == pytest.approx(5.0)
    assert features["hip_error_deg"] == pytest.approx(0.0)
    assert features["motion_error_deg"] == pytest.approx(0.0)
    assert features["cb_speed_change"] == pytest.approx(3.0)
    assert features["cb_accel"] == pytest.approx(1.5)

    # No pass_forward timestamp: the throw time is unknown, so the play is unusable.
    untagged = frames.loc[~frames["event"].eq("pass_forward")]
    assert matchup_features(untagged, 7, 100) is None


def test_microsecond_datetimes_keep_a_half_second_lookback() -> None:
    """Pandas 3 stores to_datetime results as datetime64[us].

    The integer view of that dtype is microseconds. Dividing it by 1e9 reads
    the units as nanoseconds, so 0.5 s becomes 0.0005 s and the lookback is
    dropped. This fixture is microseconds on purpose.
    """
    stamps = pd.to_datetime(
        [
            "2024-09-08T17:00:00.000000Z",
            "2024-09-08T17:00:00.500000Z",
            "2024-09-08T17:00:01.000000Z",
        ],
        utc=True,
    ).astype("datetime64[us, UTC]")
    assert str(stamps.dtype).startswith("datetime64[us")
    seconds = frame_seconds(pd.Series(stamps))
    assert seconds[1] - seconds[0] == pytest.approx(0.5)
    assert seconds[2] - seconds[0] == pytest.approx(1.0)
    # The nanosecond misread of a microsecond clock is three orders smaller.
    assert seconds[1] - seconds[0] > 0.1
    numeric = frame_seconds(pd.Series([0.0, 0.5, 1.0]))
    assert numeric[1] == pytest.approx(0.5)
    as_text = pd.Series(
        [
            "2024-09-08T17:00:00.000000Z",
            "2024-09-08T17:00:00.500000Z",
            "2024-09-08T17:00:01.000000Z",
        ]
    )
    text_seconds = frame_seconds(as_text)
    assert text_seconds[1] - text_seconds[0] == pytest.approx(0.5)
    assert str(pd.to_datetime(as_text, utc=True).dtype).startswith("datetime64[us")

    frames = pd.DataFrame(
        [
            _frame(1, 7, 0.0, 0.0, 2.0, "ball_snap", stamps[0]),
            _frame(1, 100, 0.0, 10.0, 0.0, "ball_snap", stamps[0]),
            _frame(1, 7, 0.0, 0.0, 5.0, "pass_forward", stamps[1]),
            _frame(1, 100, 0.0, 10.0, 0.0, "pass_forward", stamps[1]),
        ]
    )
    frames["time"] = pd.Series(
        [stamps[0], stamps[0], stamps[1], stamps[1]],
        dtype="datetime64[us, UTC]",
    )
    assert str(frames["time"].dtype).startswith("datetime64[us")
    matchups = build_matchups(frames, _one_assignment(), pd.DataFrame())
    assert len(matchups) == 1
    assert matchups.iloc[0]["cb_speed"] == pytest.approx(5.0)
    assert matchups.iloc[0]["cb_speed_change"] == pytest.approx(3.0)


def _one_assignment() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": 1,
                "play_id": 1,
                "defender_nfl_id": 7,
                "receiver_nfl_id": 100,
                "is_completion": False,
            }
        ]
    )


def test_zero_between_cb_variance_pools_shrunk_epa() -> None:
    """A 0.05 EPA gap inside unit noise has tau^2 = 0, so shrunk EPA is shared.

    The raw means stay on the row and still differ.
    """
    rows = []
    play = 0
    for defender, low, high, sep_low, sep_high in (
        (7, -1.0, 1.0, 1.0, 2.0),
        (9, -0.95, 1.05, 5.0, 6.0),
    ):
        for _ in range(50):
            for epa, separation in ((low, sep_low), (high, sep_high)):
                rows.append(
                    {
                        "game_id": 1,
                        "play_id": play,
                        "defender_nfl_id": defender,
                        "receiver_nfl_id": 100,
                        "coverage_assignment": "ZONE",
                        "is_completion": False,
                        "expected_points_added": epa,
                        "separation_allowed": separation,
                    }
                )
                play += 1
    table = cb_coverage_table(pd.DataFrame(rows), PLAYERS).set_index("nfl_id")
    assert set(table["epa_pooling"]) == {"complete"}
    assert table["epa_tau2"].eq(0).all()
    assert table["epa_shrunk"].nunique() == 1
    assert table.loc[7, "mean_epa"] == pytest.approx(0.0)
    assert table.loc[9, "mean_epa"] == pytest.approx(0.05)
    assert table.loc[7, "epa_shrunk"] == pytest.approx(0.025)
    assert table.loc[7, "mean_epa"] != pytest.approx(table.loc[7, "epa_shrunk"])
    assert set(table["separation_pooling"]) == {"partial"}
    assert table.loc[7, "separation_shrunk"] < table.loc[9, "separation_shrunk"]
    summary = cb_coverage_summary(pd.DataFrame(rows), table.reset_index()).iloc[0]
    assert summary["n_zone_epa_complete_pool"] == 2
    assert summary["n_zone_separation_complete_pool"] == 0
    assert "mean_epa" in summary["complete_pool_note"]
    assert "tau^2" in summary["complete_pool_note"]


def _frame(
    play_id: int,
    nfl_id: int,
    x: float,
    y: float,
    speed: float,
    event: str,
    time: float,
) -> dict[str, object]:
    return {
        "game_id": 1,
        "play_id": play_id,
        "nfl_id": nfl_id,
        "x": x,
        "y": y,
        "s": speed,
        "a": 1.5,
        "o": 0.0,
        "dir": 0.0,
        "event": event,
        "time": time,
    }


def test_logistic_recovers_a_known_slope() -> None:
    rng = np.random.default_rng(1)
    feature = rng.normal(size=(1600, 1))
    logits = 0.2 + 0.8 * feature[:, 0]
    y = rng.binomial(1, 1.0 / (1.0 + np.exp(-logits)))
    fit = fit_logistic(feature, y, None, lam=1.0)
    assert fit.converged
    assert fit.beta[0] == pytest.approx(0.2, abs=0.2)
    assert fit.beta[1] == pytest.approx(0.8, abs=0.2)


def _signal_matchups() -> pd.DataFrame:
    rng = np.random.default_rng(2027)
    n_players = 8
    n_plays = 36
    player = np.repeat(np.arange(1, n_players + 1), n_plays)
    closing = rng.normal(size=n_players * n_plays)
    wing = np.repeat(rng.normal(size=n_players), n_plays)
    other = rng.normal(size=(n_players * n_plays, 8))
    logits = (
        np.repeat(rng.normal(scale=0.2, size=n_players), n_plays)
        - 1.6 * closing
        + 1.3 * wing
    )
    threat = rng.binomial(1, 1.0 / (1.0 + np.exp(-logits)))
    frame = pd.DataFrame(
        {
            "game_id": 1,
            "play_id": np.arange(n_players * n_plays),
            "defender_nfl_id": player,
            "threat": threat,
            "separation_at_throw": other[:, 0],
            "closing_speed": closing,
            "hip_error_deg": other[:, 1],
            "motion_error_deg": other[:, 2],
            "cb_speed": other[:, 3],
            "cb_accel": other[:, 4],
            "cb_speed_change": other[:, 5],
            "wing_span": wing,
            "broad_jump": other[:, 6],
            "vertical": other[:, 7],
        }
    )
    return frame


def test_threat_model_signs_calibration_and_labels() -> None:
    model = fit_threat_model(_signal_matchups(), n_bootstrap=40, seed=2027)
    effects = model["effects"].set_index("term")
    assert effects.loc["closing_speed", "coef"] < 0
    assert effects.loc["wing_span", "coef"] > 0
    assert effects.loc["closing_speed", "mean_risk_difference"] < 0
    assert effects.loc["closing_speed", "ci_low"] < effects.loc["closing_speed", "ci_high"]
    metrics = model["metrics"].iloc[0]
    assert metrics["threat_definition"] == "completion"
    assert metrics["cv_status"] == "grouped_player"
    assert metrics["brier_grouped_cv"] < metrics["brier_baseline_grouped_cv"]
    assert metrics["exploratory"]
    assert not metrics["preregistered"]
    assert not effects["preregistered"].any()
    calibration = model["calibration"]
    assert calibration["n"].sum() == metrics["n_cv_predictions"]
    assert calibration["observed_rate"].between(0, 1).all()
    assert calibration["mean_predicted"].is_monotonic_increasing
    assert 0 <= metrics["ece_grouped_cv"] <= 1


def test_build_matchups_joins_traits_and_drops_post_throw_frames() -> None:
    frames = pd.DataFrame(
        [
            _frame(1, 7, 0.0, 0.0, 2.0, "ball_snap", 0.5),
            _frame(1, 100, 0.0, 10.0, 0.0, "ball_snap", 0.5),
            _frame(1, 7, 0.0, 0.0, 5.0, "pass_forward", 1.0),
            _frame(1, 100, 0.0, 10.0, 0.0, "pass_forward", 1.0),
            _frame(1, 7, 0.0, 9.0, 99.0, "", 1.5),
        ]
    )
    assignments = pd.DataFrame(
        [
            {
                "game_id": 1,
                "play_id": 1,
                "defender_nfl_id": 7,
                "receiver_nfl_id": 100,
                "is_completion": False,
            }
        ]
    )
    traits = pd.DataFrame(
        {"nfl_id": [7], "wing_span": [78.0], "broad_jump": [120.0], "vertical": [36.0]}
    )
    matchups = build_matchups(frames, assignments, traits)
    assert len(matchups) == 1
    row = matchups.iloc[0]
    assert row["threat"] == 0
    assert row["cb_speed"] == pytest.approx(5.0)
    assert row["wing_span"] == pytest.approx(78.0)
    assert row["closing_speed"] == pytest.approx(5.0)


def test_too_few_matchups_are_labeled_and_not_fit() -> None:
    frame = _signal_matchups().iloc[:4].copy()
    model = fit_threat_model(frame, n_bootstrap=5, seed=1)
    assert model["effects"].empty
    metrics = model["metrics"].iloc[0]
    assert metrics["cv_status"] == "not_fit"
    assert metrics["exploratory"]
    assert not metrics["preregistered"]
    assert math.isnan(metrics["brier_grouped_cv"])


def test_figures_draw_exploratory_titles(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())
    table = cb_coverage_table(
        filter_cornerback_assignments(_credited_targets(), PLAYERS),
        PLAYERS,
        _credited_targets().loc[:, ["game_id", "play_id", "team_coverage_man_zone"]],
    )
    # The six-target man cell clears the floor. Give the zone cell a floor too.
    table.loc[table["coverage"].eq("zone") & table["nfl_id"].eq(7), "meets_floor"] = True
    fig = figure_cb_coverage(table)
    assert "Exploratory" in fig.axes[0].get_title()
    assert "man" in fig.axes[0].get_title()
    empty = figure_cb_coverage(table.iloc[0:0])
    assert "No CB" in empty.axes[0].get_title()
    effects = fit_threat_model(_signal_matchups(), n_bootstrap=0, seed=3)["effects"]
    forest = figure_threat_effects(effects)
    assert "Exploratory" in forest.axes[0].get_title()
    assert "intercept" not in [tick.get_text() for tick in forest.axes[0].get_yticklabels()]
    assert set(tmp_path.iterdir()) == before


def test_cli_writes_cb_tables_and_not_play_rows(tmp_path: Path) -> None:
    from tests.test_pipeline import write_synthetic_competition

    from bdb2027.__main__ import main

    data_dir = tmp_path / "data"
    write_synthetic_competition(data_dir)
    _enrich_for_cb(data_dir)
    output = tmp_path / "effects.csv"
    code = main(
        [
            "--data-dir",
            str(data_dir),
            "--output",
            str(output),
            "--cb-exploratory",
            "--cb-bootstrap-draws",
            "0",
        ]
    )
    assert code == 0
    coverage = pd.read_csv(tmp_path / "effects_cb_coverage.csv")
    assert set(coverage["coverage"]) == {"man"}
    assert coverage["meets_floor"].all()
    assert not coverage["preregistered"].any()
    assert set(coverage["nfl_id"]) <= {7, 8, 9, 10, 11, 12}
    summary = pd.read_csv(tmp_path / "effects_cb_coverage_summary.csv").iloc[0]
    assert summary["label_source"] == "coverage_assignment"
    assert summary["n_other_targets"] == 0
    assert summary["agreement_rate"] == pytest.approx(1.0)
    audit = pd.read_csv(tmp_path / "effects_cb_coverage_audit.csv")
    assert set(audit["player_label"]) == {"man"}
    metrics = pd.read_csv(tmp_path / "effects_cb_threat_metrics.csv").iloc[0]
    assert metrics["threat_definition"] == "completion"
    assert not metrics["preregistered"]
    assert metrics["n_matchups"] > 0
    effects = pd.read_csv(tmp_path / "effects_cb_threat_effects.csv")
    assert "closing_speed" in set(effects["term"])
    assert "wing_span" in set(effects["term"])
    assert (tmp_path / "effects_cb_threat_calibration.csv").is_file()
    written = {path.name for path in tmp_path.iterdir() if path.is_file()}
    assert "effects_cb_matchups.csv" not in written
    assert not any("matchup" in name for name in written)

    # A credited target in a non-regular-season game does not enter the table.
    from bdb2027.pipeline import run_analysis, run_cb_exploratory

    result = run_analysis(data_dir)
    extra = result["assignments"].iloc[:1].copy()
    extra["game_id"] = 999
    extra["expected_points_added"] = 99.0
    pooled = pd.concat([result["assignments"], extra], ignore_index=True)
    before = (
        coverage.groupby("nfl_id")["n_targets"].sum().to_dict()
        if not coverage.empty
        else {}
    )
    filtered = run_cb_exploratory(data_dir, assignments=pooled, players=None, n_bootstrap=0)
    after = filtered["coverage"].groupby("nfl_id")["n_targets"].sum().to_dict()
    assert after == before


def _enrich_for_cb(data_dir: Path) -> None:
    results = pd.read_csv(data_dir / "combine_results.csv")
    results["wing_span"] = 74.0 + results["nfl_id"]
    results["broad_jump"] = 118.0
    results["vertical"] = 35.0
    results.to_csv(data_dir / "combine_results.csv", index=False)

    plays = pd.read_csv(data_dir / "player_play.csv")
    plays["team_coverage_man_zone"] = "MAN"
    plays.to_csv(data_dir / "player_play.csv", index=False)

    for year in (2023, 2024, 2025):
        path = data_dir / f"game_tracking_{year}.csv"
        frames = pd.read_csv(path)
        frames["time"] = 1.0
        frames["s"] = 3.0 + (frames["nfl_id"] % 5) * 0.5
        frames["a"] = 1.5 + (frames["nfl_id"] % 3) * 0.4
        frames["o"] = (frames["nfl_id"] * 30) % 360
        frames["dir"] = (frames["nfl_id"] * 40) % 360
        lookback = frames.copy()
        lookback["time"] = 0.4
        lookback["event"] = "ball_snap"
        lookback["s"] = frames["s"] - 0.8
        pd.concat([lookback, frames], ignore_index=True).to_csv(path, index=False)
