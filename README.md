# NFL Big Data Bowl 2027

![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)

Baseline submission pipeline for the Kaggle NFL Big Data Bowl. `generate_baseline.py` reads competition CSVs that are already on disk and writes a submission with `game_id`, `play_id`, `nfl_id`, and `prediction`.

## Pipeline

The script runs three stages:

1. **`load_data`** reads `player_play.csv` and `tracking_week_*.csv` from the input directory. Each frame keeps only `game_id`, `play_id`, and `nfl_id`. The input directory is never created.
2. **`extract_baseline_features`** keeps one row per distinct `(game_id, play_id, nfl_id)` and sets `prediction` to the constant `0.0`.
3. **`generate_submission`** writes the CSV atomically: a temporary file in the output directory, flushed and synced, then renamed over the destination.

`main` checks the input path before those stages. A `BaselineDataError`, or a read/write failure (`OSError`, `UnicodeError`, `ValueError`, or a CSV parse error), is logged and the process exits with code 1. A submission file is written only after every check passes.

## Fail-fast

The process exits with code 1 and writes nothing when:

- `--input-dir` is missing, is not a directory, or is empty
- the directory contains neither `player_play.csv` nor `tracking_week_*.csv`
- a matched file is empty, unreadable, or missing `game_id`, `play_id`, or `nfl_id`
- no row has all three id values filled
- the submission frame is empty or missing a required column
- the output directory does not already exist

## CLI

| Flag | Default | Notes |
| --- | --- | --- |
| `--input-dir` | `data` | Directory of competition CSVs. Not created when it is missing. |
| `--output` | `submission.csv` | Replaced only after a real submission is built. The parent directory must already exist. |

## Inputs and output

Place the official files in the input directory (default `data/`):

- `player_play.csv`
- `tracking_week_*.csv` (for example `tracking_week_1.csv`)

Only those names are loaded. Rows with a missing id are dropped, and duplicate id triples collapse to one row.

The output is a UTF-8 CSV with no index column:

```csv
game_id,play_id,nfl_id,prediction
```

Every `prediction` value is `0.0`.

## Setup

From the project root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` lists `numpy` and `pandas`.

## Usage

Defaults (`data` in, `submission.csv` out):

```bash
.venv/bin/python generate_baseline.py
```

Explicit paths:

```bash
.venv/bin/python generate_baseline.py --input-dir data --output submission.csv
```

## Project layout

```text
.
├── generate_baseline.py   # load, baseline rows, atomic CSV write
├── requirements.txt       # numpy, pandas
├── .gitignore             # .venv/, caches, data/, *.csv
└── README.md
```

`data/`, `submission.csv`, and other `*.csv` files stay local. They are listed in `.gitignore`.

## Status / Next steps

Work in progress. This baseline copies player-play ids and writes a constant prediction. Real features and a model are still to come.
