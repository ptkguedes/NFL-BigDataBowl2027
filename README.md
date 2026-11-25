# NFL Big Data Bowl 2027

Analysis project for the Kaggle hackathon [NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027), theme **Combine to NFL Performance**.

The entry is a Kaggle write-up with embedded charts and a public notebook. There is no prediction-file submission. `generate_baseline.py` was the wrong format for this competition and has been removed.

This repository studies two pre-registered questions:

- **Tight ends.** Do Combine explosiveness and deceleration measures (10-yard split, 3-cone, and TE position-drill braking from 10 Hz tracking) line up with in-game route separation and target outcomes?
- **Defensive backs.** Does the quality of the backpedal-to-break transition (`BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION`) line up with separation allowed, completions allowed, and EPA allowed?

## Current lead (to validate)

On the 2023-2025 draft classes, after the dated amendments A1-A6 (2026-11-15), the DB thesis is **speed retention through the backpedal break goes with lower EPA allowed**. The within-class correlation is r = -0.60 (95% interval -0.81 to -0.25, p = 0.002, n = 26), and it holds without the 2024 class (r = -0.65, n = 15). It is a secondary test that only appeared after the amendments, so it is a lead to validate, not a result. Robustness checks are in `docs/WRITEUP_DRAFT.md` (Table 2). Time to the break shows no link to separation allowed. DBs with no break by 5.5 s allowed fewer completions, possibly because they align deeper, which is untested. The tight-end tests are weak.

Scenario view, from a bootstrap posterior with a flat prior and 90% bands:
- A rookie DB at the within-class 75th percentile of retention beats his class median EPA allowed per target with probability 0.68 (0.56-0.84). One at the 25th percentile does so with probability 0.34.
- The high-minus-low gap is -0.32 EPA per target, or -19 EPA over an assumed 60-target season. Treat that as an upper bound that should shrink on new data.
- The gap is stronger in man coverage than in zone.

The cushion check gives only weak support to the idea that slow breakers align deeper.

Run `python -m bdb2027 --data-dir data --robustness --scenarios` to also write `<output>_robustness.csv`, `<output>_scenarios.csv` and `<output>_cushion.csv`. These hold aggregate statistics only. The notebook draws Figures 1 and 2 at runtime with `bdb2027.figures`, and no images are committed. Plotting needs `matplotlib`, which is in `requirements-dev.txt`.

Comparisons are **within draft class**. The code reports a pooled within-class Pearson correlation, a 95% Fisher interval, the class counts, and a Bonferroni threshold for the six-test family. Sample sizes around a position group are small; the result table marks `small_n` when fewer than 20 players enter a test.

## Rules

`docs/RULES_CHECKLIST.md` records what was checked against the Kaggle competition pages, the Kaggle competition record, and the NFL Football Operations Big Data Bowl page, including items that could not be verified. `docs/WRITEUP_DRAFT.md` holds the draft submission text between markers (checked by `tests/test_writeup.py` for at most 2,000 words and fewer than 10 tables and figures) and author notes that are not submitted.

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

Cornerback man/zone tables and the threat model are a separate, exploratory pass. They do not change the six-test family:

```bash
.venv/bin/python -m bdb2027 --data-dir data --output outputs/effects.csv --cb-exploratory
```

`--cb-bootstrap-draws` sets the cluster bootstrap for the threat-model intervals (default 200). The pass needs `wing_span`, `broad_jump`, and `vertical` on `combine_results.csv`, `team_coverage_man_zone` on `player_play.csv`, and `time`, `s`, `a`, `o`, and `dir` on the game-tracking files. Details are in the next section.

The Kaggle notebook skeleton is `notebooks/bdb2027_combine_to_nfl.ipynb`.

## Layout

```text
src/bdb2027/          loaders, drill features, outcomes, linkage, exploratory CB analyses
notebooks/            Kaggle notebook skeleton
tests/                synthetic fixtures and unit tests only
docs/RULES_CHECKLIST.md
docs/WRITEUP_DRAFT.md
.github/workflows/ci.yml
```

## Exploratory cornerbacks

Not pre-registered. The DB tests still pool CB, SS, FS, DB, and S. This pass keeps `nfl_position == CB` only, on the same regular-season games and the same coverage-credit rule (an opposing draftee with an active assignment, closest at `pass_forward`, within 5 yards). Safeties stay in the original tests and out of these tables.

### Man and zone

The split is the corner's own `coverage_assignment`, not `team_coverage_man_zone`.

The assignment is the job that corner was given on the play. The team column is the defensive shell, and it is the same for every defender on that play. A Cover-1 shell is man with a deep zone behind it. A Cover-3 shell is zone, and the two corners are not doing the same job. The credit rule already requires an active `coverage_assignment`, so the split uses that same column. The team shell is written only as an agreement audit.

A token that contains MAN and not a zone word is man (`MAN`, `MAN_MATCH`, `2_MAN`). A token that contains a zone word and not MAN is zone (`ZONE`, `DEEP_FREE`, `CURL_FLAT_LEFT`, and the same family: FLAT, HOOK, SEAM, QUARTER, HALF, THIRD, BRACKET, PALM). A token that names both, or neither (`MAN_ZONE`, `COVER_3`, `NO_ASSIGNMENT`), is `other` and is left out of the man and zone rows. The older retention robustness check is a different rule, exact `MAN` versus everything else, and it is unchanged.

The table has one row per CB and coverage type with at least one credited target. It reports targets, completion rate allowed, EPA allowed, and separation allowed. Each cell has the raw mean (`mean_epa`, `mean_separation`, `completion_rate`) beside the empirical-Bayes shrinkage estimate. Completion uses a beta-binomial model. EPA and separation use a normal-normal model with a DerSimonian-Laird between-CB variance, stored as `epa_tau2` and `separation_tau2`. The 95% intervals plug those hyperparameters in, so they do not include uncertainty about the prior itself.

When that between-CB variance is estimated as 0, `epa_pooling` or `separation_pooling` is `complete`. Every CB in that coverage then has the same shrunk value and the same interval: the shared mean. A zone sample where corners look alike after within-play noise will do this, and the shrunk EPA column will be identical down the zone rows. The raw player mean in `mean_epa` is unchanged. The summary file counts those rows (`n_zone_epa_complete_pool` and the man and separation counterparts) and repeats the explanation in `complete_pool_note`. `partial` means the shrunk value is pulled toward the coverage mean but still differs by CB. The figure draws shrunk EPA for rows that meet the floor, so complete pooling stacks those points. Read `mean_epa` for the unpooled player value.

A row with fewer than 5 targets is flagged `meets_floor=False`. `small_n` is set below 20 targets, the same threshold as the pre-registered tables.

### Threat probability

A credited matchup is a threat when the targeted receiver's `pass_result` is `C`. Completion is the event the rep is asked to prevent, and it is recorded after the throw. Positive EPA was set aside because it mixes yards after the catch. A separation cutoff at the catch was set aside because that frame is after the throw and restates the tracking geometry.

The model is an L2-penalized logistic regression with a normal player intercept per CB. Slopes are log-odds per 1 SD of the estimation sample, and the table also reports the mean change in completion probability for a 1 SD increase. The penalty is chosen by grouped cross-validation that scores held-out corners with their intercept set to zero. Combine traits do not vary within a CB, so an unpenalized intercept would swallow wing span, broad jump, and vertical. Scoring a held-out corner at a zero intercept keeps trait coefficients that predict someone the fit did not see. Intervals are percentile intervals from a cluster bootstrap that resamples corners and refits at that fixed penalty. They are blank when fewer than 20 bootstrap fits succeed. Calibration (Brier, log loss, reliability bins, ECE) is the grouped cross-validation, compared with an intercept-only model on the same folds.

Features, all known at or before the throw:

- separation between the CB and the credited receiver at `pass_forward`
- closing speed, positive when that gap is shrinking (NGS direction: 0 degrees is +y, 90 degrees is +x)
- hip error, the angle between orientation `o` and the bearing to the receiver
- motion error, the same angle for direction of travel `dir`
- CB speed `s` and acceleration magnitude `a` (the files do not sign `a`)
- change in CB speed from about 0.5 seconds before the throw
- Combine `wing_span`, `broad_jump`, and `vertical`

Height, weight, and arm length stay out so wing span is not split with arm length.

Plays with no `pass_forward` timestamp are dropped. Event names that record the result of the throw (`pass_outcome_*`, `pass_arrived`, tackle, touchdown, and the same family) are dropped. Every other frame is kept only at or before `pass_forward`.

### Files

`--cb-exploratory` writes:

- `outputs/effects_cb_coverage.csv` — the player-level man/zone table, with raw means beside shrunk values and an `epa_pooling` flag (`complete` when tau^2 is 0). Do not commit it.
- `outputs/effects_cb_coverage_audit.csv` — assignment strings, the man/zone/other label, and agreement with the team shell. No player ids.
- `outputs/effects_cb_coverage_summary.csv` — the label choice, the floor, and the agreement rate.
- `outputs/effects_cb_threat_effects.csv` — coefficients, odds ratios, and probability differences, with intervals.
- `outputs/effects_cb_threat_calibration.csv` — grouped-CV reliability bins.
- `outputs/effects_cb_threat_metrics.csv` — Brier, log loss, ECE, sample size, and the threat definition.

The notebook section "Exploratory cornerbacks" draws the two figures with `bdb2027.figures.figure_cb_coverage` and `figure_threat_effects`. Like Figure 1, the coverage figure has one point per player. Do not export it outside Kaggle.

Limits to keep in mind: the credit rule still sees only draftee-on-draftee targets, the per-CB samples are small, the intervals treat the shrinkage prior as known, and nothing here adjusts for opponent, throw quality, or drops. It is not one of the six pre-registered tests.

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
- Breaks are searched for only in the first 5.5 s of each attempt, because 2024 backpedal attempts are cut at about 6 s (amendment A3). Attempts with no break by then are censored at 5.5 s, and the two DB break-time tests use a within-class Spearman correlation (amendment A6). Speed retention exists only for detected breaks. The CLI also writes `<output>_sensitivity.csv` with the DB tests without the 2024 class.
- Fisher intervals use `n - 3 - (k - 1)` degrees of freedom for `k` draft classes (A4). The TE 3-cone test is flagged `underpowered` (A5).
- Plays with `play_nullified_by_penalty` equal to `Y` are dropped.
- Draft class is `draft_year`. Predictors and outcomes are demeaned inside the class before the correlation.
