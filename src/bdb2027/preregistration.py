"""Pre-registered metric family for the TE and DB analyses.

Thresholds below were fixed before any competition CSV was available in this
repo. They are analysis choices, not official NFL definitions. Amend them in
this module before looking at the corresponding result, and say so in the
write-up.
"""

from __future__ import annotations

from dataclasses import dataclass

# Combine tracking is published as 10 Hz. Deceleration uses the change in
# speed, because the data page describes `a` as instantaneous acceleration and
# does not say that `a` is signed.
SAMPLE_HZ: float = 10.0
FALLBACK_DT_SECONDS: float = 1.0 / SAMPLE_HZ
START_SPEED_YPS: float = 1.0
BREAK_HEADING_DEG: float = 45.0
RETENTION_WINDOW_SECONDS: float = 0.3
INITIAL_HEADING_FRAMES: int = 3
MIN_ATTEMPT_FRAMES: int = 4

# A draft class enters the pooled within-class correlation only when it has
# at least this many players with both the predictor and the outcome.
MIN_CLASS_PLAYERS: int = 3
# Fisher intervals need n > 3. Results with fewer than this many players are
# still returned, with small_n set, so the sample size stays visible.
SMALL_N_THRESHOLD: int = 20

# Inclusion floors. These are not the "~18 TEs / ~62 DBs" planning notes.
MIN_TE_TARGETS: int = 5
MIN_DB_TARGETS_COVERED: int = 5

TE_SKILL_DRILL_TYPE: str = "SKILL_DRILLS_TE"
THREE_CONE_DRILL_TYPE: str = "THREE_CONE_DRILL"
DB_BACKPEDAL_DRILL_NAME: str = "BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION"

TE_POSITIONS: frozenset[str] = frozenset({"TE"})
DB_POSITIONS: frozenset[str] = frozenset({"CB", "SS", "FS", "DB", "S"})

FAMILY_ALPHA: float = 0.05

# ---------------------------------------------------------------------------
# Amendments dated 2026-11-15.
#
# These were made after the first run on the competition files, so the
# outcome correlations under the original definitions had already been seen.
# The write-up has to say so and report the original run next to the amended
# one (docs/WRITEUP_DRAFT.md, "Amendments").
#
# A1. Outcomes use regular-season games only (games.season_type == "REG").
#     games.csv also has PRE and POST games, and the theme is regular-season
#     performance. Originally all game types were pooled.
# A2. Defensive-back coverage credit. Game tracking only covers the 510
#     draftees in players.csv (about 3 tracked players per pass_forward frame),
#     so "nearest tracked DB to the target" was usually not the covering
#     defender (median 12.6 yd). A draftee DB is now credited with a target
#     when all of these hold on that play:
#       - the targeted receiver is a tracked draftee (target is true);
#       - the DB is on the other team and has an active coverage_assignment
#         (not missing and not in INACTIVE_COVERAGE_ASSIGNMENTS);
#       - at pass_forward he is the closest such DB to the target and within
#         COVERAGE_RADIUS_YDS.
#     Separation allowed is the receiver's published separation_at_pass_forward
#     (nearest defender of any kind), not the receiver-to-DB distance.
#     Undrafted or veteran defenders and non-draftee targets are invisible,
#     so a credited DB is "an assigned draftee DB in the area", not a charted
#     primary defender. The 5 yd radius was picked after counting credited
#     targets per radius (3/5/7/10 yd), before any outcome correlation was
#     computed under this definition.
# A3. Break detection is capped at MAX_BREAK_TIME_S after the first frame of
#     the attempt, in every draft class. 2024 backpedal attempts end at about
#     5.3-6.6 s (2023 about 11.7 s, 2025 about 10.2 s), so later breaks could
#     only be found outside 2024. The DB tests are also reported without the
#     SENSITIVITY_DROP_CLASS class.
# A4. The Fisher interval uses n - 3 - (k - 1) degrees of freedom for k draft
#     classes. Removing k class means costs k - 1 more than an ordinary
#     Pearson correlation, which already removes one mean.
# A5. te_secondary_three_cone_completion is flagged underpowered. It stays in
#     the family and in the Bonferroni count.
AMENDMENT_DATE: str = "2026-11-15"
REGULAR_SEASON_ONLY: bool = True
REGULAR_SEASON_TYPE: str = "REG"
COVERAGE_RADIUS_YDS: float = 5.0
INACTIVE_COVERAGE_ASSIGNMENTS: frozenset[str] = frozenset({"NO_ASSIGNMENT"})
MAX_BREAK_TIME_S: float = 5.5
SENSITIVITY_DROP_CLASS: int = 2024
UNDERPOWERED_TESTS: frozenset[str] = frozenset({"te_secondary_three_cone_completion"})

# ---------------------------------------------------------------------------
# Amendment A6, dated 2026-11-15 (supersedes the "drop" part of A3).
#
# A3 dropped every backpedal attempt with no break in the first
# MAX_BREAK_TIME_S, which kept a break time for only 70 of 241 attempts.
# A6 keeps them:
#   - An attempt where the athlete started moving, no break was found within
#     MAX_BREAK_TIME_S, and the recording lasted at least
#     MIN_CENSOR_DURATION_S, is right-censored: time_to_break_s is set to
#     MAX_BREAK_TIME_S and break_censored is 1. Every detected break is at or
#     under MAX_BREAK_TIME_S, so a censored attempt ranks as the slowest.
#     Shorter recordings with no break stay missing, because "no break yet"
#     is not informative there.
#   - The player value is still the median over attempts. A player whose
#     median is MAX_BREAK_TIME_S is flagged db_break_censored.
#   - The two DB break-time tests use a rank method (RANK_TESTS): ranks inside
#     each draft class (average ranks for ties, so all censored players tie at
#     the slowest rank), demeaned inside the class, then Pearson on the
#     deviations, which is a pooled within-class Spearman correlation. The
#     Fisher interval for those rows uses the Fieller-Hartley-Pearson
#     variance 1.06 / (n - 3 - (k - 1)).
#   - Speed retention is defined at the break, so censored attempts have no
#     retention value. db_secondary_retention_epa keeps only attempts with a
#     detected break and stays a Pearson test.
#   - Scouting reading: the ordering among detected breakers is the signal.
#     Players at or past MAX_BREAK_TIME_S are context, not a ranked group.
MIN_CENSOR_DURATION_S: float = 5.0
SPEARMAN_VARIANCE_FACTOR: float = 1.06
RANK_TESTS: frozenset[str] = frozenset(
    {"db_primary_break_separation", "db_secondary_break_completion"}
)


@dataclass(frozen=True)
class PreRegisteredTest:
    """One within-draft-class association.

    `orient` is `flip` when a lower raw value is the more explosive or quicker
    movement (a faster stopwatch, or a shorter time to break). The correlation
    is then computed on the flipped value so the expected sign refers to
    "more of the trait", and the raw direction is still named in `predictor`.
    """

    test_id: str
    angle: str
    role: str
    predictor: str
    outcome: str
    orient: str
    expected_sign: int
    question: str


PREREGISTERED_TESTS: tuple[PreRegisteredTest, ...] = (
    PreRegisteredTest(
        test_id="te_primary_decel_separation",
        angle="TE",
        role="primary",
        predictor="te_skill_decel_magnitude",
        outcome="te_mean_separation",
        orient="as_is",
        expected_sign=1,
        question=(
            "Within draft class, does a harder brake on TE position drills "
            "go with more route separation when targeted?"
        ),
    ),
    PreRegisteredTest(
        test_id="te_secondary_ten_yd_separation",
        angle="TE",
        role="secondary",
        predictor="ten_yd_split",
        outcome="te_mean_separation",
        orient="flip",
        expected_sign=1,
        question=(
            "Within draft class, does a faster 10-yard split go with more "
            "route separation when targeted?"
        ),
    ),
    PreRegisteredTest(
        test_id="te_secondary_three_cone_completion",
        angle="TE",
        role="secondary",
        predictor="three_cone",
        outcome="te_completion_rate",
        orient="flip",
        expected_sign=1,
        question=(
            "Within draft class, does a faster 3-cone time go with a higher "
            "completion rate when targeted?"
        ),
    ),
    PreRegisteredTest(
        test_id="db_primary_break_separation",
        angle="DB",
        role="primary",
        predictor="db_break_time_s",
        outcome="db_mean_separation_allowed",
        orient="flip",
        expected_sign=-1,
        question=(
            "Within draft class, does a quicker backpedal-to-break transition "
            "go with less separation allowed?"
        ),
    ),
    PreRegisteredTest(
        test_id="db_secondary_retention_epa",
        angle="DB",
        role="secondary",
        predictor="db_speed_retention",
        outcome="db_mean_epa_allowed",
        orient="as_is",
        expected_sign=-1,
        question=(
            "Within draft class, does keeping more speed through the backpedal "
            "break go with less offensive EPA allowed?"
        ),
    ),
    PreRegisteredTest(
        test_id="db_secondary_break_completion",
        angle="DB",
        role="secondary",
        predictor="db_break_time_s",
        outcome="db_completion_rate_allowed",
        orient="flip",
        expected_sign=-1,
        question=(
            "Within draft class, does a quicker backpedal-to-break transition "
            "go with a lower completion rate allowed?"
        ),
    ),
)


def family_size() -> int:
    return len(PREREGISTERED_TESTS)


def bonferroni_alpha() -> float:
    return FAMILY_ALPHA / family_size()
