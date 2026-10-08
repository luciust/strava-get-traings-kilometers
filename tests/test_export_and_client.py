"""Tests for MockClient, HtmlExporter, and CredentialsManager."""
import os
import tempfile
from pathlib import Path
from strava_tui.auth.credentials import CredentialsManager
from strava_tui.client.mock_client import MockStravaClient
from strava_tui.data.analyzer import ActivityAnalyzer
from strava_tui.export.html_exporter import HtmlExporter


def test_mock_client_and_filtering():
    client = MockStravaClient(athlete_name="Jordan Triathlete")
    athlete = client.get_athlete()
    assert athlete.full_name == "Jordan Triathlete"
    assert athlete.auth_mode == "demo"

    activities = client.get_activities_for_year(2025)
    assert len(activities) > 50

    # Test filtering for "Interval"
    stats = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="Interval",
    )
    assert stats.matching_count > 0
    assert stats.total_distance_km > 0
    assert stats.year == 2025
    assert stats.phrase == "Interval"


def test_html_exporter(tmp_path):
    client = MockStravaClient()
    athlete = client.get_athlete()
    activities = client.get_activities_for_year(2025)

    stats = ActivityAnalyzer.filter_and_aggregate(
        activities=activities,
        year=2025,
        phrase="Interval",
    )

    out_file = tmp_path / "test_report.html"
    exported_path = HtmlExporter.export(stats, athlete, out_file)

    assert exported_path.exists()
    content = exported_path.read_text(encoding="utf-8")

    # Check key elements in HTML
    assert "chart.umd.min.js" in content
    assert "confetti.browser.min.js" in content
    assert "kpi-km" in content
    assert "monthlyChart" in content
    assert "sportChart" in content
    assert "cumulativeChart" in content
    assert "activitiesTable" in content
    assert str(stats.total_distance_km) in content
    assert athlete.full_name in content


def test_credentials_manager(tmp_path):
    cfg_file = tmp_path / "credentials.json"
    mgr = CredentialsManager(config_path=cfg_file)

    assert mgr.load() == {}

    mgr.save({"client_id": "12345", "access_token": "secret_token"})
    loaded = mgr.load()
    assert loaded["client_id"] == "12345"
    assert loaded["access_token"] == "secret_token"

    creds = mgr.get_api_credentials()
    assert creds["client_id"] == "12345"
    assert creds["access_token"] == "secret_token"

    mgr.set_auth_mode("demo")
    assert mgr.get_auth_mode() == "demo"
