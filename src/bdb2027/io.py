"""Column-selective, chunked readers for the nine BDB 2027 CSVs.

These functions do not download data and do not create the input directory.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pandas as pd

from bdb2027.schema import (
    CAREER_REQUIRED,
    COLUMN_ALTERNATES,
    COMBINE_RESULTS_REQUIRED,
    COMBINE_TRACKING_REQUIRED,
    GAME_TRACKING_REQUIRED,
    GAMES_REQUIRED,
    KAGGLE_INPUT_DIR,
    OFFICIAL_FILENAMES,
    PLAYER_PLAY_REQUIRED,
    PLAYERS_REQUIRED,
)

DEFAULT_CHUNK_ROWS: int = 250_000


class DataLayoutError(Exception):
    """The input directory is missing a competition file."""


class SchemaError(Exception):
    """A competition file does not have a required column."""


def default_data_dir() -> Path:
    """Prefer the Kaggle input mount, otherwise a local `data/` directory."""
    kaggle = Path(KAGGLE_INPUT_DIR)
    if kaggle.is_dir():
        return kaggle
    return Path("data")


def missing_official_files(data_dir: Path) -> list[str]:
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        return list(OFFICIAL_FILENAMES)
    return [name for name in OFFICIAL_FILENAMES if not (data_dir / name).is_file()]


def require_official_files(data_dir: Path) -> Path:
    """Return `data_dir` when all nine official files are present."""
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise DataLayoutError(
            f"input directory does not exist: {data_dir}. "
            "Download the competition CSVs from Kaggle after accepting the rules. "
            f"Expected files: {', '.join(OFFICIAL_FILENAMES)}."
        )
    missing = missing_official_files(data_dir)
    if missing:
        raise DataLayoutError(
            f"input directory {data_dir} is missing: {', '.join(missing)}. "
            "Those files have to be downloaded from the competition data page."
        )
    return data_dir


def resolve_usecols(
    available: list[str],
    requested: tuple[str, ...] | list[str],
) -> tuple[list[str], dict[str, str]]:
    """Map requested names onto columns that are actually in the header.

    Returns the names to pass to `usecols` and a rename map back to the
    published names this package uses.
    """
    present = set(available)
    selected: list[str] = []
    rename: dict[str, str] = {}
    missing: list[str] = []
    for column in requested:
        if column in present:
            selected.append(column)
            continue
        alternate = next(
            (name for name in COLUMN_ALTERNATES.get(column, ()) if name in present),
            None,
        )
        if alternate is None:
            missing.append(column)
            continue
        selected.append(alternate)
        rename[alternate] = column
    if missing:
        raise SchemaError("missing columns: " + ", ".join(missing))
    return selected, rename


def iter_csv_chunks(
    path: Path,
    columns: tuple[str, ...] | list[str],
    *,
    chunksize: int = DEFAULT_CHUNK_ROWS,
) -> Iterator[pd.DataFrame]:
    """Yield chunks that contain only `columns`, in the requested order."""
    path = Path(path)
    if not path.is_file():
        raise DataLayoutError(f"missing file: {path}")
    try:
        header = pd.read_csv(path, nrows=0)
    except pd.errors.EmptyDataError as exc:
        raise SchemaError(f"empty file: {path}") from exc
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as exc:
        raise DataLayoutError(f"could not read {path}: {exc}") from exc

    selected, rename = resolve_usecols(list(header.columns), columns)
    requested = list(columns)
    try:
        reader = pd.read_csv(path, usecols=selected, chunksize=chunksize)
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as exc:
        raise DataLayoutError(f"could not read {path}: {exc}") from exc
    for chunk in reader:
        if rename:
            chunk = chunk.rename(columns=rename)
        yield chunk.loc[:, requested]


def read_csv_columns(
    path: Path,
    columns: tuple[str, ...] | list[str],
    *,
    chunksize: int = DEFAULT_CHUNK_ROWS,
    predicate: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Load `columns` from `path`, optionally keeping rows per chunk."""
    parts: list[pd.DataFrame] = []
    for chunk in iter_csv_chunks(path, columns, chunksize=chunksize):
        if predicate is not None:
            chunk = predicate(chunk)
        if not chunk.empty:
            parts.append(chunk)
    if not parts:
        return pd.DataFrame(columns=list(columns))
    return pd.concat(parts, ignore_index=True)


def load_players(data_dir: Path) -> pd.DataFrame:
    return read_csv_columns(Path(data_dir) / "players.csv", PLAYERS_REQUIRED)


def load_combine_results(data_dir: Path) -> pd.DataFrame:
    return read_csv_columns(
        Path(data_dir) / "combine_results.csv",
        COMBINE_RESULTS_REQUIRED,
    )


def load_games(data_dir: Path) -> pd.DataFrame:
    return read_csv_columns(Path(data_dir) / "games.csv", GAMES_REQUIRED)


def load_career(data_dir: Path) -> pd.DataFrame:
    return read_csv_columns(
        Path(data_dir) / "player_career_successes.csv",
        CAREER_REQUIRED,
    )


def load_player_play(data_dir: Path, *, chunksize: int = DEFAULT_CHUNK_ROWS) -> pd.DataFrame:
    return read_csv_columns(
        Path(data_dir) / "player_play.csv",
        PLAYER_PLAY_REQUIRED,
        chunksize=chunksize,
    )


def _keep_combine_analysis_rows(chunk: pd.DataFrame) -> pd.DataFrame:
    from bdb2027.preregistration import (
        DB_BACKPEDAL_DRILL_NAME,
        TE_SKILL_DRILL_TYPE,
        THREE_CONE_DRILL_TYPE,
    )

    entity = chunk["entity_type"].astype("string").str.upper()
    players = entity.eq("PLAYER") & chunk["nfl_id"].notna()
    drills = chunk["drill_type"].isin((TE_SKILL_DRILL_TYPE, THREE_CONE_DRILL_TYPE))
    backpedal = chunk["drill_name"].eq(DB_BACKPEDAL_DRILL_NAME)
    return chunk.loc[players & (drills | backpedal)]


def load_combine_tracking(
    data_dir: Path,
    *,
    chunksize: int = DEFAULT_CHUNK_ROWS,
) -> pd.DataFrame:
    """Load player rows for the TE skill, 3-cone, and DB backpedal drills."""
    return read_csv_columns(
        Path(data_dir) / "combine_tracking.csv",
        COMBINE_TRACKING_REQUIRED,
        chunksize=chunksize,
        predicate=_keep_combine_analysis_rows,
    )


def _keep_pass_forward(chunk: pd.DataFrame) -> pd.DataFrame:
    event = chunk["event"].astype("string")
    return chunk.loc[event.eq("pass_forward") & chunk["nfl_id"].notna()]


def load_pass_forward_tracking(
    data_dir: Path,
    *,
    chunksize: int = DEFAULT_CHUNK_ROWS,
) -> pd.DataFrame:
    """Load only `pass_forward` frames from the three season tracking files."""
    data_dir = Path(data_dir)
    frames: list[pd.DataFrame] = []
    for year in (2023, 2024, 2025):
        path = data_dir / f"game_tracking_{year}.csv"
        frame = read_csv_columns(
            path,
            GAME_TRACKING_REQUIRED,
            chunksize=chunksize,
            predicate=_keep_pass_forward,
        )
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=list(GAME_TRACKING_REQUIRED))
    return pd.concat(frames, ignore_index=True)
