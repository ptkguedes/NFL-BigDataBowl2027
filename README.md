# NFL Big Data Bowl 2027

Analysis project for the Kaggle hackathon [NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027), theme **Combine to NFL Performance**.

The entry is a Kaggle write-up with embedded charts and a public notebook. There is no prediction-file submission. `generate_baseline.py` was the wrong format for this competition and has been removed.

This repository studies two pre-registered questions:

- **Tight ends.** Do Combine explosiveness and deceleration measures (10-yard split, 3-cone, and TE position-drill braking from 10 Hz tracking) line up with in-game route separation and target outcomes?
- **Defensive backs.** Does the quality of the backpedal-to-break transition (`BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION`) line up with separation allowed, completions allowed, and EPA allowed?

Comparisons are **within draft class**. The code reports a pooled within-class Pearson correlation, a 95% Fisher interval, the class counts, and a Bonferroni threshold for the six-test family. Sample sizes around a position group are small; the result table marks `small_n` when fewer than 20 players enter a test.

## Rules

`docs/RULES_CHECKLIST.md` records what was checked against the Kaggle competition pages, the Kaggle competition record, and the NFL Football Operations Big Data Bowl page, including items that could not be verified. `docs/WRITEUP_DRAFT.md` is an outline for the write-up, not the submission itself.

## Data

The competition data is not in git. Accept the Kaggle rules yourself, then download the nine CSVs from the competition data page. Do not commit them and do not redistribute them. They are licensed CC BY-NC 4.0, and the rules also forbid giving them to anyone who has not agreed to the competition rules.

Place the files in `data/` locally, or let a Kaggle notebook read them from `/kaggle/input/nfl-big-data-bowl-2027/`:

- `players.csv`
- `combine_results.csv`
- `combine_tracking.csv`
- `player_play.csv`
- `games.csv`
- `player_career_successes.csv`
- `game_tracking_2023.csv`
- `game_tracking_2024.csv`
- `game_tracking_2025.csv`

The files were checked in a local WSL `data/` directory on 2026-11-15. `data/` is gitignored.

## Optional external ratings

An external rating file is allowed only when it is publicly available to every participant at no cost, or when it meets the host's Reasonableness Standard. See Rules section 2.6 in the checklist. Madden ratings were **not** verified to meet that test. The comparison is implemented and **off by default**. It does not download, scrape, or write ratings. Do not commit a Madden file.

```bash
python -m bdb2027 --data-dir data --enable-external-benchmark \
  --external-benchmark /path/outside/the/repo/ratings.csv
```

Expected columns are `nfl_id` plus any of `speed`, `acceleration`, `agility`, `change_of_direction`, `route_running`, `release`, `man_coverage`, and `zone_coverage`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e . -r requirements-dev.txt
```

Runtime dependencies are `numpy` and `pandas` (`requirements.txt`). Development tools are `ruff` and `pytest` (`requirements-dev.txt`).

## Run

```bash
.venv/bin/python -m bdb2027 --data-dir data --output outputs/effects.csv
```

The command writes `outputs/effects.csv`. It does not write a submission CSV. If `data/` is missing files, it exits with status 1 and names the missing files.

The Kaggle notebook skeleton is `notebooks/bdb2027_combine_to_nfl.ipynb`.

## Layout

```text
src/bdb2027/          column-selective loaders, drill features, outcomes, linkage
notebooks/            Kaggle notebook skeleton
tests/                synthetic fixtures and unit tests only
docs/RULES_CHECKLIST.md
docs/WRITEUP_DRAFT.md
.github/workflows/ci.yml
```

## Tests

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

CI runs the same two commands on Python 3.12. Tests build small synthetic tables. They do not read competition data.

## Method notes that affect the numbers

- Deceleration is the drop in speed per second. Column `a` is never negative in the files, so it is not used as a signed brake.
- A "break" is not an official event on Combine tracking. It is the first frame, after the athlete is moving, where heading has changed by 45 degrees from the opening heading. The threshold is pre-registered in `src/bdb2027/preregistration.py`.
- Tight-end separation is `separation_at_pass_forward` on targeted plays with `lined_up_position` TE.
- Outcomes use regular-season games only (amendment A1, 2026-11-15).
- Game tracking covers only the 510 draftees. A draftee DB is credited with a target when the targeted receiver is a tracked draftee and the DB is the closest opposing DB with an active `coverage_assignment` within 5 yards at `pass_forward` (amendment A2). Separation allowed is the receiver's `separation_at_pass_forward`. Completions allowed and EPA allowed come from that play. These are analysis definitions, not published defender columns.
- Breaks are searched for only in the first 5.5 s of each attempt, because 2024 backpedal attempts are cut at about 6 s (amendment A3). The CLI also writes `<output>_sensitivity.csv` with the DB tests without the 2024 class.
- Fisher intervals use `n - 3 - (k - 1)` degrees of freedom for `k` draft classes (A4). The TE 3-cone test is flagged `underpowered` (A5).
- Plays with `play_nullified_by_penalty` equal to `Y` are dropped.
- Draft class is `draft_year`. Predictors and outcomes are demeaned inside the class before the correlation.
