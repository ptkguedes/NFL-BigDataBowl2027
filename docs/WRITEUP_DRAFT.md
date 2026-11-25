# Write-up draft

This file has two parts. Part A, between the `SUBMISSION START` and `SUBMISSION END` markers, is the draft text for the Kaggle write-up. `tests/test_writeup.py` checks that it stays at or under 2,000 words and under 10 tables and figures. Part B is author notes, which are not submitted.

Numbers in Part A match the 2026-11-25 re-run on `main` at `9a8b9eb`:

`python -m bdb2027 --data-dir data --output outputs/effects.csv --robustness --scenarios --cb-exploratory`

That run confirmed the 2026-11-15 family, robustness, and scenario tables (amendments A1-A6) and fit the exploratory cornerback sections. Re-run before submitting and update every number. Do not commit the output CSVs, and do not add a per-player table.

Track to select at submission: Open or University. University only if every member is an undergraduate. Leave the Grand Prize track empty unless that changes.

<!-- SUBMISSION START -->

# Holding speed through the break: Combine backpedal tracking and EPA allowed by rookie defensive backs

*Speed kept through the backpedal break is the only pre-registered test under 0.05/6. Break time and the tight-end tests miss that bar. Cornerback shrinkage and a completion model are exploratory.*

## Summary

We linked 10 Hz Combine tracking to regular-season coverage for the 2023-2025 draft classes. Defensive backs who kept more speed through the 45-degree backpedal break allowed less EPA per credited target. The pooled within-class correlation is r = -0.596 (95% interval -0.806 to -0.253, p = 0.00166, n = 26: 8 in 2023, 11 in 2024, 7 in 2025).

That row is a secondary test in a family of six. The Bonferroni threshold is 0.05/6 = 0.0083, and this is the only row that clears it. The other five miss it. Time to the break shows no link to separation allowed. The tight-end tests are weak. Amendments A1-A6 came after the first run, and n is small, so the lead still needs a later class.

## Data

We used the nine competition files. Game tracking and `player_play.csv` cover only the 510 draftees, about three tracked players per throw. Outcomes use regular-season games only (`season_type` REG). Plays nullified by penalty are dropped. Comparisons stay inside a draft class, because Combine recording differs by year. The 2024 backpedal drill ends after about 6 seconds, against 10 to 12 seconds in 2023 and 2025.

## Measures

**Break.** Breaks are not labeled. The break is the first frame, after the athlete passes 1 yd/s, where travel direction has turned 45 degrees from the opening heading. The search stops at 5.5 seconds in every year, so 2024 is not penalized for a short file. An attempt with no break by then is censored at 5.5 seconds and ranks slowest. A player's value is the median over his attempts.

**Speed retention.** Median speed in the 0.3 seconds after the break, divided by median speed in the 0.3 seconds before it. It exists only for detected breaks.

**Coverage credit.** A targeted draftee receiver is credited to the closest opposing draftee DB with an active `coverage_assignment`, if that DB is within 5 yards at `pass_forward`. The credit carries the play's EPA, the completion, and the receiver's `separation_at_pass_forward`. A DB enters the tests with at least 5 credited targets.

## Method

Inside each draft class we demean the predictor and the outcome, then correlate the deviations. The two break-time tests rank both variables inside the class first (pooled within-class Spearman), so censored players tie at the slowest rank. Intervals are Fisher intervals that spend one degree of freedom per class mean removed. Spearman rows use the 1.06 variance factor. Table 1 is the family the notebook prints from `effects_summary`. "Clears 0.05/6" means two-sided p below 0.0083.

**Table 1. Pre-registered family after amendments A1-A6.**

| Test | Method | r | 95% interval | p | n | Clears 0.05/6 |
| --- | --- | --- | --- | --- | --- | --- |
| TE: harder brake -> separation | Pearson | 0.164 | -0.300, 0.566 | 0.495 | 22 | No |
| TE: faster 10-yard split -> separation | Pearson | 0.084 | -0.398, 0.530 | 0.744 | 20 | No |
| TE: faster 3-cone -> completion (underpowered) | Pearson | 0.748 | -0.163, 0.970 | 0.094 | 7 | No |
| DB: quicker break -> separation allowed | Spearman | -0.019 | -0.319, 0.285 | 0.907 | 47 | No |
| DB: speed retention -> EPA allowed | Pearson | -0.596 | -0.806, -0.253 | 0.00166 | 26 | Yes |
| DB: quicker break -> completion rate allowed | Spearman | 0.222 | -0.085, 0.491 | 0.155 | 47 | No |

The break-time rows censor 21 of 47 players. Retention has no censored players. The 3-cone row is 7 players in 2 classes.

## Defensive backs: speed retention and EPA allowed

**Figure 1.** Placeholder, drawn at runtime by `figure_retention_scatter` (notebook section "Figure 1") and not stored in the repo. Within-class speed retention against EPA allowed per credited target, one point per DB, colored by draft class. The line is the pooled within-class slope.

Table 2 is the fragility check, outside the family of six. Digits match `robustness.round(3)`.

**Table 2. Robustness of retention -> EPA allowed.**

| Check | r | 95% interval | n |
| --- | --- | --- | --- |
| Main row | -0.596 | -0.806, -0.253 | 26 |
| Within-class Spearman | -0.544 | -0.782, -0.168 | 26 |
| Without 2023 | -0.650 | -0.862, -0.247 | 18 |
| Without 2024 | -0.652 | -0.879, -0.186 | 15 |
| Without 2025 | -0.414 | -0.738, 0.065 | 19 |
| Bootstrap within class (2,000 draws) | -0.596 | -0.861, -0.292 | 26 |
| Range if any one player is removed | -0.707 to -0.521 | | 26 |
| At least 10 credited targets | -0.431 | -0.794, 0.157 | 14 |
| Man targets only (exact MAN, at least 3) | -0.647 | -0.847, -0.286 | 22 |
| Zone targets only (non-MAN, at least 3) | -0.261 | -0.622, 0.193 | 23 |

The sign stays negative, and dropping any one player leaves r between -0.707 and -0.521. Without 2024 the interval still excludes zero (r = -0.652, n = 15, p = 0.0097), and that p-value misses 0.0083. Without 2025 the interval crosses zero (r = -0.414, n = 19), as it does at a 10-target floor (r = -0.431, n = 14). The association sits in exact-MAN targets (r = -0.647, n = 22). The zone row is every other assignment and crosses zero (r = -0.261, n = 23). Exploratory labels below use a different rule.

The family pools CB, SS, FS, DB, and S. Of these 26 players, 20 are cornerbacks and 6 are safeties. Cornerbacks alone: r = -0.640 (95% interval -0.852 to -0.246, p = 0.0033, n = 20: 5 in 2023, 10 in 2024, 5 in 2025). That filter is outside Table 2. Safeties alone are too few. Dropping 2025, the cornerback interval crosses zero (r = -0.384, n = 15, p = 0.18). Dropping 2024 leaves n = 10 (r = -0.766, p = 0.013).

**Figure 2.** Placeholder, drawn at runtime by `figure_forest` (notebook section "Figure 2"). Fisher intervals for the six family tests and the Table 2 checks. The leave-one-player bar is the range of r.

## Probabilities and scenarios

We resampled players within each class 4,000 times: a bootstrap approximation to a flat-prior posterior. Each draw refits the within-class slope of EPA allowed on retention, then compares the within-class 75th percentile of retention (raw value about 1.10) with the 25th (about 1.04). A "season" assumes 60 targets, a full-time starter's volume, which these files do not count. Credited targets are draftee-on-draftee only (median 5 per DB-season). Bands are 90%. The notebook prints `scenarios.round(3)`.

**Table 3. Retention scenarios (bootstrap posterior, 90% bands).**

| Quantity | All targets (n 26) | Man only (n 22) | Zone only (n 23) |
| --- | --- | --- | --- |
| P(slope below zero) | 1.000 | 0.998 | 0.924 |
| P(75th percentile allows less EPA/target than class median) | 0.681 (0.555-0.837) | 0.688 (0.538-0.854) | 0.578 (0.435-0.746) |
| P(25th percentile allows less EPA/target than class median) | 0.336 (0.163-0.480) | 0.246 (0.085-0.426) | 0.433 (0.305-0.547) |
| EPA/target, high minus low retention | -0.319 (-0.488 to -0.175) | -0.593 (-0.952 to -0.219) | -0.184 (-0.440 to 0.024) |
| EPA per 60 targets, high minus low | -19.2 (-29.3 to -10.5) | -35.6 (-57.1 to -13.1) | -11.1 (-26.4 to 1.5) |

A high-retention rookie beats his class median with probability 0.681, and a low-retention rookie with probability 0.336. The 60-target gap should shrink on new players: nothing here is shrunk, and the lead was fit after amendments. At the observed credited volume the gap is -1.60 EPA per season (-2.44 to -0.88).

## Defensive backs: time to the break

Quicker breaks show no link to separation allowed (Spearman r = -0.019, p = 0.907, n = 47). The completion row has the opposite sign to the one we expected (r = 0.222, interval -0.085 to 0.491, p = 0.155). Both miss 0.05/6. In these tests, 21 of 47 DBs are censored at 5.5 seconds and tie at the slowest rank.

Pre-snap `cushion` is only weak support for "slow breakers line up deeper." Within class they line up 0.57 yards deeper on credited targets (6.2 yards against 5.6, permutation p = 0.18) and 0.45 yards deeper on all snaps (p = 0.27). The censored group has more safeties (38% against 23%, p = 0.35).

## Tight ends

All three miss 0.05/6. Braking (r = 0.164, p = 0.495, n = 22) and the 10-yard split (r = 0.084, p = 0.744, n = 20) have wide intervals. The 3-cone row is underpowered (r = 0.748, p = 0.094, n = 7).

## Exploratory: man and zone among cornerbacks

Outside the family of six. Players are `nfl_position == CB`. The split is the corner's `coverage_assignment`. `team_coverage_man_zone` is an agreement audit only. Tokens that name both man and zone, or neither, stay out. Shrinkage is empirical Bayes (beta-binomial for completion rate, normal-normal for EPA and separation, DerSimonian-Laird tau^2). The floor is 5 targets in that coverage. Aggregates only: no corner is named.

Forty-two cornerbacks, 660 targets (358 man, 301 zone, 1 other). Agreement with the team shell is 87.9% (579 of 659). The floor is met by 28 corners in man, 23 in zone, and 18 in both.

Man EPA is partial pooling (tau^2 = 0.149). Zone EPA is complete pooling (tau^2 = 0) on all 39 zone rows, so every zone row shares one shrunk EPA, 0.164, with interval [-0.015, 0.343]. Between-corner zone differences remain in the raw means. Separation stays partial in both coverages. No corner's shrunk-EPA interval lies entirely on one side of zero.

## Exploratory: completion on a credited target

Outside the family of six. The outcome is `pass_result` C. The model is L2-penalized logistic regression with a player intercept. Slopes are log-odds per 1 SD. Features stop at `pass_forward`: separation, closing speed, hip error, motion error, speed, acceleration magnitude, and speed change over about 0.5 s, plus wing span, broad jump, and vertical. Lambda is 1.0, from player-grouped cross-validation. Intervals are a 200-draw cluster bootstrap (seed 2027).

Of 660 credited targets, 486 are complete (174 dropped) on 32 cornerbacks. The completion rate is 53.7% (261 of 486). Grouped CV beats an intercept-only model by a small margin: Brier 0.239 against 0.250, log loss 0.678 against 0.694, ECE 0.064. The tails are off. Bin 1 (n = 49) predicts 0.21 and observes 0.45. Bin 10 (n = 48) predicts 0.85 and observes 0.73.

Three intervals exclude zero: separation at the throw +0.62 [0.41, 0.89], closing speed -0.31 [-0.61, -0.05], CB acceleration +0.28 [0.03, 0.58]. Wing span, broad jump, vertical, hip error, motion error, speed, and speed change all cross zero. Those Combine body measures add no detectable signal beyond the tracking features in this fit.

**Figure 3.** Placeholder. The notebook section "Exploratory figures" draws this at runtime; the repo stores no image. Panel A is `figure_cb_coverage`: shrunk EPA in man (blue) and zone (orange) for corners at the five-target floor, with the plugged-in 95% interval. One point per player, so it stays in the notebook. Panel B is `figure_threat_effects`: the log-odds forest above, intercept omitted.

## What a team could use

If retention holds on a new class, it is cheap to compute from tracking teams already have, and it is a film tiebreaker for DBs who already break quickly. The threat model points the same way: geometry and closing speed at the throw move completion probability, and the Combine body measures in the model do not.

## Limitations

- Small n. The lead is 26 players. Without 2025 (n = 19) and at 10 targets (n = 14) the interval crosses zero. Without 2024 (n = 15, p = 0.0097) it misses 0.05/6. The cornerback cut (n = 20) moves the same way when 2025 is dropped.
- Multiple comparisons. Six tests share one threshold, and A1-A6 were written after the first run. Only retention clears it. The cornerback filter, man/zone shrinkage, and the threat model are exploratory.
- Zone EPA is completely pooled (tau^2 = 0). Shrunk zone EPA does not separate corners, and no shrunk-EPA interval lies entirely above or below zero.
- Threat-model probabilities are miscalibrated in the tails (bin 1: 0.21 predicted, 0.45 observed; bin 10: 0.85 against 0.73).
- Only draftees are tracked, so a credited DB is an assigned draftee near the target, not a charted primary defender. Opponent, scheme, throw quality, drops, and injury are unadjusted. Shrinkage intervals treat the prior as known.
- The break is a definition, not an official NGS event, and 2024 recordings are shorter.

## Reproducibility

The notebook calls `bdb2027.pipeline.run_analysis` on `/kaggle/input/nfl-big-data-bowl-2027/` and rebuilds Tables 1-3 and Figures 1-2. Figure 3 comes from `run_cb_exploratory` in "Exploratory cornerbacks" and is still a placeholder here. Definitions and amendments are in `src/bdb2027/preregistration.py`.

<!-- SUBMISSION END -->

## Part B. Author notes (not submitted)

### Rules reminders

- At or under 2,000 words, fewer than 10 tables or figures, attached public notebook. Part A has 3 tables and 3 figures.
- The write-up has to use Combine tracking and link it to regular-season performance. Both gates rest on the backpedal drill series and regular-season `player_play` outcomes.
- Do not attach or quote row-level competition data. Tables 1-3 are aggregates. Figure 3 panel A is one point per player and stays inside the notebook.
- Optional external benchmark (Madden or other ratings): include it only if the source is public and free for every participant, or meets the host's Reasonableness Standard (Rules section 2.6). It is off by default (`--enable-external-benchmark`), it is not part of the family, and it would cost a figure.

### Exploratory cornerbacks

`src/bdb2027/cb_coverage.py` and `src/bdb2027/threat.py` are not part of the pre-registered family. Part A now reports the aggregate results from the 2026-11-25 run and labels them exploratory. It does not name corners and it does not rank them.

The DB tests still pool CB, SS, FS, DB, and S. The exploratory pass keeps `nfl_position == CB`. Man versus zone uses the corner's `coverage_assignment`. `team_coverage_man_zone` is the shell for every defender on the play, so it is an agreement audit only. Strings that are neither man nor zone stay out of the rows. Each CB-coverage cell has a raw mean (`mean_epa`) and an empirical-Bayes interval (beta-binomial for completion rate, normal-normal for EPA and separation). When DerSimonian-Laird tau^2 is 0, `epa_pooling` is `complete` and every CB in that coverage shares one shrunk EPA. On this run, man EPA is partial (tau^2 = 0.149) and zone EPA is complete (tau^2 = 0, 39 zone rows, shared shrunk EPA 0.164, interval [-0.015, 0.343]). Separation stays partial in both. The floor is 5 credited targets in that coverage. The figure is `figure_cb_coverage` (Figure 3, panel A).

The cornerback-only retention correlation (r = -0.640, n = 20) is a position filter of the 26-player lead (20 CB and 6 SS). It is not a row in `effects_robustness.csv`, and the notebook's robustness table does not print it. Safeties alone were too few. Year drops for that filter: without 2024, r = -0.766, p = 0.013, n = 10; without 2025, r = -0.384, the interval crosses zero, p = 0.18, n = 15.

A threat is a completion on the credited target. The model is penalized logistic regression with a player intercept, using pre-throw tracking (speed, acceleration magnitude, hip and motion error relative to the receiver, closing speed, speed change over 0.5 s) plus wing span, broad jump, and vertical. Frames after `pass_forward`, and post-outcome event names, are dropped. Run it with `--cb-exploratory`. The player-level coverage table (`effects_cb_coverage.csv`) is not for the write-up or for git. Read `README.md` for the file list, the label map, and the limits.

### Before submitting

1. Part A matches the 2026-11-25 re-run (`main` `9a8b9eb`, command above). Re-run again if the code or the files change, and replace every number.
2. Cushion check done (2026-11-15, same p-values on the 2026-11-25 re-run): weak support only (p = 0.18 to 0.35). Part A reports the gaps from `effects_cushion.csv`.
3. If a later class or holdout becomes available, test retention -> EPA there first. That is the validation this lead needs.
4. Figures 1 and 2 are drawn at runtime by `bdb2027.figures` in the notebook. Figure 3 is the exploratory pair (`figure_cb_coverage`, `figure_threat_effects`), also drawn at runtime. Do not commit exported images. Figure 1 and Figure 3 panel A have one point per player. Do not add a chart that does not change the claim, and do not paste the per-CB coverage table into Part A.

### Amendments and results history

Dated 2026-11-15, after the first run on the competition files. State in the write-up that these came after seeing the first results, and show both runs. The definitions are in `src/bdb2027/preregistration.py`.

| ID | Change | Why |
| --- | --- | --- |
| A1 | Outcomes use only games with `season_type` `REG`. | `games.csv` has 49 PRE, 272 REG, and 13 POST games per season, although the data page lists only REG and POST. The theme and the linkage gate say regular-season performance. About 20% of targets were in PRE or POST games. |
| A2 | DB coverage credit uses `coverage_assignment`. A draftee DB is credited with a target when the targeted receiver is a tracked draftee, the DB is on the other team with an active `coverage_assignment` (not missing, not `NO_ASSIGNMENT`), and at `pass_forward` he is the closest such DB to the receiver and within 5 yards. Separation allowed is the receiver's `separation_at_pass_forward`. | Game tracking holds only the 510 draftees, about 3 tracked players per `pass_forward` frame. The original "nearest tracked DB" was a median 12.6 yards from the target and usually not the covering defender. |
| A3 | A break is only searched for in the first 5.5 s of each drill attempt, in every class. DB results are also reported without the 2024 class. | 2024 `BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION` attempts end after 5.3 to 6.6 s. 2023 attempts last about 11.7 s and 2025 about 10.2 s. Without a cap, later breaks could only be found outside 2024. |
| A4 | Fisher standard error is `1 / sqrt(n - 3 - (k - 1))` for `k` draft classes. | Removing `k` class means costs `k - 1` degrees of freedom beyond an ordinary Pearson correlation. |
| A5 | `te_secondary_three_cone_completion` is flagged `underpowered`. It stays in the family of 6 and in the Bonferroni count. | Only 7 tight ends in 2 classes have a 3-cone time and at least 5 regular-season targets. |
| A6 | Backpedal attempts with no break in the first 5.5 s are kept, not dropped. If the athlete moved and the recording lasted at least 5.0 s, the attempt is censored at 5.5 s (`break_censored`), which ranks it slowest. The two DB break-time tests become a pooled within-class Spearman correlation (ranks inside each class, average ranks for ties, then demeaned), with Fisher variance `1.06 / (n - 3 - (k - 1))`. Speed retention is only defined at a break, so the retention test keeps only attempts with a detected break and stays Pearson. Every row now reports `p_value`, and the break rows report `n_censored`. | Under A3 alone, only 70 of 241 backpedal attempts kept a break time. Censoring keeps all 241 and keeps the information that the player had not broken by 5.5 s. |

Results, both runs. Pooled within-class Pearson r, 95% Fisher interval, n players.

| Test | Original (all game types, nearest DB, no cap, n - 3) | Amended (A1-A5) | Amended, DB without 2024 |
| --- | --- | --- | --- |
| te_primary_decel_separation | 0.166 [-0.213, 0.502], n 29 | 0.164 [-0.300, 0.566], n 22 | |
| te_secondary_ten_yd_separation | 0.006 [-0.398, 0.409], n 24 | 0.084 [-0.398, 0.530], n 20 | |
| te_secondary_three_cone_completion (underpowered) | 0.063 [-0.506, 0.593], n 13 | 0.748 [-0.163, 0.970], n 7 | |
| db_primary_break_separation | -0.080 [-0.289, 0.137], n 84 | -0.130 [-0.507, 0.288], n 26 | -0.301 [-0.717, 0.273], n 15 |
| db_secondary_retention_epa | 0.217 [-0.003, 0.417], n 80 | -0.596 [-0.806, -0.253], n 26 | -0.652 [-0.879, -0.186], n 15 |
| db_secondary_break_completion | -0.012 [-0.226, 0.203], n 84 | -0.277 [-0.612, 0.143], n 26 | -0.251 [-0.690, 0.323], n 15 |

After amendment A6 (censoring and Spearman for the two break-time rows; the other four rows do not change). The 2026-11-25 re-run reproduced this block.

| Test | Method | r | 95% interval | p | n (censored) |
| --- | --- | --- | --- | --- | --- |
| db_primary_break_separation | Spearman | -0.019 | [-0.319, 0.285] | 0.907 | 47 (21) |
| db_secondary_retention_epa | Pearson | -0.596 | [-0.806, -0.253] | 0.00166 | 26 (0) |
| db_secondary_break_completion | Spearman | 0.222 | [-0.085, 0.491] | 0.155 | 47 (21) |
| Without 2024: db_primary_break_separation | Spearman | -0.134 | [-0.527, 0.306] | 0.558 | 24 (9) |
| Without 2024: db_secondary_retention_epa | Pearson | -0.652 | [-0.879, -0.186] | 0.0097 | 15 (0) |
| Without 2024: db_secondary_break_completion | Spearman | 0.351 | [-0.084, 0.674] | 0.111 | 24 (9) |

The completion row is positive, which is the opposite of the expected negative sign: quicker breakers allowed slightly more completions. Its interval covers zero.

Only `db_secondary_retention_epa` clears the Bonferroni threshold of 0.05 / 6 (two-sided p = 0.00166 on the amended run). It is a secondary test, its sign flipped between the original run and the amended run, and the amendments came after the first run. Present it as a lead to check on a later class. Without the break cap (A1, A2, A4 only) the same test gives -0.428 [-0.663, -0.116] with n 38.

Exploratory aggregates from the same 2026-11-25 run, for Part A. The player-level coverage file stays out of git.

- Coverage: 42 CBs, 660 targets (358 man, 301 zone, 1 other), agreement 579/659 = 0.879, floor 28 man / 23 zone / 18 both. Man EPA tau^2 = 0.149 (partial). Zone EPA tau^2 = 0 (complete, 39 rows).
- Threat: 486 complete matchups, 32 CBs, 261 completions (rate 0.537), lambda 1.0, grouped-player CV, 200 bootstrap draws. Brier 0.239 vs 0.250. Log loss 0.678 vs 0.694. ECE 0.064. Bin 1: predicted 0.208, observed 0.449. Bin 10: predicted 0.845, observed 0.729. Intervals excluding zero: separation_at_throw 0.617 [0.411, 0.894], closing_speed -0.313 [-0.608, -0.047], cb_accel 0.285 [0.031, 0.581].
