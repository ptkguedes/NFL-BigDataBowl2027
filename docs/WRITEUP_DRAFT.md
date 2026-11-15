# Write-up draft

This file has two parts. Part A, between the `SUBMISSION START` and `SUBMISSION END` markers, is the draft text for the Kaggle write-up. `tests/test_writeup.py` checks that it stays at or under 2,000 words and under 10 tables and figures. Part B is author notes, which are not submitted. Numbers come from the local run of `python -m bdb2027 --data-dir data --robustness --scenarios` on the competition files (amendments A1-A6, 2026-11-15). Re-run before submitting and update every number.

Track to select at submission: Open or University. University only if every member is an undergraduate. Leave the Grand Prize track empty unless that changes.

<!-- SUBMISSION START -->

# Holding speed through the break: Combine backpedal tracking and EPA allowed by rookie defensive backs

*A finding that came after the amendments and still needs validation, with honest nulls for break time and tight ends.*

## Summary

We linked 10 Hz Combine tracking to regular-season NFL coverage for the 2023-2025 draft classes. One measure stood out. Defensive backs who kept more of their speed through the 45-degree break in the backpedal drill allowed less offensive EPA per credited target. The pooled within-class correlation is r = -0.60 (95% interval -0.81 to -0.25, p = 0.002, n = 26 players in 3 classes). It holds without the 2024 class, whose drill recordings are cut short (r = -0.65, n = 15).

This is a lead to validate, not a settled result. It is a secondary test in a pre-registered family of six. It only appeared after we amended the definitions once we had seen the first run, and the sample is small. Time to the break, the measure we expected to matter, shows no link to separation allowed. The tight-end tests are weak.

## Data

We used the nine competition files. Game tracking and `player_play.csv` cover only the 510 draftees, about three tracked players per throw. Outcomes use regular-season games only (`season_type` REG). Plays nullified by penalty are dropped. Comparisons are always made inside a draft class, because Combine recording differs by year. The clearest case is the 2024 backpedal drill: its attempts end after about 6 seconds, against 10 to 12 seconds in 2023 and 2025.

## Measures

**Break.** Breaks are not labeled in the Combine file. We define the break as the first frame, after the athlete passes 1 yd/s, where his direction of travel has turned 45 degrees from his opening heading. We look only in the first 5.5 seconds of each attempt, in every year, so that 2024 is not penalized. An attempt with no break by 5.5 seconds is censored at 5.5 seconds and ranks slowest. A player's value is the median over his attempts.

**Speed retention.** This is median speed in the 0.3 seconds after the break divided by median speed in the 0.3 seconds before it. It exists only for detected breaks.

**Coverage credit.** A targeted draftee receiver is credited to the closest opposing draftee DB who has an active `coverage_assignment` on that play, if that DB is within 5 yards at `pass_forward`. Each credited target carries the play's EPA, completion, and the receiver's `separation_at_pass_forward`. A DB enters the tests with at least 5 credited targets.

## Method

Inside each draft class we demean the predictor and the outcome, then correlate the deviations. The two break-time tests rank both variables inside the class first (a pooled within-class Spearman), so censored players tie at the slowest rank. Intervals are Fisher intervals that spend one degree of freedom per class mean removed. The Spearman rows use the 1.06 variance factor. The family has six tests with a Bonferroni threshold of 0.05/6 = 0.0083. Table 1 reports all six.

**Table 1. Pre-registered family after amendments A1-A6.** Expected sign is for "more of the trait".

| Test | Method | r | 95% interval | p | n |
| --- | --- | --- | --- | --- | --- |
| TE: harder brake on TE drills -> separation | Pearson | 0.16 | -0.30, 0.57 | 0.49 | 22 |
| TE: faster 10-yard split -> separation | Pearson | 0.08 | -0.40, 0.53 | 0.74 | 20 |
| TE: faster 3-cone -> completion rate (underpowered) | Pearson | 0.75 | -0.16, 0.97 | 0.09 | 7 |
| DB: quicker break -> separation allowed | Spearman | -0.02 | -0.32, 0.28 | 0.91 | 47 |
| DB: more speed retention -> EPA allowed | Pearson | -0.60 | -0.81, -0.25 | 0.002 | 26 |
| DB: quicker break -> completion rate allowed | Spearman | 0.22 | -0.09, 0.49 | 0.16 | 47 |

## Defensive backs: speed retention and EPA allowed

**Figure 1.** Within-class deviations of speed retention against EPA allowed per credited target, one point per DB, colored by draft class.

Rookie DBs who came out of the break closer to their entry speed gave up less EPA when targeted. Table 2 checks how fragile that is. None of these checks were pre-registered.

**Table 2. Robustness of the retention -> EPA row.**

| Check | r | Interval | n |
| --- | --- | --- | --- |
| Main row | -0.60 | -0.81, -0.25 | 26 |
| Within-class Spearman | -0.54 | -0.78, -0.17 | 26 |
| Without 2023 | -0.65 | -0.86, -0.25 | 18 |
| Without 2024 | -0.65 | -0.88, -0.19 | 15 |
| Without 2025 | -0.41 | -0.74, 0.07 | 19 |
| Bootstrap within class (2,000 draws) | -0.60 | -0.86, -0.29 | 26 |
| Range when any one player is removed | -0.71 to -0.52 | | 26 |
| At least 10 credited targets | -0.43 | -0.79, 0.16 | 14 |
| Man-coverage targets only | -0.65 | -0.85, -0.29 | 22 |
| Zone targets only | -0.26 | -0.62, 0.19 | 23 |

The sign never flips, and no single player drives it. The weak points are just as clear. Dropping 2025 or raising the target floor widens the interval across zero. Most of the association sits in man coverage, where the credited DB is most likely the real coverage defender and where carrying speed through a break should matter most. That is a reading, not a test.

## Probabilities and scenarios

To make the lead concrete, we resampled players within each class 4,000 times. That gives a bootstrap approximation to a posterior with a flat prior. In each draw we fitted the within-class slope of EPA allowed per target on retention. We then compared two profiles taken from the observed data: a DB at the 75th percentile of within-class retention (raw retention about 1.10) and one at the 25th percentile (about 1.04). A "season" assumes 60 targets in coverage, roughly a full-time starter. That volume is an assumption, not a count from these files, which only credit draftee-on-draftee targets (median 5 per DB-season). Bands are 90%.

**Table 3. Retention scenarios (bootstrap posterior, 90% bands).**

| Quantity | All targets (n 26) | Man only (n 22) | Zone only (n 23) |
| --- | --- | --- | --- |
| P(slope below zero) | 1.00 | 1.00 | 0.92 |
| P(75th-percentile DB allows less EPA/target than his class median) | 0.68 (0.56-0.84) | 0.69 (0.54-0.85) | 0.58 (0.44-0.75) |
| P(25th-percentile DB allows less EPA/target than his class median) | 0.34 (0.16-0.48) | 0.25 (0.09-0.43) | 0.43 (0.31-0.55) |
| EPA/target, high minus low retention | -0.32 (-0.49 to -0.18) | -0.59 (-0.95 to -0.22) | -0.18 (-0.44 to 0.02) |
| EPA per 60-target season, high minus low | -19 (-29 to -11) | -36 (-57 to -13) | -11 (-26 to 1) |

Read the probabilities rather than the season totals. A high-retention rookie beats his class median about two times in three, and a low-retention rookie about one time in three. The season-scale gap is large by NFL standards, and it is almost certainly an upper bound. Per-DB EPA means rest on about 15 credited targets each, nothing is shrunk, and the lead was found after amendments, so the effect should be expected to shrink on new players. At the observed credited volume the gap is -1.6 EPA per season (-2.4 to -0.9).

## Defensive backs: time to the break

Quicker breaks do not go with less separation allowed (Spearman -0.02). They also do not go with fewer completions allowed. That row has the opposite sign to what we expected (0.22, interval -0.09 to 0.49).

For scouting, the ordering that matters is among players who broke inside 5.5 seconds. The drill cannot separate the rest from each other, so we treat them as context. In the break tests, 21 of 47 DBs had a median attempt with no break by 5.5 seconds. Those slow breakers allowed a 52.6% completion rate on credited targets, against 61.0% for the 26 faster breakers, with similar separation (2.46 against 2.39 yards). One possible reading was that slow breakers line up deeper, so the throws credited to them are harder ones. Pre-snap `cushion` gives only weak support. Within class, slow breakers lined up 0.57 yards deeper on credited targets (6.2 against 5.6 yards, permutation p = 0.18) and 0.45 yards deeper over all snaps (p = 0.27). The group also has more safeties (38% against 23%, p = 0.35). Depth may contribute, but it does not explain the completion gap, and we make no claim that it does.

**Figure 2.** 95% intervals for all six family tests and the Table 2 checks, in one forest plot.

## Tight ends

The TE tests are weak. TE-drill braking and the 10-yard split show small positive correlations with separation when targeted, with intervals wide enough to include a moderate effect in either direction. The 3-cone test has only seven players with a time and enough targets, so we report it without reading anything into it.

## What a team could use

If speed retention through a backpedal break holds in new draft classes, it is cheap to compute from data teams already have. It points at something that stopwatch drills cannot see: how much speed a defender gives up when he changes direction, rather than how fast he can change direction. At this sample size it is a tiebreaker for film study of DBs who already break quickly, not a ranking tool.

## Limitations

- Small samples, six related tests, and amendments made after the first run.
- Only draftees are tracked, so many coverage snaps are invisible and a credited DB is "an assigned draftee near the target", not a charted primary defender.
- Observational. Opponent, scheme, role, and injury are not adjusted for.
- The break is a reproducible definition, not an official NGS event, and 2024 recordings are shorter.

## Reproducibility

The public Kaggle notebook calls `bdb2027.pipeline.run_analysis` on `/kaggle/input/nfl-big-data-bowl-2027/` and rebuilds Tables 1-3 and Figures 1-2 at runtime. All definitions and dated amendments are in `src/bdb2027/preregistration.py`.

<!-- SUBMISSION END -->

## Part B. Author notes (not submitted)

### Rules reminders

- At or under 2,000 words, fewer than 10 tables or figures, attached public notebook. Part A has 3 tables and 2 figures.
- The write-up has to use Combine tracking and link it to regular-season performance. Both gates rest on the backpedal drill series and regular-season `player_play` outcomes.
- Do not attach or quote row-level competition data. Tables 1-2 are aggregates.
- Optional external benchmark (Madden or other ratings): include it only if the source is public and free for every participant, or meets the host's Reasonableness Standard (Rules section 2.6). It is off by default (`--enable-external-benchmark`), it is not part of the family, and it would cost a figure.

### Before submitting

1. Re-run with `--robustness --scenarios` and replace every number in Part A.
2. Cushion check done (2026-11-15): weak support only (p = 0.18 to 0.35), so Part A now reports it as "may contribute, does not explain". Drop the sentence if a re-run moves it further from significance.
3. If a later class or holdout becomes available, test retention -> EPA there first. That is the validation this lead needs.
4. Figures 1 and 2 are drawn at runtime by `bdb2027.figures` in the notebook. Do not commit exported images. Figure 1 has one point per player. Do not add a chart that does not change the claim.

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

After amendment A6 (censoring and Spearman for the two break-time rows; the other four rows do not change):

| Test | Method | r | 95% interval | p | n (censored) |
| --- | --- | --- | --- | --- | --- |
| db_primary_break_separation | Spearman | -0.019 | [-0.319, 0.285] | 0.91 | 47 (21) |
| db_secondary_retention_epa | Pearson | -0.596 | [-0.806, -0.253] | 0.002 | 26 (0) |
| db_secondary_break_completion | Spearman | 0.222 | [-0.085, 0.491] | 0.16 | 47 (21) |
| Without 2024: db_primary_break_separation | Spearman | -0.134 | [-0.527, 0.306] | 0.56 | 24 (9) |
| Without 2024: db_secondary_retention_epa | Pearson | -0.652 | [-0.879, -0.186] | 0.010 | 15 (0) |
| Without 2024: db_secondary_break_completion | Spearman | 0.351 | [-0.084, 0.674] | 0.11 | 24 (9) |

The completion row is positive, which is the opposite of the expected negative sign: quicker breakers allowed slightly more completions. Its interval covers zero.

Only `db_secondary_retention_epa` clears the Bonferroni threshold of 0.05 / 6 (two-sided p about 0.002 on the amended run). It is a secondary test, its sign flipped between the two runs, and the amendments came after the first run. Present it as a lead to check, not a finding. Without the break cap (A1, A2, A4 only) the same test gives -0.428 [-0.663, -0.116] with n 38.
