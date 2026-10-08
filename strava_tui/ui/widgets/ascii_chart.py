"""Text and bar chart widget for displaying monthly and sport breakdowns in terminal."""
from typing import List
from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from strava_tui.data.models import MonthlyStat, SportStat


class MonthlyBarChart(Static):
    """Renders a text bar chart showing monthly kilometers progression."""

    DEFAULT_CSS = """
    MonthlyBarChart {
        height: auto;
        border: solid $accent;
        padding: 0 1;
        background: $surface;
    }
    """

    def __init__(self, monthly_stats: List[MonthlyStat] = None, id: str = None):
        super().__init__(id=id)
        self.stats = monthly_stats or []

    def update_stats(self, stats: List[MonthlyStat]):
        self.stats = stats
        self.refresh()

    def render(self):
        table = Table(
            title="📅 Monthly Kilometers Breakdown",
            title_style="bold #FC4C02",
            show_header=True,
            header_style="bold dim",
            expand=True,
            box=None,
        )
        table.add_column("Month", width=6, style="bold cyan")
        table.add_column("Bar Graph", ratio=1)
        table.add_column("Kilometers", justify="right", width=12, style="bold white")
        table.add_column("Count", justify="right", width=6, style="dim")

        max_km = max((m.distance_km for m in self.stats), default=1.0)
        if max_km <= 0:
            max_km = 1.0

        bar_chars = "█"
        max_bar_len = 24

        for m in self.stats:
            ratio = m.distance_km / max_km
            bar_len = int(ratio * max_bar_len)
            bar_text = Text()

            if m.distance_km > 0:
                bar_text.append(bar_chars * bar_len, style="#FC4C02")
                # Show percentage or sub-bar
                if bar_len == 0:
                    bar_text.append("▏", style="#FC4C02")
            else:
                bar_text.append("·", style="dim")

            table.add_row(
                m.month_name,
                bar_text,
                f"{m.distance_km:,.1f} km",
                f"({m.count})",
            )

        return table


class SportBreakdownTable(Static):
    """Renders sport breakdown in text form."""

    DEFAULT_CSS = """
    SportBreakdownTable {
        height: auto;
        border: solid $accent;
        padding: 0 1;
        background: $surface;
    }
    """

    def __init__(self, sport_stats: List[SportStat] = None, id: str = None):
        super().__init__(id=id)
        self.stats = sport_stats or []

    def update_stats(self, stats: List[SportStat]):
        self.stats = stats
        self.refresh()

    def render(self):
        table = Table(
            title="🏅 Breakdown by Sport",
            title_style="bold #38BDF8",
            show_header=True,
            header_style="bold dim",
            expand=True,
            box=None,
        )
        table.add_column("Sport", style="bold yellow")
        table.add_column("Distance", justify="right", style="bold white")
        table.add_column("Workouts", justify="right", style="dim")
        table.add_column("Elevation", justify="right", style="green")

        if not self.stats:
            table.add_row("No activities", "0.0 km", "0", "0 m")
            return table

        for s in self.stats:
            table.add_row(
                s.sport_type,
                f"{s.distance_km:,.1f} km",
                str(s.count),
                f"{s.elevation_gain_m:,.0f} m",
            )

        return table
