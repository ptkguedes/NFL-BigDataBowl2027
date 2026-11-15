"""End-to-end run on a synthetic nine-file competition directory."""

from pathlib import Path

import pandas as pd

from bdb2027.__main__ import main
from bdb2027.pipeline import run_analysis
from bdb2027.preregistration import family_size
from bdb2027.schema import OFFICIAL_FILENAMES


def _brake_rows(
    *,
    nfl_id: int,
    draft_year: int,
    event_id: str,
    drill_type: str,
    drill_name: str,
    drop: float,
    break_at: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(9):
        speed = 2.0 + 2.0 * index if index < 4 else 8.0
        direction = 0.0
        if index >= break_at:
            speed = 8.0 - drop
            direction = 90.0
        rows.append(
            {
                "draft_year": draft_year,
                "event_id": event_id,
                "nfl_id": nfl_id,
                "entity_type": "PLAYER",
                "time": f"2023-03-01T00:00:00.{index * 100:03d}Z",
                "drill_type": drill_type,
                "drill_name": drill_name,
                "attempt": 1,
                "x": float(index),
                "y": 20.0,
                "s": speed,
                "a": 1.0,
                "dir": direction,
            }
        )
    return rows


def write_synthetic_competition(data_dir: Path) -> None:
    """Six tight ends and six defensive backs, two draft classes, fake ids."""
    data_dir.mkdir(parents=True, exist_ok=True)
    te_ids = [1, 2, 3, 4, 5, 6]
    db_ids = [7, 8, 9, 10, 11, 12]
    years = {1: 2023, 2: 2023, 3: 2023, 4: 2024, 5: 2024, 6: 2024}
    years.update({7: 2023, 8: 2023, 9: 2023, 10: 2024, 11: 2024, 12: 2024})
    # Within each class, index 0/1/2 is slow, middle, fast.
    rank = {1: 0, 2: 1, 3: 2, 4: 0, 5: 1, 6: 2, 7: 0, 8: 1, 9: 2, 10: 0, 11: 1, 12: 2}

    players = []
    for nfl_id in te_ids:
        players.append(_player(nfl_id, years[nfl_id], "TE"))
    for nfl_id in db_ids:
        players.append(_player(nfl_id, years[nfl_id], "CB"))
    for nfl_id in range(101, 107):
        players.append(_player(nfl_id, 2023, "WR"))
    pd.DataFrame(players).to_csv(data_dir / "players.csv", index=False)

    results = []
    for nfl_id in te_ids + db_ids:
        slot = rank[nfl_id]
        results.append(
            {
                "draft_year": years[nfl_id],
                "nfl_id": nfl_id,
                "combine_position": "TE" if nfl_id in te_ids else "DB",
                "ten_yd_split": 1.70 - 0.10 * slot,
                "forty": 4.80 - 0.10 * slot,
                "three_cone": 7.50 - 0.30 * slot,
            }
        )
    pd.DataFrame(results).to_csv(data_dir / "combine_results.csv", index=False)

    tracking: list[dict[str, object]] = []
    for nfl_id in te_ids:
        tracking.extend(
            _brake_rows(
                nfl_id=nfl_id,
                draft_year=years[nfl_id],
                event_id=f"te-{nfl_id}",
                drill_type="SKILL_DRILLS_TE",
                drill_name="TE_ROUTE",
                drop=1.0 + rank[nfl_id],
                break_at=5,
            )
        )
    for nfl_id in db_ids:
        tracking.extend(
            _brake_rows(
                nfl_id=nfl_id,
                draft_year=years[nfl_id],
                event_id=f"db-{nfl_id}",
                drill_type="SKILL_DRILLS_DB",
                drill_name="BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION",
                drop=1.0,
                break_at=3 + rank[nfl_id],
            )
        )
    tracking.append(
        {
            "draft_year": 2023,
            "event_id": "forty-ignore",
            "nfl_id": 1,
            "entity_type": "PLAYER",
            "time": "2023-03-01T00:00:01.000Z",
            "drill_type": "FORTY_YARD_DASH",
            "drill_name": "FORTY_YARD_DASH",
            "attempt": 1,
            "x": 0.0,
            "y": 0.0,
            "s": 9.0,
            "a": 0.0,
            "dir": 0.0,
        }
    )
    pd.DataFrame(tracking).to_csv(data_dir / "combine_tracking.csv", index=False)

    plays: list[dict[str, object]] = []
    play_id = 1
    for nfl_id in te_ids:
        completions = 1 + 2 * rank[nfl_id]
        separation = 1.0 + rank[nfl_id]
        for target_index in range(5):
            plays.append(
                _play(
                    play_id,
                    nfl_id,
                    "TE",
                    complete=target_index < completions,
                    separation=separation,
                    epa=0.1 * rank[nfl_id],
                )
            )
            play_id += 1
    db_plays: list[tuple[int, int, float, bool, float]] = []
    for nfl_id in db_ids:
        slot = rank[nfl_id]
        for _ in range(5):
            receiver = 101 + (nfl_id % 6)
            separation = 1.0 + slot
            complete = slot == 2
            epa = float(slot)
            plays.append(
                _play(play_id, receiver, "WR", complete=complete, separation=separation, epa=epa)
            )
            plays.append(
                _play(
                    play_id,
                    nfl_id,
                    "CB",
                    complete=complete,
                    separation=float("nan"),
                    epa=epa,
                    target=False,
                    team_abbr="DEF",
                    coverage_assignment="MAN",
                )
            )
            db_plays.append((play_id, nfl_id, separation, complete, epa))
            play_id += 1
    pd.DataFrame(plays).to_csv(data_dir / "player_play.csv", index=False)

    frames: list[dict[str, object]] = []
    for play_id, defender, separation, _complete, _epa in db_plays:
        receiver = 101 + (defender % 6)
        frames.append(_frame(play_id, receiver, 50.0, 20.0))
        frames.append(_frame(play_id, defender, 50.0, 20.0 + separation))
        decoy = 7 if defender != 7 else 8
        frames.append(_frame(play_id, decoy, 50.0, 40.0))
    pd.DataFrame(frames).to_csv(data_dir / "game_tracking_2023.csv", index=False)
    unused = pd.DataFrame([_frame(1, 1, 0.0, 0.0)])
    unused["event"] = "ball_snap"
    unused.to_csv(data_dir / "game_tracking_2024.csv", index=False)
    unused.to_csv(data_dir / "game_tracking_2025.csv", index=False)

    pd.DataFrame(
        {
            "game_id": [2023090700],
            "season": [2023],
            "season_type": ["REG"],
            "week": [1],
        }
    ).to_csv(data_dir / "games.csv", index=False)
    pd.DataFrame(
        {
            "nfl_id": te_ids + db_ids,
            "career_offensive_snaps": [10] * 12,
            "career_defensive_snaps": [0] * 6 + [10] * 6,
        }
    ).to_csv(data_dir / "player_career_successes.csv", index=False)


def _player(nfl_id: int, draft_year: int, position: str) -> dict[str, object]:
    return {
        "nfl_id": nfl_id,
        "display_name": f"Player {nfl_id}",
        "draft_year": draft_year,
        "nfl_position": position,
    }


def _play(
    play_id: int,
    nfl_id: int,
    position: str,
    *,
    complete: bool,
    separation: float,
    epa: float,
    target: bool = True,
    team_abbr: str = "OFF",
    coverage_assignment: str | None = None,
    game_id: int = 2023090700,
) -> dict[str, object]:
    return {
        "game_id": game_id,
        "play_id": play_id,
        "nfl_id": nfl_id,
        "lined_up_position": position,
        "pass_result": "C" if complete else "I",
        "play_nullified_by_penalty": "N",
        "target": target,
        "expected_points_added": epa,
        "separation_at_pass_forward": separation,
        "team_abbr": team_abbr,
        "coverage_assignment": coverage_assignment,
    }


def _frame(play_id: int, nfl_id: int, x: float, y: float) -> dict[str, object]:
    return {
        "game_id": 2023090700,
        "play_id": play_id,
        "nfl_id": nfl_id,
        "x": x,
        "y": y,
        "event": "pass_forward",
    }


def test_pipeline_reports_within_class_effects(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_synthetic_competition(data_dir)
    result = run_analysis(data_dir)
    effects = result["effects"]
    assert len(effects) == family_size() == 6
    assert set(effects["role"]) == {"primary", "secondary"}
    te_primary = effects.loc[effects["test_id"].eq("te_primary_decel_separation")].iloc[0]
    db_primary = effects.loc[effects["test_id"].eq("db_primary_break_separation")].iloc[0]
    assert te_primary["n_players"] == 6
    assert te_primary["pearson_r"] > 0.8
    assert te_primary["ci_low"] < te_primary["ci_high"]
    assert db_primary["n_players"] == 6
    assert db_primary["pearson_r"] < -0.5
    assert "FORTY_YARD_DASH" not in set(result["attempts"]["drill_type"])
    assert result["external"]["status"] == "skipped"
    assert result["n_games"] == 1
    three_cone = effects.loc[effects["test_id"].eq("te_secondary_three_cone_completion")].iloc[0]
    assert bool(three_cone["underpowered"]) is True
    assert int(effects["underpowered"].sum()) == 1


def test_preseason_targets_are_dropped(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_synthetic_competition(data_dir)
    plays = pd.read_csv(data_dir / "player_play.csv")
    extra = pd.DataFrame(
        [
            _play(
                9000 + index,
                1,
                "TE",
                complete=True,
                separation=20.0,
                epa=5.0,
                game_id=2023081000,
            )
            for index in range(5)
        ]
    )
    pd.concat([plays, extra], ignore_index=True).to_csv(data_dir / "player_play.csv", index=False)
    games = pd.read_csv(data_dir / "games.csv")
    preseason = pd.DataFrame(
        {"game_id": [2023081000], "season": [2023], "season_type": ["PRE"], "week": [1]}
    )
    pd.concat([games, preseason], ignore_index=True).to_csv(data_dir / "games.csv", index=False)

    regular = run_analysis(data_dir)["te_players"].set_index("nfl_id")
    assert regular.loc[1, "n_targets"] == 5
    assert regular.loc[1, "te_mean_separation"] == 1.0
    pooled = run_analysis(data_dir, regular_season_only=False)["te_players"].set_index("nfl_id")
    assert pooled.loc[1, "n_targets"] == 10


def test_sensitivity_drops_the_2024_class(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_synthetic_competition(data_dir)
    sensitivity = run_analysis(data_dir)["sensitivity"]
    assert set(sensitivity["angle"]) == {"DB"}
    assert len(sensitivity) == 3
    assert set(sensitivity["class_counts"]) == {"2023:3"}


def test_cli_missing_directory_lists_official_files(tmp_path: Path) -> None:
    code = main(["--data-dir", str(tmp_path / "absent"), "--output", str(tmp_path / "out.csv")])
    assert code == 1
    assert not (tmp_path / "out.csv").exists()


def test_cli_writes_effects(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_synthetic_competition(data_dir)
    output = tmp_path / "effects.csv"
    code = main(["--data-dir", str(data_dir), "--output", str(output)])
    assert code == 0
    written = pd.read_csv(output)
    assert len(written) == 6
    assert (tmp_path / "effects_sensitivity.csv").is_file()
    assert set(OFFICIAL_FILENAMES) == {
        "players.csv",
        "combine_results.csv",
        "combine_tracking.csv",
        "player_play.csv",
        "games.csv",
        "player_career_successes.csv",
        "game_tracking_2023.csv",
        "game_tracking_2024.csv",
        "game_tracking_2025.csv",
    }
