# BDB 2027 rules checklist

Retrieved 15 November 2026. This file records what was read from official pages. It does not add requirements that those pages do not state. Where a page and another official source disagree, both are quoted and the disagreement is flagged.

## Sources

| Source | What was read | How |
| --- | --- | --- |
| Kaggle competition pages for `nfl-big-data-bowl-2027` (competition id 162982) | Rules, Description, Timeline, Submission Requirements, data description, Evaluation, abstract | Public URLs below. The site HTML shell does not include the article text, so the published page bodies were read from Kaggle's competition PageService (`/api/i/competitions.PageService/ListPages`) on 15 November 2026. |
| Kaggle competition record | Title, deadline, license, team size, prize quantity, hackathon flag, merger and entry-close timestamps | `CompetitionService/GetCompetition` for `nfl-big-data-bowl-2027`, same day. |
| Kaggle hackathon tracks | Open, University, and Grand Prize track text and prize amounts | `HackathonService/ListHackathonTracks`, same day. |
| NFL Football Operations | 2027 edition description, tracks as the NFL page states them, judging at a high level | [Big Data Bowl](https://operations.nfl.com/programs-initiatives/innovation/big-data-bowl), fetched 15 November 2026. |
| Community docs repo | Pointer only | [Abdelhaleem1/nfl-big-data-bowl-2027-docs](https://github.com/Abdelhaleem1/nfl-big-data-bowl-2027-docs). Its column dictionary is labeled unverified locally, so this project does not treat those column names as official. |

Public URLs:

- Overview and theme: https://www.kaggle.com/competitions/nfl-big-data-bowl-2027
- Rules: https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/rules
- Data: https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/data
- License named on the competition record: https://creativecommons.org/licenses/by-nc/4.0/

Secondary write-ups and forum posts were not used as rules. Several claims that appear in unofficial guides (a named judge, paid finalist travel, an appendix excluded from the word cap, a host correction of the NFL Operations track wording) were **not** found in the sources above. They are listed under unverified items.

## Competition format

Verified from the Kaggle Description, abstract, Evaluation page, and the competition record (`hackathon: true`).

- Theme: "Combine to NFL Performance." The task is an analytical framework linking 10 Hz Combine sensor tracking to future regular-season NFL game performance.
- This is a hackathon. The general rules say submissions in a hackathon are judged on the Evaluation Rubric on the competition website, and that hackathons have no leaderboard.
- The deliverable is a write-up plus a public notebook, not a prediction CSV. The 2026 prediction-style baseline does not match this competition.
- The Description encourages a narrow question: one aspect of movement, one position group, or one drill. The examples include change of direction, deceleration, and acceleration for receivers and defensive backs compared with in-game separation. The list is not exhaustive.
- Position groups named on the NFL Operations 2027 section: wide receivers, tight ends, defensive backs, offensive linemen, and defensive linemen. Combine tracking is from Zebra chips at the 2023, 2024, and 2025 Combines, plus in-game tracking for those players.

## Write-up format and length

Verified from Submission Requirements and Evaluation.

- No more than 2,000 words.
- Fewer than 10 tables or figures. The page says submissions over these limits may be penalized. Ten tables or figures is already over the stated limit.
- Readable markdown, embedded visuals, and an attached **public Kaggle notebook**. Missing any of these fails the Writeup Completeness gate.
- "Any writeup that does not use the player tracking data will not be scored." The same sentence appears on Submission Requirements and on Evaluation.
- Participants are encouraged to show statistical code when it helps, but most code should be in an appendix or a linked notebook.
- The rules do not state a required language for the write-up. That silence is not a rule that any language is accepted; it is simply unstated.

Not stated on these pages: whether an appendix is excluded from the 2,000-word count or the figure count, whether figure captions count, or a required section order. See unverified items.

## Required notebook

Verified from the Evaluation gate "Writeup Completeness": the write-up must feature readable markdown, embedded visuals, and an attached public Kaggle notebook.

The notebook skeleton in this repo reads `/kaggle/input/nfl-big-data-bowl-2027/`. That path is the usual Kaggle mount for this competition slug. The pages that were read do not spell the mount path. Treat the path as a platform convention, not as a sentence on the rules page.

## Tracks, prizes, and categories

Verified from the rules prize section and from `ListHackathonTracks`.

Total prizes on the rules page: **$100,000**.

| Track | Who | Prizes on the rules page |
| --- | --- | --- |
| Open Track | Track description: "No eligibility restrictions for entry." | 3 finalists at $10,000 and 3 runners-up at $5,000 ($45,000). |
| University Track | "Open only to groups or individuals composed entirely of undergraduate students. Verification may be required to prove eligibility." | Same split, $45,000. |
| Grand Prize | "Submissions should not be made to this track." It is an additional $10,000 for one invited finalist team after a presentation at the 2027 NFL Scouting Combine. | $10,000. |

Kaggle categories on the competition record are the tags football, sports, and data analytics. Those are site tags, not the two entry tracks.

**Conflict, flagged.** The NFL Operations 2027 section, retrieved the same day, says:

- "Undergraduate/Graduate Track: Open only to groups or individuals composed entirely of undergraduate or graduate students."
- "Open Track: Open to all individuals or groups outside of college/university."

The Kaggle University Track text does not mention graduate students, and the Kaggle Open Track text does not restrict entry to people outside college. The rules you accept are the Kaggle rules. The Operations page is still an official NFL page, and this checklist does not resolve the conflict. No host forum post correcting the Operations wording was retrieved.

## Deadlines

Verified from the Timeline page. "All deadlines are at 11:59 PM UTC on the corresponding day unless otherwise noted. The competition organizers reserve the right to update the contest timeline."

| Event | As the Timeline page states it |
| --- | --- |
| Start | October 6, 2026 |
| Final submission deadline | January 6, 2027 |
| Judging period | January 7, 2027 – January 25, 2027, "subject to change based on the number of submissions received" |
| Anticipated results | January 26, 2027 |

The competition record's `deadline` field is `2027-01-06T23:59:00Z`, which matches 11:59 PM UTC on 6 January 2027.

The Timeline page does not list a separate entry deadline or team-merger deadline. The competition record has `teamMergerExplicitDeadline` and `prohibitNewEntrantsExplicitDeadline` of `2027-01-06T23:59:59Z`. Those are platform fields, not sentences on the Timeline page.

The date of the Combine presentation is not on the Timeline page. The Operations page says finalists will be announced in early 2027 and will present at the 2027 NFL Scouting Combine. It does not give the calendar day.

## Data files, use, and license

Verified from the data-description page, rules sections 1.7 and 2.4, and the competition license record.

The data page says the dataset has **9 CSV files**, about **2.2 GiB**, for **510** rookie prospects drafted or signed between 2023 and 2025. It also states 6,310 Combine drill attempts, 316,338 player-play records, and 1,002 games. On 2026-11-15 the downloaded files were checked locally. They had 510 prospects, 6,310 attempts, and 1,002 games, matching the page, and 314,197 `player_play.csv` rows, 2,141 fewer than the page states. `play_description` contains line breaks, so a raw line count (327,020) overstates the rows. This repo does not contain the files.

| File | Role on the data page |
| --- | --- |
| `players.csv` | Prospect identifiers, draft year, NFL position, college, draft slot. |
| `combine_results.csv` | Anthropometrics and stopwatch tests, including `ten_yd_split`, `forty`, and `three_cone`, plus NGS scores. |
| `combine_tracking.csv` | 10 Hz Combine tracking. `drill_type` examples include `SKILL_DRILLS_TE`, `SKILL_DRILLS_DB`, and `THREE_CONE_DRILL`. `drill_name` examples include `BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION`. |
| `player_play.csv` | Play-level NFL participation and outcomes, including `separation_at_pass_forward`, `target`, `pass_result`, and `expected_points_added`. |
| `games.csv` | Game, season, week, and home/visitor clubs. The page says `season_type` is `REG` or `POST`. The file also has `PRE` (49 games per season). See amendment A1. |
| `player_career_successes.csv` | Career snaps, games, All-Pro, and Pro Bowl counts. |
| `game_tracking_2023.csv` | 10 Hz in-game tracking. `event` includes `pass_forward`. |
| `game_tracking_2024.csv` | Same schema for 2024. |
| `game_tracking_2025.csv` | Same schema for 2025. |

Column names used by this code are the names on that data page, including the published spelling `visitor_team_win_probility_added`. The loader also accepts `visitor_team_win_probability_added` if the published spelling is absent. The file on disk uses the typo `visitor_team_win_probility_added` (checked 2026-11-15).

License:

- Rules section 1.7, "DATA ACCESS AND USE": CC BY-NC 4.0.
- The competition record names "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)" and links to the Creative Commons deed above.
- Rules section 2.4: Competition Data may be used for non-commercial purposes only, including the competition, Kaggle forums, and academic research and education. The sponsor may disqualify other uses.
- Rules section 2.4, data security: do not transmit, duplicate, publish, redistribute, or otherwise make the Competition Data available to any party who is not participating in the competition.

The general-rules definition of "Competition Data" still mentions private and public test sets. The data page that was read describes the nine files above and does not describe a hidden prediction test set. That definition looks like shared Kaggle boilerplate next to a hackathon that also says there is no leaderboard. This checklist does not claim a hidden test set exists.

## External data

Verified from rules section 2.6, "EXTERNAL DATA AND TOOLS." Paraphrased closely:

- You may use data other than the Competition Data ("External Data") to develop and test submissions.
- That data must either be publicly available and equally accessible to all participants for the competition **at no cost to the other participants**, or it must satisfy the Reasonableness criteria in section 2.6.b.
- External data and models are acceptable unless the host specifically prohibits them.
- Because of cost or restrictions such as geo restrictions, use must be "reasonably accessible to all" and of "minimal cost."
- The host applies a Reasonableness Standard using cost and accessibility. The rules' own examples: a small subscription for extra elements of a large language model such as Gemini Advanced can be acceptable; purchasing a license for a proprietary dataset that costs more than a prize is not reasonable.
- Using external data does not remove other duties, including winner obligations.
- Rules section 2.5.a.3: if input data or a pretrained model with an incompatible license is used in a winning solution, that data or model does not itself have to be open-sourced. That exception does not waive the access test in section 2.6 during the competition.
- Rules section 3.5.d: no private sharing of code or data outside the team. Code may be shared when it is made available to all participants on the forums.
- Rules section 3.14: you warrant that the submission is your original work and that it does not infringe third-party intellectual property.

**What the rules do not say.** They do not name a disclosure form, a citation format, or a required sentence in the write-up. They do not mention EA, Madden, or player ratings. They do not say that a paid video game's ratings are allowed.

### Madden ratings

Patrick may want EA Madden NFL ratings (Speed, Acceleration, Agility, Change of Direction, Route Running, Release, Man Coverage, Zone Coverage) only as a secondary benchmark for tight ends and defensive backs, not as the core analysis.

Finding:

- External data of the kind section 2.6 describes is allowed, under the conditions above.
- Madden ratings were **not** shown to meet those conditions. No official EA license permitting republication of those ratings was retrieved. Ratings that exist only inside a paid game are not, on their face, "equally accessible to use by all Participants ... at no cost."
- Putting those ratings in this git repository or in a public notebook would be a redistribution and copyright question that this check did not clear. Rules section 3.14 puts the infringement risk on the entrant.
- The section 2.5.a.3 exception would matter only for a winning solution's open-source duty. It is not permission to use a non-public file during the competition.

This repo therefore keeps an optional comparison that is **off unless explicitly enabled**. It reads a local CSV that is already on disk. It does not download, scrape, or write the ratings. The comparison is labeled `external_secondary` and is outside the pre-registered six-test family. Leave it off unless a source is confirmed against section 2.6, and do not commit the file.

## Team rules

Verified from the competition-specific rules and the general rules.

- Maximum team size is five (rules section 2.1.a and the competition record).
- One Kaggle account per person. Submitting from more than one account is grounds for disqualification. You cannot sign up from multiple accounts.
- Each person joins or forms only one team, registers individually, and confirms the team invitation.
- Hackathons: each team may submit one submission only (rules section 2.2.c). Submissions made before a merger are unsubmitted (rules section 2.1.b).
- No private sharing of code or data outside the team.
- Public sharing of competition code, if done, is on the competition forum or notebooks and is deemed licensed under an OSI-approved license that does not limit commercial use.
- Open-source code used in the model must carry an OSI-approved license that does not limit commercial use, unless the specific rules say otherwise.
- Team prizes are split evenly unless the team unanimously agrees otherwise and tells Kaggle before prizes are issued.

**Conflict, flagged.** The same specific-rules section also says you may submit a maximum of five submissions per day and select up to two final submissions (2.2.a and 2.2.b). The competition record repeats `maxDailySubmissions: 5` and `numScoredSubmissions: 2`, and it has `hasLeaderboard: true`. Section 2.2.c and general rule 3.7 say a hackathon team submits once and that hackathons have no leaderboard. The written hackathon sentences and the platform fields were both present on 15 November 2026. This project follows the hackathon sentences: one write-up, no prediction leaderboard. The numeric platform fields were not reconciled with a rendered leaderboard, because the HTML shell did not show one.

## Eligibility

Verified from rules sections 2.7 and 3.1.

- Registered Kaggle account.
- The older of 18 or the age of majority in the place of residence, unless the sponsor agrees and parental or guardian consent has been obtained by the sponsor.
- Specific rule 2.7.b: the sponsor allows people under 18 to participate with parental or guardian consent, but they cannot receive a prize.
- Not a resident of Crimea, the so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, or North Korea, and not a person or representative of an entity under U.S. export controls or sanctions.
- Open to residents of the United States and worldwide, aside from those exclusions. Other local laws may still apply. A winner in a country where prizes cannot be awarded is not eligible to receive one.
- Employees, interns, contractors, officers, and directors of the NFL, Kaggle, and their parents, subsidiaries, and affiliates may enter but cannot win prizes.
- The sponsor may verify eligibility. False identity or residency information can mean disqualification.
- If you enter for an employer or school, the rules bind you and that entity, and you warrant that they know and consent.

The competition record has `requiresIdentityVerification: true`. The rules text that was read does not say what document that check uses. University Track verification "may be required" for undergraduates; the accepted documents are not listed.

## Judging

Verified from the Evaluation page and the judges paragraph on Submission Requirements.

Two pass/fail gates, then four scores from 0 to 10:

| Gate or score | Standard on the page |
| --- | --- |
| Combine-to-NFL linkage | Pass/fail. The write-up explicitly links Combine sensor tracking data to regular-season NFL game performance. |
| Write-up completeness | Pass/fail. Readable markdown, embedded visuals, and an attached public Kaggle notebook. |
| Football, 30% | Could NFL teams or the league office use the results week to week? Does the analysis account for the variables that make football data complex? Are the ideas unique? |
| Data science, 30% | Is the work correct? Are claims backed by data? Are the statistical models appropriate given the data? Are the analytical applications innovative? |
| Write-up, 20% | Well written, easy to follow, and is the motivation (metric, player evaluation, and so on) clearly defined? |
| Data visualization, 20% | Are the charts and tables accessible, accurate, and innovative? |

"Scores will be summarized using a weighted average based on the percentages above."

"Judges will consist of analytics staffers working for the 32 NFL teams or player tracking vendors that work with NFL teams."

The NFL Operations page says NFL club analytics staff judge submissions with NFL Football Operations staff, and that finalists present at the Combine. It also describes a separate mentorship program. The mentorship code of conduct on that page applies to the mentorship program, not to every competition entry. This checklist does not copy those mentorship rules into the competition rules.

General rules that affect a winner, verified from the rules text: notification by email; reply within one week of the first notification attempt or the prize can be forfeited; prize documents within two weeks; prizes paid about 30 days after documents arrive; taxes are the winner's responsibility; U.S. residents receive a 1099; winners license the winning submission and the source code under an OSI-approved license that does not limit commercial use, with the software and incompatible-input-data exceptions in section 2.5; winners may be asked for a reproducible description and a code repository. Publicity: the sponsor and Kaggle may use name and likeness for promotion without extra pay, unless the law prohibits it.

## Pre-registered analysis choices that are not rules

These are project choices, fixed in `src/bdb2027/preregistration.py` before any competition CSV was available in this repository. They are not NFL definitions.

- Six tests. Two are primary (TE skill-drill deceleration versus separation when targeted; DB time-to-break versus separation allowed). The other four are secondary and share one Bonferroni threshold, `0.05 / 6`.
- Within-`draft_year` demeaning, then Pearson correlation. Effect size is that correlation. The interval is a Fisher z interval that treats players as independent after demeaning. It is not cluster-robust, and estimating class means uses degrees of freedom the interval does not remove.
- A draft class is included only when it has at least three players with both values. `small_n` is true when the pooled player count is under 20.
- TE inclusion floor: at least five targeted plays. DB inclusion floor: at least five credited targets (amendment A2). The planning notes of about 18 tight ends and about 62 defensive backs with enough snaps are **not** measured sample sizes.
- Break threshold: 45 degrees of heading change. Deceleration is computed from the change in speed, not from `a`.
- DB positions treated as coverage players: `CB`, `SS`, `FS`, `DB`, `S`.

## Amendments, 2026-11-15

These were made after the first run on the competition files, so results under the original definitions had been seen. They are recorded in `src/bdb2027/preregistration.py` and in `docs/WRITEUP_DRAFT.md`, which also lists the original results.

| ID | Change | Why |
| --- | --- | --- |
| A1 | Outcomes use only games with `season_type` `REG`. | `games.csv` has 49 PRE, 272 REG, and 13 POST games per season, although the data page lists only REG and POST. The theme and the linkage gate say regular-season performance. About 20% of targets were in PRE or POST games. |
| A2 | DB coverage credit uses `coverage_assignment`. A draftee DB is credited with a target when the targeted receiver is a tracked draftee, the DB is on the other team with an active `coverage_assignment` (not missing, not `NO_ASSIGNMENT`), and at `pass_forward` he is the closest such DB to the receiver and within 5 yards. Separation allowed is the receiver's `separation_at_pass_forward`. | Game tracking holds only the 510 draftees, about 3 tracked players per `pass_forward` frame. The original "nearest tracked DB" was a median 12.6 yards from the target and usually not the covering defender. |
| A3 | A break is only searched for in the first 5.5 s of each drill attempt, in every class. DB results are also reported without the 2024 class. | 2024 `BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION` attempts end after 5.3 to 6.6 s. 2023 attempts last about 11.7 s and 2025 about 10.2 s. Without a cap, later breaks could only be found outside 2024. |
| A4 | Fisher standard error is `1 / sqrt(n - 3 - (k - 1))` for `k` draft classes. | Removing `k` class means costs `k - 1` degrees of freedom beyond an ordinary Pearson correlation. |
| A5 | `te_secondary_three_cone_completion` is flagged `underpowered`. It stays in the family of 6 and in the Bonferroni count. | Only 7 tight ends in 2 classes have a 3-cone time and at least 5 regular-season targets. |

Other checks from the same run:

- Column `a` is never negative in `combine_tracking.csv` (minimum 0), so it is a magnitude. Deceleration from the change in speed stays.
- `BALL` entity rows exist only in the 2025 Combine file. Ball speed reaches about 25.8 yd/s. Player rows never exceed 12 yd/s. The loader already keeps only `PLAYER` rows.
- Stopwatch times (`ten_yd_split`, `forty`, `three_cone`) have similar means and ranges in all three classes.

## Unverified or conflicting

1. The Kaggle website was not rendered in a browser. Page text was taken from the competition PageService and the competition and track records. If the rendered site has been edited since those records were written, this checklist would not show that edit.
2. Whether an appendix, captions, or code blocks count toward the 2,000 words or the figure limit.
3. A required disclosure sentence or citation format for external data. The duty that was found is the access test in section 2.6, the ban on private sharing, and the warranty against infringement.
4. Whether any free, public, equally accessible source of Madden ratings exists, and what EA's current terms say about republishing Speed, Acceleration, Agility, Change of Direction, Route Running, Release, Man, or Zone ratings. No EA terms page was retrieved.
5. The Operations page versus Kaggle on graduate students and on who may enter the Open Track. No host forum correction was retrieved.
6. Hackathon "one submission, no leaderboard" versus platform fields of five daily submissions, two scored submissions, and `hasLeaderboard: true`.
7. Whether the general-rules mention of private and public test sets describes a real hidden file. The data page that was read does not list one.
8. Resolved 2026-11-15: counts match except `player_play.csv` (314,197 rows, not 316,338), and the file uses `visitor_team_win_probility_added`.
9. Resolved 2026-11-15: column `a` is never negative, so it is a magnitude.
10. A named individual judge, whether finalist travel and lodging are paid, whether the Combine presentation can be given remotely, and the criteria used only for the in-person Grand Prize. The track text says invited finalists present and one team receives an additional $10,000. It does not state a separate rubric.
11. What identity-verification or University Track verification requires as documents.
12. Host comments sometimes repeated in unofficial guides (a null result still passes, preseason or postseason outcomes count, `nflreadr` was suggested, the Operations graduate wording was called an error). Those comments were not retrieved from the competition forum for this checklist.
13. Resolved 2026-11-15: the nine files were downloaded to the local WSL `data/` directory, which is gitignored.
14. Whether the host accepts preseason or postseason outcomes (item 12). Amendment A1 follows the official "regular-season" wording.
