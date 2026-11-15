"""Loader tests against tiny synthetic CSVs."""

from pathlib import Path

import pandas as pd
import pytest

from bdb2027.io import SchemaError, iter_csv_chunks, read_csv_columns, resolve_usecols

FIXTURE = Path(__file__).parent / "fixtures" / "players_min.csv"


def test_fixture_reader_drops_extra_columns() -> None:
    frame = read_csv_columns(FIXTURE, ["nfl_id", "nfl_position"])
    assert list(frame.columns) == ["nfl_id", "nfl_position"]
    assert frame["nfl_id"].tolist() == [900001, 900002]


def test_chunks_cover_every_row(tmp_path: Path) -> None:
    source = tmp_path / "rows.csv"
    pd.DataFrame({"nfl_id": range(10), "other": range(10)}).to_csv(source, index=False)
    parts = list(iter_csv_chunks(source, ["nfl_id"], chunksize=4))
    assert [len(part) for part in parts] == [4, 4, 2]
    stacked = pd.concat(parts, ignore_index=True)
    assert stacked["nfl_id"].tolist() == list(range(10))
    assert "other" not in stacked.columns


def test_missing_column_names_the_file_requirement() -> None:
    with pytest.raises(SchemaError, match="birth_date"):
        read_csv_columns(FIXTURE, ["nfl_id", "birth_date"])


def test_published_win_probability_alias() -> None:
    available = ["game_id", "visitor_team_win_probability_added"]
    selected, rename = resolve_usecols(available, ["visitor_team_win_probility_added"])
    assert selected == ["visitor_team_win_probability_added"]
    assert rename == {"visitor_team_win_probability_added": "visitor_team_win_probility_added"}
