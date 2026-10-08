"""Main dashboard screen for Strava activity analysis, filtering, and export."""
import os
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

from strava_tui.auth.credentials import CredentialsManager
from strava_tui.client.api_client import StravaApiClient
from strava_tui.client.base import BaseStravaClient
from strava_tui.client.mock_client import MockStravaClient
from strava_tui.client.web_client import StravaWebClient
from strava_tui.data.analyzer import ActivityAnalyzer
from strava_tui.data.models import Activity, AggregatedStats, AthleteProfile
from strava_tui.export.html_exporter import HtmlExporter
from strava_tui.ui.screens.activity_modal import ActivityDetailModal
from strava_tui.ui.widgets.ascii_chart import MonthlyBarChart, SportBreakdownTable
from strava_tui.ui.widgets.stat_card import StatCard


class MainScreen(Screen):
    """Main dashboard screen."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
        background: $background;
    }
    #top-filter-bar {
        height: auto;
        padding: 1 1;
        background: $surface;
        border-bottom: solid $accent;
    }
    .filter-input {
        width: 1fr;
        margin-right: 1;
    }
    #year-input {
        width: 12;
        margin-right: 1;
    }
    #sport-select {
        width: 18;
        margin-right: 1;
    }
    .action-btn {
        margin-right: 1;
        min-width: 12;
    }
    #stats-cards-bar {
        height: auto;
        padding: 0 1;
        margin-top: 1;
    }
    #content-split {
        height: 1fr;
        margin-top: 1;
    }
    #left-panel {
        width: 44;
        height: 100%;
        margin-right: 1;
    }
    #right-panel {
        width: 1fr;
        height: 100%;
    }
    #activities-table {
        height: 100%;
        border: solid $accent;
    }
    #status-bar {
        height: 1;
        padding: 0 1;
        background: $surface-darken-1;
        color: $text-muted;
    }
    """

    def __init__(self):
        super().__init__()
        self.creds_mgr = CredentialsManager()
        self.client: Optional[BaseStravaClient] = None
        self.athlete: Optional[AthleteProfile] = None
        self.all_activities_in_year: List[Activity] = []
        self.current_stats: Optional[AggregatedStats] = None
        self.last_exported_html: Optional[Path] = None

    def compose(self) -> ComposeResult:
        current_year = str(datetime.now().year)

        # Top Control & Filter Bar
        with Horizontal(id="top-filter-bar"):
            yield Input(
                placeholder="Search phrase in name (e.g. 'Interval', 'Commute', 'Long Run')...",
                id="search-phrase",
                classes="filter-input",
            )
            yield Input(value=current_year, id="year-input")
            yield Select(
                [
                    ("All Sports", "all"),
                    ("Run", "Run"),
                    ("Ride", "Ride"),
                    ("VirtualRide", "VirtualRide"),
                    ("Swim", "Swim"),
                    ("Hike", "Hike"),
                    ("Workout", "Workout"),
                ],
                value="all",
                id="sport-select",
            )
            yield Button("🔍 Filter", variant="primary", id="btn-apply-filter", classes="action-btn")
            yield Button("🔄 Fetch Strava", variant="default", id="btn-fetch-data", classes="action-btn")
            yield Button("✨ Export HTML", variant="success", id="btn-export-html", classes="action-btn")
            yield Button("🌐 Open Report", variant="warning", id="btn-open-browser", classes="action-btn")
            yield Button("👤 Account", variant="default", id="btn-switch-account", classes="action-btn")

        # KPI Metric Cards
        with Horizontal(id="stats-cards-bar"):
            yield StatCard("Combined Distance", "0.0", "km", "Matching workouts", is_hero=True, id="card-km")
            yield StatCard("Trainings Found", "0", "", "In selected year", id="card-count")
            yield StatCard("Moving Time", "0h 00m", "", "Time in motion", id="card-time")
            yield StatCard("Elevation Gain", "0.0", "m", "Vertical climbing", id="card-elev")
            yield StatCard("Average Workout", "0.0", "km", "Avg speed: 0 km/h", id="card-avg")

        # Main Split Content: Charts on Left, Activities Table on Right
        with Horizontal(id="content-split"):
            with VerticalScroll(id="left-panel"):
                yield MonthlyBarChart(id="monthly-chart")
                yield SportBreakdownTable(id="sport-table")

            with Vertical(id="right-panel"):
                table = DataTable(id="activities-table")
                table.cursor_type = "row"
                table.zebra_stripes = True
                yield table

        yield Static("Ready.", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#activities-table", DataTable)
        table.add_columns(
            "Date",
            "Training Name",
            "Sport",
            "Distance (km)",
            "Moving Time",
            "Elevation (m)",
            "Pace / Speed",
        )

        self.initialize_client()

    def initialize_client(self):
        auth_mode = self.creds_mgr.get_auth_mode()
        status_bar = self.query_one("#status-bar", Static)

        if auth_mode == "demo":
            self.client = MockStravaClient()
            self.athlete = self.client.get_athlete()
            status_bar.update(f"Running in Demo Mode as {self.athlete.full_name}. Fetching sample activities...")
            self.load_data()
        elif auth_mode == "api":
            try:
                self.client = StravaApiClient(self.creds_mgr)
                self.athlete = self.client.get_athlete()
                status_bar.update(f"Connected to Strava API as {self.athlete.full_name}.")
                self.load_data()
            except Exception as e:
                status_bar.update(f"API Error: {str(e)}. Please reconnect.")
        elif auth_mode == "session":
            try:
                self.client = StravaWebClient(self.creds_mgr)
                self.athlete = self.client.get_athlete()
                status_bar.update(f"Logged into Strava Web Session as {self.athlete.full_name}.")
                self.load_data()
            except Exception as e:
                status_bar.update(f"Web Session Error: {str(e)}. Please log in again.")
        else:
            status_bar.update("No active connection. Opening authentication screen...")
            from strava_tui.ui.screens.auth_screen import AuthScreen
            self.app.push_screen(AuthScreen(on_auth_success=self.on_auth_completed))

    def on_auth_completed(self, mode: str):
        self.app.pop_screen()
        self.initialize_client()

    def load_data(self, force_refresh: bool = False):
        year_str = self.query_one("#year-input", Input).value.strip()
        try:
            year = int(year_str)
        except ValueError:
            year = datetime.now().year
            self.query_one("#year-input", Input).value = str(year)

        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(f"Fetching activities for year {year}...")

        def fetch_bg():
            try:
                if isinstance(self.client, StravaApiClient) and force_refresh:
                    activities = self.client.get_activities_for_year(year, use_cache=False)
                elif isinstance(self.client, StravaWebClient) and force_refresh:
                    activities = self.client.get_activities_for_year(year, use_cache=False)
                elif self.client:
                    activities = self.client.get_activities_for_year(year)
                else:
                    activities = []

                self.all_activities_in_year = activities

                def on_done():
                    self.apply_filter()
                    status_bar.update(
                        f"Loaded {len(self.all_activities_in_year)} activities for {year}."
                    )

                self.app.call_from_thread(on_done)
            except Exception as e:
                self.app.call_from_thread(
                    status_bar.update,
                    f"[red]Failed to load activities: {str(e)}[/red]",
                )

        threading.Thread(target=fetch_bg, daemon=True).start()

    def apply_filter(self):
        phrase = self.query_one("#search-phrase", Input).value
        year_str = self.query_one("#year-input", Input).value.strip()
        sport = self.query_one("#sport-select", Select).value

        try:
            year = int(year_str)
        except ValueError:
            year = datetime.now().year

        # Compute aggregate statistics
        self.current_stats = ActivityAnalyzer.filter_and_aggregate(
            activities=self.all_activities_in_year,
            year=year,
            phrase=phrase,
            sport_type=sport if sport != "all" else None,
        )

        # Update StatCards
        self.query_one("#card-km", StatCard).update_values(
            f"{self.current_stats.total_distance_km:,.1f}",
            subtitle=f"Phrase: '{phrase}'" if phrase else "All activities",
        )
        self.query_one("#card-count", StatCard).update_values(
            str(self.current_stats.matching_count),
            subtitle=f"Of {self.current_stats.total_activities_in_year} in {year}",
        )
        self.query_one("#card-time", StatCard).update_values(
            self.current_stats.total_moving_time_formatted
        )
        self.query_one("#card-elev", StatCard).update_values(
            f"{self.current_stats.total_elevation_gain_m:,.0f}"
        )
        self.query_one("#card-avg", StatCard).update_values(
            f"{self.current_stats.avg_distance_km:,.1f}",
            subtitle=f"Avg Speed: {self.current_stats.avg_speed_kmh} km/h",
        )

        # Update Charts
        self.query_one("#monthly-chart", MonthlyBarChart).update_stats(
            self.current_stats.monthly_breakdown
        )
        self.query_one("#sport-table", SportBreakdownTable).update_stats(
            self.current_stats.sport_breakdown
        )

        # Update DataTable
        table = self.query_one("#activities-table", DataTable)
        table.clear()

        for a in self.current_stats.activities:
            speed_pace = a.pace_per_km if "run" in a.sport_type.lower() else f"{a.average_speed_kmh} km/h"
            table.add_row(
                a.start_date.strftime("%Y-%m-%d"),
                a.name,
                a.sport_type,
                f"{a.distance_km:,.2f}",
                a.moving_time_formatted,
                f"{a.total_elevation_gain:,.0f}",
                speed_pace,
                key=a.id,
            )

        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(
            f"Filtered: {self.current_stats.matching_count} matching '{phrase or '*'}' "
            f"combined for [bold #FC4C02]{self.current_stats.total_distance_km:,.1f} km[/bold #FC4C02]."
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-apply-filter":
            self.apply_filter()
        elif btn_id == "btn-fetch-data":
            self.load_data(force_refresh=True)
        elif btn_id == "btn-export-html":
            self.export_html()
        elif btn_id == "btn-open-browser":
            self.open_exported_html()
        elif btn_id == "btn-switch-account":
            self.app.action_switch_auth()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.apply_filter()

    def on_select_changed(self, event: Select.Changed) -> None:
        self.apply_filter()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key.value
        matched = [a for a in (self.current_stats.activities if self.current_stats else []) if a.id == row_key]
        if matched:
            self.app.push_screen(ActivityDetailModal(matched[0]))

    def export_html(self):
        if not self.current_stats or not self.athlete:
            self.notify("No data loaded to export.", severity="warning")
            return

        status_bar = self.query_one("#status-bar", Static)
        try:
            path = HtmlExporter.export(self.current_stats, self.athlete)
            self.last_exported_html = path
            status_bar.update(f"[green]HTML exported successfully to: {path}[/green]")
            self.notify(f"Exported flashy report to {path.name}", title="HTML Export")
        except Exception as e:
            status_bar.update(f"[red]Export failed: {str(e)}[/red]")
            self.notify(f"Export failed: {str(e)}", severity="error")

    def open_exported_html(self):
        if not self.last_exported_html or not self.last_exported_html.exists():
            # Export first if not exported yet
            self.export_html()

        if self.last_exported_html and self.last_exported_html.exists():
            try:
                webbrowser.open(f"file://{self.last_exported_html.resolve()}")
                self.notify("Opened report in browser", title="Browser Launch")
            except Exception as e:
                self.notify(f"Could not open browser: {e}", severity="error")
