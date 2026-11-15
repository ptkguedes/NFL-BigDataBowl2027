"""Column names published on the BDB 2027 Kaggle data page.

The pipeline reads a required subset. The full published lists are here so a
header check can tell a renamed file from a file that merely has extra columns.
`visitor_team_win_probility_added` is spelled the way the data page spells it.
"""

from __future__ import annotations

PLAYERS_COLUMNS: tuple[str, ...] = (
    "nfl_id",
    "display_name",
    "draft_year",
    "nfl_position",
    "birth_date",
    "college_name",
    "college_conference",
    "draft_round",
    "draft_pick_within_round",
    "draft_overall_pick",
)

COMBINE_RESULTS_COLUMNS: tuple[str, ...] = (
    "draft_year",
    "nfl_id",
    "combine_position",
    "combine_height",
    "combine_weight",
    "hand_size",
    "arm_length",
    "wing_span",
    "ten_yd_split",
    "forty",
    "vertical",
    "broad_jump",
    "three_cone",
    "short_shuttle",
    "bench_reps",
    "ngs_athleticism_score",
    "ngs_college_production_score",
    "ngs_final_score",
)

COMBINE_TRACKING_COLUMNS: tuple[str, ...] = (
    "draft_year",
    "event_id",
    "nfl_id",
    "entity_type",
    "time",
    "drill_type",
    "drill_name",
    "attempt",
    "x",
    "y",
    "s",
    "a",
    "dis",
    "dir",
)

CAREER_COLUMNS: tuple[str, ...] = (
    "nfl_id",
    "career_offensive_snaps",
    "career_defensive_snaps",
    "career_special_teams_snaps",
    "career_games_active",
    "career_games_started",
    "ap_all_pro_1st_team",
    "ap_all_pro_2nd_team",
    "pro_bowl_original_ballot",
)

PLAYER_PLAY_COLUMNS: tuple[str, ...] = (
    "game_id",
    "play_id",
    "team_abbr",
    "nfl_id",
    "lined_up_position",
    "play_description",
    "quarter",
    "down",
    "yards_to_go",
    "possession_team",
    "yardline_side",
    "yardline_number",
    "game_clock",
    "pre_snap_home_score",
    "pre_snap_visitor_score",
    "play_direction",
    "pre_snap_home_team_win_probability",
    "pre_snap_visitor_team_win_probability",
    "home_team_win_probability_added",
    "visitor_team_win_probility_added",
    "expected_points_added",
    "expected_points",
    "offense_formation",
    "receiver_alignment",
    "pass_result",
    "pass_length",
    "play_nullified_by_penalty",
    "penalty_yards",
    "pre_penalty_yards_gained",
    "yards_gained",
    "team_coverage_man_zone",
    "team_coverage_type",
    "in_motion_at_ball_snap",
    "target",
    "rec_yards",
    "rush_yards",
    "yards_after_catch",
    "fumble",
    "fumble_lost",
    "route_ran",
    "separation_at_pass_forward",
    "cushion",
    "expected_yards_after_catch",
    "dropback_duration",
    "extended_sack_allowed",
    "pass_rushers_encountered",
    "peak_pressure_probability_allowed",
    "pressure_allowed",
    "sack_allowed",
    "time_to_pressure_allowed",
    "blitzing",
    "player_get_off",
    "sack",
    "tackle",
    "assist",
    "caused_forced_fumble",
    "recovered_fumble",
    "tackle_for_loss",
    "time_to_pressure",
    "time_to_qb_hurry",
    "coverage_assignment",
    "coverage_assignment_at_snap",
    "quick_pressure",
    "unblocked_pressure",
)

GAMES_COLUMNS: tuple[str, ...] = (
    "game_id",
    "game_key",
    "season",
    "season_type",
    "week",
    "home_team_abbr",
    "visitor_team_abbr",
)

GAME_TRACKING_COLUMNS: tuple[str, ...] = (
    "game_id",
    "play_id",
    "nfl_id",
    "time",
    "x",
    "y",
    "s",
    "a",
    "dis",
    "o",
    "dir",
    "event",
)

# Alternate spellings accepted only when the published name is absent.
# The data page spells the visiting win-probability column with "probility".
COLUMN_ALTERNATES: dict[str, tuple[str, ...]] = {
    "visitor_team_win_probility_added": ("visitor_team_win_probability_added",),
}

OFFICIAL_FILENAMES: tuple[str, ...] = (
    "players.csv",
    "combine_results.csv",
    "combine_tracking.csv",
    "player_play.csv",
    "games.csv",
    "player_career_successes.csv",
    "game_tracking_2023.csv",
    "game_tracking_2024.csv",
    "game_tracking_2025.csv",
)

KAGGLE_INPUT_DIR = "/kaggle/input/nfl-big-data-bowl-2027"

PLAYERS_REQUIRED: tuple[str, ...] = (
    "nfl_id",
    "display_name",
    "draft_year",
    "nfl_position",
)
COMBINE_RESULTS_REQUIRED: tuple[str, ...] = (
    "draft_year",
    "nfl_id",
    "combine_position",
    "ten_yd_split",
    "forty",
    "three_cone",
)
COMBINE_TRACKING_REQUIRED: tuple[str, ...] = (
    "draft_year",
    "event_id",
    "nfl_id",
    "entity_type",
    "time",
    "drill_type",
    "drill_name",
    "attempt",
    "x",
    "y",
    "s",
    "a",
    "dir",
)
PLAYER_PLAY_REQUIRED: tuple[str, ...] = (
    "game_id",
    "play_id",
    "nfl_id",
    "lined_up_position",
    "pass_result",
    "play_nullified_by_penalty",
    "target",
    "expected_points_added",
    "separation_at_pass_forward",
    "team_abbr",
    "coverage_assignment",
)
GAMES_REQUIRED: tuple[str, ...] = ("game_id", "season", "season_type", "week")
CAREER_REQUIRED: tuple[str, ...] = (
    "nfl_id",
    "career_offensive_snaps",
    "career_defensive_snaps",
)
GAME_TRACKING_REQUIRED: tuple[str, ...] = (
    "game_id",
    "play_id",
    "nfl_id",
    "x",
    "y",
    "event",
)
