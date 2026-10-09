"""Tests for ActivityAnalyzer and data models."""
import pytest
from datetime import datetime, timezone
from strava_tui.data.models import Activity
from strava_tui.data.analyzer import ActivityAnalyzer


def make_activity(id_str, name, km, sport="Run", year=2025, month=5):
    return Activity(
        id=id_str,
        name=name,
        distance_meters=km * 1000.0,
        moving_time_seconds=int(km * 300),  # 5 min/km
        elapsed_time_seconds=int(km * 320),
        total_elevation_gain=km * 10.0,
        sport_type=sport,
        start_date=datetime(year, month, 10, 10, 0, 0, tzinfo=timezone.utc),
    )


def test_filter_by_phrase():
    activities = [
        make_activity("1", "Morning Interval Training", 10.0, "Run", 2025, 3),
        make_activity("2", "Easy Recovery Jog", 5.0, "Run", 2025, 4),
        make_activity("3", "Track Intervals 400m", 8.0, "Run", 2025, 5),
        make_activity("4", "Interval workout ride", 30.0, "Ride", 2024, 5),  # different year
    ]

    # Test year 2025 + phrase "Interval"
    stats = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="Interval",
    )

    assert stats.year == 2025
    assert stats.phrase == "Interval"
    assert stats.total_activities_in_year == 3
    assert stats.matching_count == 2
    assert stats.total_distance_km == 18.0  # 10.0 + 8.0
    assert stats.avg_distance_km == 9.0


def test_filter_case_insensitive():
    activities = [
        make_activity("1", "threshold intervals", 12.5, "Run", 2025, 2),
        make_activity("2", "INTERVAL SESSION", 10.0, "Run", 2025, 2),
    ]

    stats = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="interval",
    )

    assert stats.matching_count == 2
    assert stats.total_distance_km == 22.5


def test_sport_filter():
    activities = [
        make_activity("1", "Interval Run", 10.0, "Run", 2025, 1),
        make_activity("2", "Interval Ride", 40.0, "Ride", 2025, 1),
    ]

    stats_run = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="Interval",
        sport_type="Run",
    )
    assert stats_run.matching_count == 1
    assert stats_run.total_distance_km == 10.0

    stats_ride = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="Interval",
        sport_type="Ride",
    )
    assert stats_ride.matching_count == 1
    assert stats_ride.total_distance_km == 40.0

    # Test with Select.NULL or non-string
    from textual.widgets import Select
    stats_null = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="Interval",
        sport_type=Select.NULL,
    )
    assert stats_null.matching_count == 2
    assert stats_null.total_distance_km == 50.0


def test_monthly_breakdown():
    activities = [
        make_activity("1", "Intervals Jan", 10.0, "Run", 2025, 1),
        make_activity("2", "Intervals Mar", 15.0, "Run", 2025, 3),
        make_activity("3", "Intervals Mar part 2", 5.0, "Run", 2025, 3),
    ]

    stats = ActivityAnalyzer.filter_and_aggregate(activities=activities, year=2025, phrase="Intervals")
    assert len(stats.monthly_breakdown) == 12

    jan = next(m for m in stats.monthly_breakdown if m.month_number == 1)
    assert jan.distance_km == 10.0
    assert jan.count == 1

    mar = next(m for m in stats.monthly_breakdown if m.month_number == 3)
    assert mar.distance_km == 20.0
    assert mar.count == 2
