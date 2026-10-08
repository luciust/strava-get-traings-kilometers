"""StatCard widget for displaying summary metrics in Textual TUI."""
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static


class StatCard(Static):
    """A card showing a metric title, value, unit, and subtitle."""

    DEFAULT_CSS = """
    StatCard {
        height: 5;
        min-width: 18;
        margin: 0 1;
        background: $surface;
        border: round $primary;
        padding: 0 1;
    }
    StatCard.hero-card {
        border: heavy $accent;
        background: $surface-lighten-1;
    }
    """

    def __init__(
        self,
        title: str,
        value: str,
        unit: str = "",
        subtitle: str = "",
        is_hero: bool = False,
        id: str = None,
    ):
        super().__init__(id=id)
        self.title_text = title
        self.value_text = value
        self.unit_text = unit
        self.subtitle_text = subtitle
        self.is_hero = is_hero
        if is_hero:
            self.add_class("hero-card")

    def update_values(self, value: str, subtitle: str = ""):
        self.value_text = value
        if subtitle:
            self.subtitle_text = subtitle
        self.refresh()

    def render(self):
        text = Text()
        # Title
        text.append(f"{self.title_text.upper()}\n", style="bold dim")
        # Value & Unit
        value_style = "bold #FC4C02" if self.is_hero else "bold white"
        text.append(self.value_text, style=value_style)
        if self.unit_text:
            text.append(f" {self.unit_text}", style="dim")
        # Subtitle
        if self.subtitle_text:
            text.append(f"\n{self.subtitle_text}", style="italic green" if not self.is_hero else "dim #FF8A00")

        return text
