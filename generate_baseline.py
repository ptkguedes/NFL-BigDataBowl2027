#!/usr/bin/env python3
"""Generate a baseline NFL Big Data Bowl submission from local CSV inputs.

The script does not download competition data. It writes game_id, play_id,
nfl_id, and prediction only after real input files are found. If the input
directory or those files are missing, it exits with an error and does not
create a submission.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

ID_COLUMNS: tuple[str, ...] = ("game_id", "play_id", "nfl_id")
SUBMISSION_COLUMNS: tuple[str, ...] = (*ID_COLUMNS, "prediction")
INPUT_GLOBS: tuple[str, ...] = ("player_play.csv", "tracking_week_*.csv")
BASELINE_PREDICTION: float = 0.0


class BaselineDataError(Exception):
    """Raised when a submission cannot be built from local NFL inputs."""


def generate_baseline_submission(input_dir: Path, output_path: Path) -> Path:
    """Write a baseline submission CSV from real local NFL inputs.

    ``input_dir`` must already exist and contain ``player_play.csv`` or
    ``tracking_week_*.csv`` with columns game_id, play_id, and nfl_id.
    This function does not create ``input_dir`` and does not write
    ``output_path`` when that data is missing.

    Each output row is one distinct player-play from those files.
    ``prediction`` is the constant baseline 0. The CSV is replaced
    atomically: a temporary file is written in the output directory, then
    renamed over ``output_path``.
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    if not input_dir.exists():
        raise BaselineDataError(
            f"ERROR: input directory does not exist: {input_dir}\n"
            "No submission file was written."
        )
    if not input_dir.is_dir():
        raise BaselineDataError(
            f"ERROR: input path is not a directory: {input_dir}\n"
            "No submission file was written."
        )

    source_paths = _candidate_paths(input_dir)
    submission = _build_submission(source_paths) if source_paths else None
    if submission is None:
        raise BaselineDataError(_missing_data_message(input_dir))

    _atomic_write_csv(submission, output_path)
    print(f"Wrote baseline submission: {output_path} ({len(submission)} rows)")
    return output_path


def _missing_data_message(input_dir: Path) -> str:
    return (
        f"ERROR: no real NFL data in input directory: {input_dir}\n"
        "Expected player_play.csv or tracking_week_*.csv with columns "
        "game_id, play_id, nfl_id.\n"
        "No submission file was written."
    )


def _candidate_paths(input_dir: Path) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in INPUT_GLOBS:
        for path in sorted(input_dir.glob(pattern)):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(path)
    return found


def _build_submission(source_paths: list[Path]) -> pd.DataFrame | None:
    pandas = _import_pandas()
    frames: list[pd.DataFrame] = []
    for path in source_paths:
        frame = _read_id_frame(pandas, path)
        if frame is not None:
            frames.append(frame)
    if not frames:
        return None
    combined = pandas.concat(frames, ignore_index=True)
    keys = combined.loc[:, list(ID_COLUMNS)].dropna(how="any")
    keys = keys.drop_duplicates(subset=list(ID_COLUMNS))
    if keys.empty:
        return None
    submission = keys.copy()
    submission["prediction"] = BASELINE_PREDICTION
    return submission.loc[:, list(SUBMISSION_COLUMNS)]


def _import_pandas() -> ModuleType:
    try:
        import pandas as pandas_module
    except ImportError as exc:
        raise BaselineDataError(
            "ERROR: pandas is required to read NFL CSV inputs. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from exc
    return pandas_module


def _read_id_frame(pandas: ModuleType, path: Path) -> pd.DataFrame | None:
    try:
        header = pandas.read_csv(path, nrows=0)
        if any(column not in header.columns for column in ID_COLUMNS):
            return None
        frame = pandas.read_csv(path, usecols=list(ID_COLUMNS))
    except pandas.errors.EmptyDataError:
        return None
    except (OSError, UnicodeError, pandas.errors.ParserError) as exc:
        raise BaselineDataError(
            f"ERROR: could not read NFL input file: {path}\n"
            f"{exc}\n"
            "No submission file was written."
        ) from exc
    if frame.empty:
        return None
    return frame


def _atomic_write_csv(frame: pd.DataFrame, output_path: Path) -> None:
    parent = output_path.parent
    if str(parent) == "":
        parent = Path(".")
    if not parent.exists() or not parent.is_dir():
        raise BaselineDataError(
            f"ERROR: output directory does not exist: {parent}\n"
            "No submission file was written."
        )

    temporary_path: Path | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(
            file_descriptor, "w", encoding="utf-8", newline=""
        ) as handle:
            frame.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI. Input and output paths are required arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Write a baseline NFL Big Data Bowl submission from local CSV inputs."
        )
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Existing directory with competition CSV files. Not created if missing.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Submission CSV path. Replaced atomically only when real rows exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse CLI paths and write a baseline submission, or return exit code 1."""
    args = build_parser().parse_args(argv)
    try:
        generate_baseline_submission(args.input_dir, args.output)
    except BaselineDataError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
