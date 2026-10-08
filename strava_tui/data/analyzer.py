"""Data analysis and aggregation engine for Strava activities."""
import calendar
import re
from typing import List, Optional
from datetime import datetime

from strava_tui.data.models import Activity, AggregatedStats, MonthlyStat, SportStat


class ActivityAnalyzer:
    """Analyzes and filters Strava activities based on criteria like year and name phrase."""

    @staticmethod
    def filter_and_aggregate(
        activities: List[Activity],
        year: int,
        phrase: str = "",
        sport_type: Optional[str] = None,
        case_sensitive: bool = False,
        use_regex: bool = False,
    ) -> AggregatedStats:
        """
        Filter activities by year, name phrase, and sport type, then compute combined kilometers and stats.
        """
        # Count all activities in the given year
        activities_in_year = [a for a in activities if a.start_date.year == year]
        total_in_year = len(activities_in_year)

        # Prepare phrase matcher
        clean_phrase = phrase.strip()
        regex_pattern = None
        if clean_phrase and use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex_pattern = re.compile(clean_phrase, flags)
            except re.error:
                regex_pattern = None

        matched_activities: List[Activity] = []
        for activity in activities_in_year:
            # Check sport type if specified
            if sport_type and sport_type.lower() != "all":
                if activity.sport_type.lower() != sport_type.lower():
                    continue

            # Check phrase match
            if clean_phrase:
                if regex_pattern:
                    if not regex_pattern.search(activity.name):
                        continue
                else:
                    target_name = activity.name if case_sensitive else activity.name.lower()
                    search_term = clean_phrase if case_sensitive else clean_phrase.lower()
                    if search_term not in target_name:
                        continue

            matched_activities.append(activity)

        # Sort matched activities descending by date
        matched_activities.sort(key=lambda a: a.start_date, reverse=True)

        # Calculate totals
        total_distance_km = sum(a.distance_km for a in matched_activities)
        total_moving_time = sum(a.moving_time_seconds for a in matched_activities)
        total_elevation_gain = sum(a.total_elevation_gain for a in matched_activities)
        matching_count = len(matched_activities)

        avg_distance_km = round(total_distance_km / matching_count, 2) if matching_count > 0 else 0.0
        avg_speed_kmh = (
            round((sum(a.distance_meters for a in matched_activities) / total_moving_time) * 3.6, 2)
            if total_moving_time > 0
            else 0.0
        )

        longest_activity = (
            max(matched_activities, key=lambda a: a.distance_km) if matched_activities else None
        )
        highest_climb = (
            max(matched_activities, key=lambda a: a.total_elevation_gain) if matched_activities else None
        )

        # Monthly breakdown (1 through 12)
        monthly_stats: List[MonthlyStat] = []
        for month_num in range(1, 13):
            month_name = calendar.month_abbr[month_num]
            month_activities = [a for a in matched_activities if a.start_date.month == month_num]
            m_count = len(month_activities)
            m_km = round(sum(a.distance_km for a in month_activities), 2)
            m_time = sum(a.moving_time_seconds for a in month_activities)
            m_elev = round(sum(a.total_elevation_gain for a in month_activities), 1)

            monthly_stats.append(
                MonthlyStat(
                    month_number=month_num,
                    month_name=month_name,
                    count=m_count,
                    distance_km=m_km,
                    moving_time_seconds=m_time,
                    elevation_gain_m=m_elev,
                )
            )

        # Sport breakdown
        sport_groups = {}
        for a in matched_activities:
            sport = a.sport_type or "Unknown"
            if sport not in sport_groups:
                sport_groups[sport] = []
            sport_groups[sport].append(a)

        sport_stats: List[SportStat] = []
        for sport, items in sorted(sport_groups.items(), key=lambda x: sum(a.distance_km for a in x[1]), reverse=True):
            sport_stats.append(
                SportStat(
                    sport_type=sport,
                    count=len(items),
                    distance_km=round(sum(a.distance_km for a in items), 2),
                    moving_time_seconds=sum(a.moving_time_seconds for a in items),
                    elevation_gain_m=round(sum(a.total_elevation_gain for a in items), 1),
                )
            )

        return AggregatedStats(
            year=year,
            phrase=clean_phrase,
            total_activities_in_year=total_in_year,
            matching_count=matching_count,
            total_distance_km=round(total_distance_km, 2),
            total_moving_time_seconds=total_moving_time,
            total_elevation_gain_m=round(total_elevation_gain, 1),
            avg_distance_km=avg_distance_km,
            avg_speed_kmh=avg_speed_kmh,
            longest_activity=longest_activity,
            highest_climb_activity=highest_climb,
            monthly_breakdown=monthly_stats,
            sport_breakdown=sport_stats,
            activities=matched_activities,
        )
