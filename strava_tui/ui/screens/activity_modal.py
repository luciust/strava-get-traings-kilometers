"""Modal dialog showing full details of a selected activity."""
import webbrowser
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from strava_tui.data.models import Activity


class ActivityDetailModal(ModalScreen):
    """Modal screen displaying detailed activity telemetry."""

    DEFAULT_CSS = """
    ActivityDetailModal {
        align: center middle;
    }
    #detail-container {
        width: 65;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #detail-title {
        text-style: bold;
        color: #FC4C02;
        margin-bottom: 1;
        text-align: center;
    }
    .detail-row {
        height: 1;
        margin: 0 0;
    }
    .detail-key {
        width: 22;
        color: $text-muted;
        text-style: bold;
    }
    .detail-val {
        color: $text;
        text-style: bold;
    }
    #buttons-bar {
        margin-top: 1;
        align: center middle;
        height: auto;
    }
    #buttons-bar Button {
        margin: 0 1;
    }
    """

    def __init__(self, activity: Activity):
        super().__init__()
        self.activity = activity

    def compose(self) -> ComposeResult:
        with Container(id="detail-container"):
            yield Label(f"🏃 {self.activity.name}", id="detail-title")

            with Horizontal(classes="detail-row"):
                yield Label("Sport Type:", classes="detail-key")
                yield Label(f"{self.activity.sport_type}", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Date & Time:", classes="detail-key")
                yield Label(f"{self.activity.date_formatted}", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Distance:", classes="detail-key")
                yield Label(f"{self.activity.distance_km:,.2f} km ({self.activity.distance_meters:,.0f} m)", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Moving Time:", classes="detail-key")
                yield Label(f"{self.activity.moving_time_formatted}", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Elevation Gain:", classes="detail-key")
                yield Label(f"{self.activity.total_elevation_gain:,.1f} m", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Average Speed:", classes="detail-key")
                yield Label(f"{self.activity.average_speed_kmh} km/h", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Average Pace:", classes="detail-key")
                yield Label(f"{self.activity.pace_per_km}", classes="detail-val")

            if self.activity.average_heartrate:
                with Horizontal(classes="detail-row"):
                    yield Label("Heart Rate (Avg/Max):", classes="detail-key")
                    max_hr_str = f" / {self.activity.max_heartrate:.0f}" if self.activity.max_heartrate else ""
                    yield Label(f"{self.activity.average_heartrate:.0f}{max_hr_str} bpm", classes="detail-val")

            with Horizontal(classes="detail-row"):
                yield Label("Strava URL:", classes="detail-key")
                yield Label(f"{self.activity.strava_url}", classes="detail-val")

            with Horizontal(id="buttons-bar"):
                yield Button("Open in Browser", id="btn-open-browser", variant="primary")
                yield Button("Close (Esc)", id="btn-close", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open-browser":
            try:
                webbrowser.open(self.activity.strava_url)
            except Exception:
                pass
        elif event.button.id == "btn-close":
            self.app.pop_screen()
