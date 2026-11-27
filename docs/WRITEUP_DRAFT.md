# Write-up draft

This file has two parts. Part A, between the `SUBMISSION START` and `SUBMISSION END` markers, is the draft text for the Kaggle write-up. `tests/test_writeup.py` checks that it stays at or under 2,000 words and under 10 tables and figures. Part B is author notes, which are not submitted.

Part A was rewritten on 2026-11-27 around a reliability lead. Numbers come from the aggregate scan of that date (attempt-to-attempt reliability, seven Combine-to-outcome candidates with a Holm correction, and a second-round check of the old defensive-back retention result). No per-player table belongs in the write-up or in git.

The track choice is in Part B.

<!-- SUBMISSION START -->

# Measure the instrument before the player

*At 10 pictures a second, Combine tracking repeats top speed and does not repeat the first step. A striking defensive-back correlation fails that test. The one link that holds is a stopwatch, not a new tracking trait.*

## What the chip can measure twice

Before asking whether a Combine number predicts a season, ask whether the same player produces it twice. Agreement here is the correlation of attempt 1 with attempt 2, after removing the draft-class average. A value of 1 means the second rep is the same answer. A value of 0 means the second rep is unrelated to the first. Most position drills are filmed once, so this check exists only where a player ran the drill twice: the 40 (375 pairs), the gauntlet (137), the offensive-line drop (118), the defensive-line pass-rush drill (106), the 45-degree backpedal (119), the defensive-back line drill (82), and the 3-cone and shuttle (about 40).

**Table 1. Attempt-to-attempt agreement for long-window speed.** Fed by the attempt-agreement file. Pairs are players with two usable reps.

| Measurement | Agreement | Pairs |
| --- | --- | --- |
| 40-yard dash, top speed | 0.99 | 375 |
| 40, flying 10-to-20 yard split | 0.98 | 375 |
| Gauntlet, top speed | 0.66 | 137 |
| Defensive-line pass-rush drill, top speed | 0.63 | 106 |
| Offensive-line drop, top speed | 0.54 | 118 |
| 45-degree backpedal, top speed | 0.52 | 119 |
| 3-cone, time to reach 3 yards per second | 0.78 | 36 |

Top speed in the 40 is essentially the same number twice, and the flying middle split is that same number. Gauntlet speed, pass-rush-drill speed, drop speed, and 45-degree top speed agree well enough to talk about a player, not a single noisy rep. The 3-cone time-to-speed is the exception that proves the window matters: on a longer agility drill, "how long until he is moving" can repeat (0.78). It does not repeat when the window is the first step.

Across the drills with two attempts, the median agreement is 0.27 for peak acceleration in the first second, 0.17 for distance covered in that second, and 0.14 for time to reach 3 yards per second. A fitted sprint curve is worse: the initial acceleration term agrees at 0.06 and the time-constant at 0.11. The tracking-derived 0-to-10 yard split of the 40 agrees at only 0.26 (375 pairs). That is a different instrument from the official electronic 10-yard split. At 10 pictures a second the first step is two to four frames, so these numbers are mostly which frames the chip happened to catch.

**Figure 1.** Placeholder, not stored in the repository. The reliability map: each point is one drill measurement, attempt-to-attempt agreement against how long a window it uses, with the stable in-game measurements marked beside them. Feed it from the attempt-agreement file (`reliability.csv`) and the odd-versus-even game file (`game_metric_reliability.csv`). The 40 splits are in `forty_split_reliability.csv`.

The same players' in-game numbers, split into odd and even plays, do repeat. Defensive-line get-off agrees at 0.97 and pressure rate at 0.76 (69 linemen). An offensive lineman's speed in the first second of a pass set agrees at 0.98, and the peak pressure probability he allows at 0.89 (66 linemen). A defensive back's burst in the second after the throw agrees at 0.86 (80 backs). Receiver yards after the catch, relative to expectation, agrees at only 0.49 (74 receivers). The Sunday measurements that matter are stable. The Combine measurements of the first step are not.

## A correlation that does not survive its own ruler

Speed kept through the 45-degree break, speed just after the turn divided by speed just before it, lines up with expected points allowed per credited target. Expected points are the offense's change in expected points on the play. The correlation is about -0.60 (interval -0.81 to -0.25, 26 backs). A back who comes out of the turn faster gives up fewer expected points. The link is still about -0.57 to -0.60 after draft slot and after 40 time. A within-class shuffle puts the two-sided probability at 0.009. Dropping any one player leaves the correlation between -0.71 and -0.52. Inside this sample it is not one player's fluke, and it is not draft capital or straight-line speed.

The ruler fails. Two valid attempts agree at 0.17 (10 pairs, interval -0.56 to 0.75). Averaging those two reps would only raise agreement to about 0.29. Of 241 attempts on the drill, 171 (71 percent) never show a break inside the search window, so they have no retention number. In the 26-player result, 22 players contribute a single attempt. If a measurement only agrees with itself at 0.17, the strongest correlation it can have with any outcome is about 0.41, even if the outcome were measured perfectly. The observed -0.60 sits above that ceiling. Dropping the break-time cap, so more turns count, the agreement is 0.01 on 70 pairs. The metric also does not show up where it should on Sundays: separation allowed is -0.03 (26 backs), and closing speed at the throw is +0.17 (20 corners), the wrong direction. Both intervals include zero.

The lesson is the lead of this paper. A striking correlation from a measurement that does not repeat is chance, or it is who happened to give an uncensored rep. It is not a trait to draft on. An earlier look at credited throws found that the gap and the closing speed at the release move the chance of a completion, and wing span and jumps do not. Those are game measurements, and the game measurements above do repeat. They do not rescue a Combine rep that does not.

## The link that is actually there

Get-off is a time, so a quicker first step is a smaller number. That quicker get-off goes with a higher pressure rate: correlation -0.45 (interval -0.62 to -0.23, 69 defensive linemen), after accounting for weight and for how often he aligns on the edge. Get-off itself repeats at 0.97. Next Gen Stats already publishes it. This is a sturdy in-game fact, not a Combine discovery.

The official electronic 10-yard split does carry into that fact, on 54 linemen, after the same accounting for weight and alignment. The split is also a time. A faster split goes with more pressures (correlation -0.36, interval -0.58 to -0.10) and with a quicker get-off (correlation +0.32 between the two times, interval +0.05 to +0.55). The official 40 time behaves the same way (-0.41 with pressure rate, +0.34 with get-off). Add draft slot and the pressure link is -0.31, while the get-off link is +0.27 and its interval touches zero. Tracking versions of the start add nothing once that official 10-yard split is in the model: the remaining correlations run from -0.03 to -0.12, and none is distinguishable from zero.

Seven Combine-tracking candidates were tried, each a chain from a drill number to an in-game movement to a season outcome. A Holm correction raises the bar as more tests are tried, so one lucky result out of seven does not count. None of the seven links from the drill to the season outcome survives it. The retention test above is an eighth look, from an earlier pass, and it is not in that seven.

**Table 2. Seven Combine-tracking candidates.** The number is drill to season result, inside position group and draft class. For pressure rate and yards after the catch, positive means more of the drill trait went with more production. For expected points allowed, negative means less offense given up. "Passes" means it survives the seven-test Holm correction. Fed by `candidates.csv`. The seventh row is from the same scan and was added because the pass-rush drill was the most repeatable defensive-line speed, before its outcome was inspected. It still counts in the seven.

| Candidate | Players | Drill to outcome | Passes |
| --- | --- | --- | --- |
| 40 peak acceleration to pressure rate | 53 | +0.25 | No |
| Hoop-drill top speed to pressure rate (10 repeat pairs) | 63 | +0.29 | No |
| Offensive-line drop speed to pressure allowed | 65 | -0.12 | No |
| Gauntlet top speed to yards after catch | 73 | +0.14 | No |
| 40 peak acceleration to expected points allowed | 39 | -0.24 | No |
| 45-degree top speed to expected points allowed | 47 | -0.23 | No |
| Pass-rush-drill top speed to pressure rate | 69 | +0.31 | No |

The closest miss is the last row (Holm probability 0.067). Three defensive-line drills do line up with get-off before any body-type accounting, and those movement links survive the correction. They disappear once weight and edge alignment are included, and they disappear once the official 40 or 10-yard split is included. Drill top speed was marking a light edge rusher against a heavy interior lineman. The stopwatch already has that information. For offensive linemen, receivers, and defensive backs, 40 time, the official 10-yard split, and 40 top speed are unrelated to the outcomes used here. The absolute correlation is at most 0.28.

One subgroup was inspected after the fact. Among interior linemen only, a faster tracking 0-to-10 split (again a time, so the correlation is negative) goes with more pressures: -0.58 (interval -0.78 to -0.25, 28 players), and weight does not move it. That split's own attempt-to-attempt agreement is 0.26. Edge-only, 25 to 26 players, shows nothing. This is a hypothesis for a later class, not a finding.

## What to trust

Trust a number that the same player produces twice, and that still means something after body type and the stopwatch.

Use 40 top speed and the flying 10-to-20 as a check that the chip and the stopwatch saw the same run. They repeat at 0.99 and 0.98. Other public work already uses 40 top speed. For defensive linemen, before any body-type accounting, faster top speed goes with a quicker get-off (-0.65) and with more pressures (+0.46), and that is the same light-edge versus heavy-interior mix. Do not treat it as a new trait. Gauntlet top speed repeats at 0.66, but it did not predict yards after the catch. Defensive-line and offensive-line drill top speed repeat in the 0.5 to 0.6 range and then collapse to body type. Prefer the official 10-yard split when the question is whether a rusher gets off the ball and creates pressure.

Do not rank players on a first step, a peak acceleration in the first second, a tracking 0-to-10 split, or speed kept through one change-of-direction rep. Those agreements sit near 0.1 to 0.3, and the first step is two to four frames. The retention correlation near -0.60 is the cautionary example, not a board column.

For the league, burst and change-of-direction drills need a faster sampling rate than 10 Hz, or several attempts, before a tracking number can be a trait. Two reps that agree at 0.2 cannot support a ranking. In-game get-off, pressure rate, and a back's burst after the throw already repeat. Measure those on Sundays.

## Where this sits

Next Gen Stats already estimates completion probability and separation. The 2021 Big Data Bowl coverage work framed how a defender is asked to play. Nimphius described the change-of-direction deficit, the time a cut costs beyond straight speed. SumerSports has published hip fluidity. Among the public 2027 notebooks, Speed Realization uses 40 top speed and finds no link for defensive backs, which matches the nulls here. Deceleration Weapon and Decoupling Point study braking and the point a route leaves the stem. Speed Into the Cut uses this same 45-degree drill and also finds cut-exit speed repeating at only 0.26. This paper is the map in front of those questions: which Combine tracking numbers are stable enough to link to a season, and which are not.

<!-- SUBMISSION END -->

## Part B. Author notes (not submitted)

### Rules reminders

- Track: University, solo author. Leave the Grand Prize track empty.
- At or under 2,000 words, fewer than 10 tables or figures, attached public notebook. Part A has 2 tables and 1 figure.
- Do not attach or quote row-level competition data, and do not add a per-player table. The working player files from the 2026-11-27 scan stay off git.
- The notebook in this repo still draws the older retention figures. Figure 1 in Part A is a placeholder. Draw it from `reliability.csv`, `game_metric_reliability.csv`, and `forty_split_reliability.csv` before submitting. Table 2 is fed by `candidates.csv` except the pass-rush-drill row, which is in the scan summary (added after the reliability screen, before its outcome was read, and counted in the Holm family of seven).

### Number notes for the reliability lead

Attempt agreement below 0.5 is the median across drills with two reps, as stated in the scan summary: peak acceleration in the first second 0.27, distance in 1 second 0.17, time to 3 yards per second 0.14, sprint-profile initial acceleration 0.06, time constant 0.11. The tracking 0-to-10 split is 0.263 on 375 pairs. The flying 10-to-20 is 0.977. Game split-half agreement: get-off 0.965 (n 69), pressure rate 0.761 (n 69), offensive-line set speed 0.981 and peak pressure probability 0.889 (n 66), defensive-back release burst 0.856 (n 80), yards after catch over expected 0.488 (n 74).

The retention correlation in the second-round file is -0.596 (interval -0.806 to -0.253, p 0.0017, n 26). Partial correlations stay in -0.57 to -0.60 after log draft pick and after 40 time (40-time partial -0.572 on 22 players). Within-class permutation p is 0.0091 on 10,000 shuffles. Leave-one-out runs from -0.707 to -0.521. Repetition on the pipeline definition is 0.170 (interval -0.557 to 0.749, 10 pairs); Spearman-Brown for a two-rep mean is 0.29. The ceiling sqrt(0.17) is about 0.41, from the scan note. Separation allowed is -0.027 (n 26). Closing speed is +0.167 (n 20). Without the break cap, agreement is 0.01 on 70 pairs.

Get-off to pressure, net of weight and alignment, is -0.45 (interval -0.62 to -0.23, n 69) in the scan summary. The unadjusted game-side correlation in the candidate file is about -0.55. Official 10-yard split, same controls, n 54: pressure -0.36 (interval -0.58 to -0.10, permutation p 0.006), get-off +0.32 (interval 0.05 to 0.55, p 0.02). The 40 time is -0.41 and +0.34. With log draft pick added, -0.31 and +0.27, and the get-off interval touches zero. Tracking partials beyond the official split run from -0.03 to -0.12. Interior-only tracking 0-to-10 to pressure is -0.58 (interval -0.78 to -0.25, n 28). Forty top speed for defensive linemen, before body-type controls: get-off -0.65, pressure +0.46.

Candidate outcome correlations and Holm probabilities, for the table in Part A: C1 +0.25, Holm 0.39, n 53; C2 +0.29, Holm 0.13, n 63, repeat pairs 10; C3 -0.12, Holm 0.53, n 65; C4 +0.14, Holm 0.53, n 73; C5 -0.24, Holm 0.53, n 39; C6 -0.23, Holm 0.53, n 47; C7 +0.31, Holm 0.067, permutation p 0.009, n 69. C7 with weight and alignment: outcome +0.13 (p 0.31), get-off -0.06. With the 10-yard split, about zero.

The older completion model (gap and closing speed at the throw, not wing span or jumps) is one sentence in Part A. Do not bring back the coefficient table or the calibration bins unless a figure is freed.

### Amendments and results history

The six-test family and amendments A1-A6 (2026-11-15) defined the retention metric used in the cautionary section. They are no longer the lead. State in the write-up that the retention correlation was seen before the reliability scan, and that the definitions were amended after a first look. The drill-to-outcome candidates C1-C7 are a later scan (2026-11-27) with their own Holm family. C7 was chosen for reliability before its outcome was read, and it still counts.

Dated 2026-11-15, after the first run on the competition files. The definitions are in `src/bdb2027/preregistration.py`.

| ID | Change | Why |
| --- | --- | --- |
| A1 | Outcomes use only games with `season_type` `REG`. | The theme says regular-season performance. Preseason and postseason games are in the file. |
| A2 | A draftee defensive back is credited when he is the closest opposing back with an active coverage assignment and within 5 yards at the throw. | Game tracking holds only the 510 draftees. The nearest tracked back was usually not the covering defender. |
| A3 | The break is searched only in the first 5.5 seconds, in every class. | 2024 backpedal attempts end near 6 seconds. 2023 and 2025 run about 10 to 12 seconds. |
| A4 | The correlation interval spends a degree of freedom for each draft-class mean removed. | Class means are estimated, not known. |
| A5 | The tight-end 3-cone test stays in the original family and is flagged underpowered. | Seven tight ends in two classes. |
| A6 | Attempts with no break by 5.5 seconds are censored and ranked slowest. Speed retention exists only when a break is detected. | Censoring keeps the information that the player had not broken. Retention cannot be computed without a break, which is why 71 percent of attempts drop out of that metric. |
