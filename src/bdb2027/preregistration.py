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
