# Write-up outline

This is the outline for the Kaggle write-up. It is not the submission. The finished write-up has to stay at or under 2,000 words and use fewer than 10 tables or figures. An attached public notebook is required. Do not submit this draft to the Grand Prize track.

Working title: Combine brakes and NFL separation for tight ends and defensive backs

Working subtitle: Within-draft-class links from 10 Hz Combine tracking to targeted-route separation

Track to select at submission: Open or University. University only if every member is an undergraduate. Leave the Grand Prize track empty.

## 1. Question

Two pre-registered questions, nothing else in the scored family.

Tight ends. Do Combine explosiveness and deceleration measures translate to route separation and target outcomes? The measures are the 10-yard split, the 3-cone time, and the braking peak on TE position drills (`SKILL_DRILLS_TE`) from 10 Hz tracking.

Defensive backs. Does the backpedal-to-break transition (`BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION`) predict coverage outcomes: separation allowed, completions allowed, and offensive EPA allowed?

The tracking requirement is met by the TE drill series and by the DB transition series, plus in-game `pass_forward` frames for the DB outcomes. Stopwatch times are the traditional comparison, not a substitute for the tracking.

## 2. Pre-registered family

State that this list was fixed before the competition CSVs were analyzed. Report every row. Do not add a test after seeing the result without saying that it was not pre-registered.

| Role | Angle | Predictor | Outcome | Expected sign |
| --- | --- | --- | --- | --- |
| Primary | TE | Harder brake on TE position drills | Mean separation when targeted | Positive |
| Secondary | TE | Faster 10-yard split | Mean separation when targeted | Positive |
| Secondary | TE | Faster 3-cone | Completion rate when targeted | Positive |
| Primary | DB | Quicker time to the 45-degree break | Mean separation allowed | Negative |
| Secondary | DB | Speed kept through that break | Mean offensive EPA allowed | Negative |
| Secondary | DB | Quicker time to the break | Completion rate allowed | Negative |

Family size is 6. The interval on each row is an unadjusted 95% Fisher interval. The Bonferroni reference threshold is 0.05/6. The write-up should show the interval and the sample size, not a star.

This table is one of the write-up's tables. Count it.

## 3. Data and definitions

Name the nine competition files and the CC BY-NC 4.0 limits. Do not attach the files.

Definitions to state in plain language:

- Draft class is `draft_year`. Classes are not pooled on the raw scale, because Combine recording can differ by year. Both the predictor and the outcome are demeaned inside the class. The correlation is the Pearson correlation of those deviations.
- A TE play counts when `nfl_position` is TE, `lined_up_position` is TE, the play is not nullified by penalty, and `target` is true. Separation is `separation_at_pass_forward`. A completion is `pass_result` of `C`.
- A DB outcome is not a published column. At `pass_forward`, the targeted receiver is assigned to the nearest player whose NFL position is CB, SS, FS, DB, or S. Separation allowed is that distance in yards. Completion and EPA are the play's `pass_result` and `expected_points_added`.
- A break is the first frame, after speed reaches 1 yard per second, where heading has moved 45 degrees from the opening heading. That label is not on the file. Deceleration is the drop in speed per second. Column `a` is not treated as a signed brake, because the data page does not say it is signed.
- Inclusion floors: at least five targeted TE plays, and at least five covered targets for a DB. A class needs at least three such players to enter the pooled correlation.
- The notes of about 18 tight ends and about 62 defensive backs are planning cautions from the project brief. Replace them with the actual `n_players` and `class_counts` from `outputs/effects.csv`. Mark `small_n` when that count is under 20.

## 4. Method, in one short section

One paragraph on within-class demeaning, one on the Fisher interval and its limit (players are treated as independent after demeaning; class means were estimated and the interval does not spend those degrees of freedom), and one on multiplicity. Say that a wide interval is an expected result at this sample size, not a failed chart.

No model beyond this correlation family belongs in the write-up unless it is labeled as not pre-registered.

## 5. Tight ends

Placeholder for the primary scatter of within-class deviations and a sentence that matches the sign of `te_primary_decel_separation`. Then the two secondary rows, including a null if that is what the interval shows. Do not rank prospects.

Planned figures: the within-class scatter, and one forest of the three TE intervals. Those are two figures.

## 6. Defensive backs

Same shape for `db_primary_break_separation`, then EPA allowed and completions allowed. State that "allowed" means "nearest DB at the throw," so a zone defender who was closer than the assigned man can be charged with the play. That is a limitation, not a footnote to hide.

Planned figures: the within-class scatter, and one forest of the three DB intervals. Those are two figures.

## 7. Optional external benchmark

Include this section only if the rating source has been checked against Rules section 2.6 and is public and free for every participant, or meets the host's Reasonableness Standard. Otherwise delete the section and do not spend a figure on it.

If it is included, label it as a secondary benchmark, not as a Combine-to-NFL test. The core family does not use it. Name the source, the season or edition of the ratings, and the license under which other teams can obtain the same file at no cost. Say that Madden ratings were not cleared by the rules check in `docs/RULES_CHECKLIST.md` unless that statement is no longer true because a qualifying source was found later.

The code path is off by default:

```bash
python -m bdb2027 --data-dir data --enable-external-benchmark \
  --external-benchmark /path/outside/the/repo/ratings.csv
```

Columns, if present: Speed, Acceleration, Agility, Change of Direction, Route Running, Release, Man Coverage, Zone Coverage, joined on `nfl_id`. The comparison is within draft class, for tight ends and defensive backs only. Do not commit the file. Do not scrape a ratings site to create it.

If this section is used, it may add one scatter. Drop another figure first if the write-up would otherwise reach 10 tables or figures.

## 8. What a team could do with the result

One short paragraph aimed at the football score. If the primary intervals cover zero, say that the drill is a weak week-to-week separator at this sample size. If an interval sits away from zero, say the direction and the position group, and say what the measure does not adjust for: opponent, scheme, injury, and role.

## 9. Limitations

- Small n and six related tests.
- Observational. The interval is not a causal effect of training the drill.
- DB assignment uses the nearest defensive back, not a charted assignment.
- Combine drill labels and the 45-degree rule are a reproducible definition, not an official NGS event.
- Outcomes pool the seasons present in the files. Playing time beyond the target floors is reported from `player_career_successes.csv` and is not a covariate in the six tests.
- External ratings, if used, are not the evidence for the two gates. The gates rest on Combine tracking and NFL performance.

## 10. Appendix and notebook

Point to the public notebook `notebooks/bdb2027_combine_to_nfl.ipynb` after it has been copied to Kaggle and set to public. The notebook reads `/kaggle/input/nfl-big-data-bowl-2027/` and calls `bdb2027.pipeline.run_analysis`. Most code stays there, not in the write-up.

## Figure budget

Counted tables and figures in the finished write-up, before any optional benchmark chart: the family table, a sample-size table, two scatters, and two forests. That is 6, under the limit of fewer than 10. Do not add a chart that does not change the claim.
