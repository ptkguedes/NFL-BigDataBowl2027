# Write-up draft

This file has two parts. Part A, between the `SUBMISSION START` and `SUBMISSION END` markers, is the draft text for the Kaggle write-up. `tests/test_writeup.py` checks that it stays at or under 2,000 words and under 10 tables and figures. Part B is author notes, which are not submitted.

Numbers in Part A match the 2026-11-25 re-run on `main` at `9a8b9eb`:

`python -m bdb2027 --data-dir data --output outputs/effects.csv --robustness --scenarios --cb-exploratory`

That run confirmed the 2026-11-15 family, robustness, and scenario tables (amendments A1-A6) and fit the exploratory cornerback sections. Re-run before submitting and update every number. Do not commit the output CSVs, and do not add a per-player table.

The track choice is in Part B.

<!-- SUBMISSION START -->

# Holding speed through the break

*The back who comes out of the turn still fast gives up less offense. That is the one pre-registered result that passes a strict correction for running six tests. How fast he gets to the break does not.*

## The finding

We linked 10 Hz Combine tracking to regular-season coverage for the 2023-2025 draft classes. For each defensive back we took speed in the 0.3 seconds after the 45-degree break in the backpedal drill and divided by speed in the 0.3 seconds before it.

A ratio of 1.10 means he comes out of the turn 10% faster than he went in. A ratio of 1.04 means 4% faster. Those are the top and bottom quarters of a draft class (75th and 25th percentile). On the field, 1.10 is the corner who stays in phase with the receiver at the break. 1.04 is the corner who gives up a step.

The outcome is expected points added (EPA): the change in the offense's expected points on the play. A target is credited to the closest opposing draftee who has a coverage assignment, if he is within 5 yards when the ball is thrown. Inside each draft class, more speed kept through the break goes with less EPA allowed. The correlation is r = -0.596 (95% interval -0.806 to -0.253, p = 0.00166, 26 backs: 8 in 2023, 11 in 2024, 7 in 2025).

The high-retention back allows 0.32 fewer expected points per credited target than the low-retention back (interval -0.49 to -0.18). Over an assumed 60 targets, a full starter's year, that is about 19 expected points (interval -29 to -11), roughly three touchdowns' worth. These files only credit draftee-on-draftee throws, a median of 5 per back, and at that volume the gap is 1.6 expected points. Treat 19 as an upper bound. It should shrink on a new class.

The gap is a man-coverage result. In man it is 0.59 expected points per target, about 36 over 60 targets. In zone it is 0.18 per target and the interval includes no difference.

A high-retention rookie beats his class median about two times in three (probability 0.68). A low-retention rookie does so about one time in three (0.34).

This was one of six tests written down in advance, and the only one that passes a strict correction for running all six (the bar is 0.05 divided by 6). The definitions were rewritten after the first look at the data, and 26 players is a small sample. It is a lead to check on the next class.

**Figure 1.** Placeholder, drawn in the notebook and not stored here. One point per back: speed kept through the break against EPA allowed, after removing the draft-class average.

## The other five tests

Comparisons are made inside a draft class, because the Combine tapes differ by year. The 2024 backpedal file ends after about 6 seconds. The 2023 and 2025 files run 10 to 12 seconds. A break is the first frame, after the athlete passes 1 yard per second, where his direction has turned 45 degrees. The search stops at 5.5 seconds in every year. Players who never break by then, 21 of 47 on the break tests, tie at the slow end. Those two tests use ranks for that reason. The other tests use the values themselves. A back needs at least 5 credited targets to enter. Plays wiped out by penalty are dropped, and only regular-season games count.

**Table 1. Six pre-registered tests.** "Passes" means the p-value is under 0.05/6.

| Test | r | 95% interval | p | Players | Passes |
| --- | --- | --- | --- | --- | --- |
| TE: harder brake -> separation | 0.164 | -0.300, 0.566 | 0.495 | 22 | No |
| TE: faster 10-yard split -> separation | 0.084 | -0.398, 0.530 | 0.744 | 20 | No |
| TE: faster 3-cone -> completion (7 players) | 0.748 | -0.163, 0.970 | 0.094 | 7 | No |
| DB: quicker break -> separation allowed | -0.019 | -0.319, 0.285 | 0.907 | 47 | No |
| DB: speed through the break -> EPA allowed | -0.596 | -0.806, -0.253 | 0.00166 | 26 | Yes |
| DB: quicker break -> completion rate allowed | 0.222 | -0.085, 0.491 | 0.155 | 47 | No |

Quicker breaks do not bring tighter coverage, and they do not bring fewer completions. The completion row points the other way. The tight-end tests miss the bar. The 3-cone row is too small to read.

## How fragile the lead is

**Table 2. Retention against EPA allowed, under a few cuts.** The notebook has the other checks, including dropping any one player.

| Check | r | 95% interval | Players |
| --- | --- | --- | --- |
| Main result | -0.596 | -0.806, -0.253 | 26 |
| Drop 2023 | -0.650 | -0.862, -0.247 | 18 |
| Drop 2024 | -0.652 | -0.879, -0.186 | 15 |
| Drop 2025 | -0.414 | -0.738, 0.065 | 19 |
| At least 10 credited targets | -0.431 | -0.794, 0.157 | 14 |
| Man targets | -0.647 | -0.847, -0.286 | 22 |
| Zone targets | -0.261 | -0.622, 0.193 | 23 |

Dropping 2024 still excludes zero, but p = 0.0097 misses the six-test bar (15 players). Dropping 2025, and requiring 10 targets, the interval includes zero. Man means an exact man tag and at least 3 targets. Zone means every other tag. Dropping any one player does not flip the sign.

Twenty of the 26 backs are cornerbacks, and six are safeties. Among cornerbacks alone the correlation is r = -0.640 (interval -0.852 to -0.246, p = 0.0033, 20 players). The safeties are too few to estimate on their own.

**Table 3. High retention (about 1.10) minus low retention (about 1.04).** Negative means the high-retention back allows fewer expected points. Ranges are 90%. Sixty targets is an assumed starter year, not a count from these files.

| | All (26) | Man (22) | Zone (23) |
| --- | --- | --- | --- |
| Expected points per target | -0.32 (-0.49 to -0.18) | -0.59 (-0.95 to -0.22) | -0.18 (-0.44 to 0.02) |
| Expected points over 60 targets | -19 (-29 to -11) | -36 (-57 to -13) | -11 (-26 to 1) |

**Figure 2.** Placeholder, drawn in the notebook. Intervals for the six tests and for every retention check, including the ones left out of Table 2.

Backs who never break by 5.5 seconds line up about half a yard deeper (0.57 yards on credited targets, 6.2 against 5.6, p = 0.18; 0.45 yards on all snaps, p = 0.27). More of them are safeties (38% against 23%, p = 0.35). That is weak support, not an explanation.

## Exploratory: man and zone

This was not one of the six tests. It keeps cornerbacks only and splits on the corner's own assignment. That label agrees with the team shell on 87.9% of throws (579 of 659). There are 42 corners and 660 targets: 358 man, 301 zone, and 1 other.

When a corner has few targets, his average is pulled toward the group so one noisy game does not dominate. In man, corners still differ after that pull. In zone, the pull is complete: every corner gets the same adjusted EPA, 0.16, and the differences that remain are the raw averages. No corner's range sits entirely on one side of zero. Do not rank zone corners from the adjusted number.

## Exploratory: what changes a completion

This was not one of the six tests. On 486 throws to 32 corners with a full look at the release, 53.7% were completed (261 of 486). The model uses only what is known when the ball comes out: the gap, whether that gap is closing, the corner's speed and acceleration, and his wing span, broad jump, and vertical. A "typical" change below is one standard deviation in this sample, turned into percentage points of completion probability. The ranges resample corners.

The average gap at the throw is 2.5 yards. A typical extra 1.3 yards of separation raises the chance the pass is completed by about 13 points (9 to 16). Spread across those 1.3 yards, that is about 10 points per extra yard.

Closing the gap faster by a typical amount, 2.3 yards per second (about 4.6 mph), lowers the completion chance by about 7 points (1 to 12). That is about 3 points per extra yard per second of closing speed.

A typical increase in the corner's acceleration at the throw raises the completion chance by about 6 points (1 to 11). The tracking file does not give that acceleration a coaching unit beyond the recorded magnitude, so this one stays as a typical change, not a per-yard figure.

Wing span, broad jump, vertical, hip angle, path angle, speed, and the change in speed over the previous half-second all have ranges that include no effect. Once the throw is on tape, those Combine measurables do not add a completion signal.

The model is only a little sharper than guessing the overall 54% completion rate. It is off at the extremes: throws it calls unlikely are completed much more often than it expects, and throws it calls likely are completed a bit less often. The bin-by-bin check is in the notebook. Do not use the raw probabilities as odds.

**Figure 3.** Placeholder, drawn in the notebook and not stored here. One panel is adjusted EPA in man and in zone, one point per corner, so it stays in the notebook. The other panel is the completion effects above.

## What a team could use

Use this as a tiebreaker, not as a draft board.

A scout can compute it from tracking the club already gets at the Combine or a pro day. On the backpedal-to-break drill, divide speed out of the turn by speed into the turn. When two corners both break quickly on film and the rest of the card is close, prefer the one who comes out of the plant still fast: about 10% faster than he went in, rather than about 4%. Do not sort a class on this number alone. The sample is 26 rookies, the definitions were set after a first look, and the result weakens if the 2025 class is set aside or if only backs with 10 or more credited targets are kept.

A DB coach should train the turn, not only the stopwatch to the plant. The backs who hold speed through the break give up less offense, and in man that is about 0.6 expected points per target. The rep is to stay in phase at the stem break so the receiver does not get a step. The same idea shows up when the ball is released. An extra yard of separation at the throw is worth about 10 completion points here, and a corner who is closing that gap takes completions off the board. A longer wing span, a better broad jump, or a better vertical does not, once the tracking at the throw is known.

A coordinator should weight this more in a man-heavy plan than in a zone plan. The retention result is clear on man targets and unclear on zone targets. In zone, these corners do not separate from each other once noisy averages are pulled together.

Prefer it for corners. Twenty of the 26 backs in the lead are corners, and the corner-only result is essentially the same correlation. There are not enough safeties here to say the drill means the same thing for them.

## Limits

- The lead is 26 players. Drop 2025, or require 10 credited targets, and the interval includes no effect. Dropping 2024 still points the same way but misses the six-test bar.
- Six tests shared one correction, and the definitions changed after the first run. Only speed through the break passes. The man-versus-zone look and the completion model were not in those six.
- In zone, the adjusted EPA does not separate corners. No corner's range sits entirely above or below zero.
- The completion probabilities are off at the extremes.
- Only draftees are tracked. The credited back is the closest assigned draftee within 5 yards, not a charted primary defender. Opponent, scheme, throw quality, and drops are not adjusted.
- The break is our definition, not an official event, and the 2024 drill tapes are short.

The notebook rebuilds the tables and figures. The checks left out of Table 2, the full scenario ranges, and the calibration bins are there.

<!-- SUBMISSION END -->

## Part B. Author notes (not submitted)

### Rules reminders

- Track: University, solo author. Leave the Grand Prize track empty.
- At or under 2,000 words, fewer than 10 tables or figures, attached public notebook. Part A has 3 tables and 3 figures.
- The write-up has to use Combine tracking and link it to regular-season performance. Both gates rest on the backpedal drill series and regular-season `player_play` outcomes.
- Do not attach or quote row-level competition data. Tables 1-3 are aggregates. Figure 3 panel A is one point per player and stays inside the notebook.
- Optional external benchmark (Madden or other ratings): include it only if the source is public and free for every participant, or meets the host's Reasonableness Standard (Rules section 2.6). It is off by default (`--enable-external-benchmark`), it is not part of the family, and it would cost a figure.

### Exploratory cornerbacks

`src/bdb2027/cb_coverage.py` and `src/bdb2027/threat.py` are not part of the pre-registered family. Part A now reports the aggregate results from the 2026-11-25 run and labels them exploratory. It does not name corners and it does not rank them.

The DB tests still pool CB, SS, FS, DB, and S. The exploratory pass keeps `nfl_position == CB`. Man versus zone uses the corner's `coverage_assignment`. `team_coverage_man_zone` is the shell for every defender on the play, so it is an agreement audit only. Strings that are neither man nor zone stay out of the rows. Each CB-coverage cell has a raw mean (`mean_epa`) and an empirical-Bayes interval (beta-binomial for completion rate, normal-normal for EPA and separation). When DerSimonian-Laird tau^2 is 0, `epa_pooling` is `complete` and every CB in that coverage shares one shrunk EPA. On this run, man EPA is partial (tau^2 = 0.149) and zone EPA is complete (tau^2 = 0, 39 zone rows, shared shrunk EPA 0.164, interval [-0.015, 0.343]). Separation stays partial in both. The floor is 5 credited targets in that coverage. The figure is `figure_cb_coverage` (Figure 3, panel A).

The cornerback-only retention correlation (r = -0.640, n = 20) is a position filter of the 26-player lead (20 CB and 6 SS). It is not a row in `effects_robustness.csv`, and the notebook's robustness table does not print it. Safeties alone were too few. Year drops for that filter: without 2024, r = -0.766, p = 0.013, n = 10; without 2025, r = -0.384, the interval crosses zero, p = 0.18, n = 15.

A threat is a completion on the credited target. The model is penalized logistic regression with a player intercept, using pre-throw tracking (speed, acceleration magnitude, hip and motion error relative to the receiver, closing speed, speed change over 0.5 s) plus wing span, broad jump, and vertical. Frames after `pass_forward`, and post-outcome event names, are dropped. Run it with `--cb-exploratory`. The player-level coverage table (`effects_cb_coverage.csv`) is not for the write-up or for git. Read `README.md` for the file list, the label map, and the limits.

### Detail moved out of Part A

Part A keeps the main retention row, the three year drops, the 10-target floor, and the man/zone split. The notebook prints the rest of `effects_robustness.csv`. Those rows, from the 2026-11-25 run:

- Within-class Spearman: r = -0.544, interval -0.782 to -0.168, n = 26.
- Bootstrap, 2,000 within-class resamples: r = -0.596, interval -0.861 to -0.292.
- Drop any one player: r stays between -0.707 and -0.521.

Fisher intervals use `1 / sqrt(n - 3 - (k - 1))` for k draft classes. The two break-time tests are within-class Spearman with variance factor 1.06, because attempts with no break by 5.5 s are censored and tied at the slowest rank. Scenario probabilities the write-up rounds to "two in three" and "one in three" are 0.681 (0.555 to 0.837) and 0.336 (0.163 to 0.480) for all targets. Man: 0.688 (0.538 to 0.854) and 0.246 (0.085 to 0.426). Zone: 0.578 (0.435 to 0.746) and 0.433 (0.305 to 0.547). P(slope below zero) is 1.000, 0.998, and 0.924. Observed-volume gap: -1.60 expected points (-2.44 to -0.88) at a median of 5 credited targets.

Completion-chance changes in Part A are `mean_risk_difference` from the threat effects file, the average change in predicted completion probability when that feature rises by 1 SD (`threat.py`, `_risk_difference`). Separation SD is 1.264 yards (mean 2.502), so 0.128 / 1.264 = 0.101, about 10 points per yard. Closing-speed SD is 2.268 yards per second, times 3600/1760 = 4.64 mph. The per-yard-per-second figure is -0.0674 / 2.268 = -0.030, about 3 points. Acceleration stays per 1 SD (0.060, interval 0.007 to 0.113) because the code names `a` as acceleration magnitude and does not convert it. Calibration bins stay in the notebook: bin 1 predicted 0.208 vs observed 0.449; bin 10 predicted 0.845 vs observed 0.729. Brier 0.239 vs 0.250. Log loss 0.678 vs 0.694. ECE 0.064.

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
