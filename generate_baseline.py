#!/usr/bin/env python3
"""Baseline pipeline for an NFL Big Data Bowl submission.

Reads local competition CSVs and writes game_id, play_id, nfl_id, and
prediction. It does not download data and does not invent rows. A missing
input directory, an empty directory, or a folder without real NFL files
exits with status 1 and writes nothing.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ID_COLUMNS: tuple[str, ...] = ("game_id", "play_id", "nfl_id")
SUBMISSION_COLUMNS: tuple[str, ...] = (*ID_COLUMNS, "prediction")
INPUT_GLOBS: tuple[str, ...] = ("player_play.csv", "tracking_week_*.csv")
BASELINE_PREDICTION: float = 0.0


class BaselineDataError(Exception):
    """Raised when a submission cannot be built from local NFL inputs."""


def load_data(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Load real NFL CSV inputs from ``input_dir``.

    Keys are file stems such as ``player_play`` and ``tracking_week_1``.
    Only ``player_play.csv`` and ``tracking_week_*.csv`` are accepted.
    Raises BaselineDataError when the directory is missing, empty, or
    does not contain those files. This function does not create
    ``input_dir``.
    """
    input_dir = Path(input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise BaselineDataError(
            f"input directory does not exist: {input_dir}. "
            "No submission file was written."
        )
    if not any(input_dir.iterdir()):
        raise BaselineDataError(
            f"input directory is empty: {input_dir}. "
            "No submission file was written."
        )

    source_paths = _candidate_paths(input_dir)
    if not source_paths:
        raise BaselineDataError(_missing_data_message(input_dir))

    loaded: dict[str, pd.DataFrame] = {}
    for path in source_paths:
        loaded[path.stem] = _read_id_frame(path)
    return loaded


def extract_baseline_features(
    data_dict: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Reduce loaded NFL frames to one baseline row per player-play.

    ``prediction`` is the constant 0. Rows are copied from frames that
    contain game_id, play_id, and nfl_id. Raises BaselineDataError when
    no such rows exist, so the caller does not write a submission.
    """
    if not data_dict:
        raise BaselineDataError(
            "no real NFL data was loaded. "
            "No submission file was written."
        )

    frames: list[pd.DataFrame] = []
    for frame in data_dict.values():
        if any(column not in frame.columns for column in ID_COLUMNS):
            continue
        subset = frame.loc[:, list(ID_COLUMNS)]
        if subset.empty:
            continue
        frames.append(subset)
    if not frames:
        raise BaselineDataError(
            "no real NFL data with columns game_id, play_id, nfl_id. "
            "No submission file was written."
        )

    combined = pd.concat(frames, ignore_index=True)
    keys = combined.dropna(how="any")
    keys = keys.drop_duplicates(subset=list(ID_COLUMNS))
    if keys.empty:
        raise BaselineDataError(
            "NFL input files contain no rows with "
            "game_id, play_id, and nfl_id. "
            "No submission file was written."
        )

    features = keys.copy()
    features["prediction"] = np.full(
        len(features),
        BASELINE_PREDICTION,
        dtype=np.float64,
    )
    return features.loc[:, list(SUBMISSION_COLUMNS)]


def generate_submission(
    features_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Atomically write the Kaggle submission CSV.

    The file is written to a temporary sibling and then renamed over
    ``output_path``. Raises BaselineDataError when the frame is empty,
    columns are missing, or the output directory does not exist.
    """
    output_path = Path(output_path)
    missing = [
        column
        for column in SUBMISSION_COLUMNS
        if column not in features_df.columns
    ]
    if missing:
        joined = ", ".join(missing)
        raise BaselineDataError(
            f"submission frame is missing columns: {joined}. "
            "No submission file was written."
        )
    if features_df.empty:
        raise BaselineDataError(
            "submission frame has no rows. "
            "No submission file was written."
        )

    ordered = features_df.loc[:, list(SUBMISSION_COLUMNS)]
    _atomic_write_csv(ordered, output_path)
    logging.info(
        "Wrote baseline submission: %s (%s rows)",
        output_path,
        len(ordered),
    )


def main() -> None:
    """Parse CLI flags, run the baseline pipeline, and exit on failure."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    args = build_parser().parse_args()
    input_dir = Path(args.input_dir)
    output_path = Path(args.output)
    _exit_if_input_unusable(input_dir)
    try:
        data = load_data(input_dir)
        features = extract_baseline_features(data)
        generate_submission(features, output_path)
    except BaselineDataError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as exc:
        logging.error(
            "could not build the submission: %s. "
            "No submission file was written.",
            exc,
        )
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI. Paths default to ``data`` and ``submission.csv``."""
    parser = argparse.ArgumentParser(
        description=(
            "Write a baseline NFL Big Data Bowl submission "
            "from local CSV inputs."
        ),
    )
    parser.add_argument(
        "--input-dir",
        default=Path("data"),
        type=Path,
        help=(
            "Directory with competition CSV files. "
            "Default: data. Not created if missing."
        ),
    )
    parser.add_argument(
        "--output",
        default=Path("submission.csv"),
        type=Path,
        help=(
            "Submission CSV path. Default: submission.csv. "
            "Replaced atomically only when real rows exist."
        ),
    )
    return parser


def _exit_if_input_unusable(input_dir: Path) -> None:
    """Fail fast when the input directory is missing or empty."""
    if not input_dir.exists():
        logging.error(
            "input directory does not exist: %s. "
            "No submission file was written.",
            input_dir,
        )
        sys.exit(1)
    if not input_dir.is_dir():
        logging.error(
            "input path is not a directory: %s. "
            "No submission file was written.",
            input_dir,
        )
        sys.exit(1)
    try:
        has_entries = any(input_dir.iterdir())
    except OSError as exc:
        logging.error(
            "could not read input directory: %s. %s. "
            "No submission file was written.",
            input_dir,
            exc,
        )
        sys.exit(1)
    if not has_entries:
        logging.error(
            "input directory is empty: %s. "
            "No submission file was written.",
            input_dir,
        )
        sys.exit(1)


def _missing_data_message(input_dir: Path) -> str:
    return (
        f"no real NFL data in input directory: {input_dir}. "
        "Expected player_play.csv or tracking_week_*.csv with columns "
        "game_id, play_id, nfl_id. "
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


def _read_id_frame(path: Path) -> pd.DataFrame:
    try:
        header = pd.read_csv(path, nrows=0)
    except pd.errors.EmptyDataError as exc:
        raise BaselineDataError(
            f"NFL input file is empty: {path}. "
            "No submission file was written."
        ) from exc
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as exc:
        raise BaselineDataError(
            f"could not read NFL input file: {path}. {exc}. "
            "No submission file was written."
        ) from exc

    missing = [column for column in ID_COLUMNS if column not in header.columns]
    if missing:
        joined = ", ".join(missing)
        raise BaselineDataError(
            f"NFL input file {path.name} is missing columns: {joined}. "
            "No submission file was written."
        )
    try:
        frame = pd.read_csv(path, usecols=list(ID_COLUMNS))
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as exc:
        raise BaselineDataError(
            f"could not read NFL input file: {path}. {exc}. "
            "No submission file was written."
        ) from exc
    return frame


def _atomic_write_csv(frame: pd.DataFrame, output_path: Path) -> None:
    parent = output_path.parent
    if str(parent) == "":
        parent = Path(".")
    if not parent.exists() or not parent.is_dir():
        raise BaselineDataError(
            f"output directory does not exist: {parent}. "
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
            file_descriptor,
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            frame.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    main()
