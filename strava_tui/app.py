"""Main Textual application for Strava Training Analytics."""
import webbrowser
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from strava_tui.auth.credentials import CredentialsManager
from strava_tui.ui.screens.auth_screen import AuthScreen
from strava_tui.ui.screens.main_screen import MainScreen


class StravaTuiApp(App):
    """Textual TUI Application for Strava Activity Distance & Analytics."""

    TITLE = "Strava Kilometers Analytics"
    SUB_TITLE = "Training Phrase & Year Distance Calculator"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("e", "export_html", "Export HTML"),
        Binding("o", "open_html", "Open in Browser"),
        Binding("r", "refresh_data", "Refresh Data"),
        Binding("a", "switch_auth", "Account / Login"),
        Binding("t", "toggle_dark", "Toggle Theme"),
    ]

    def __init__(self, default_mode: str = None, **kwargs):
        super().__init__(**kwargs)
        self.default_mode = default_mode
        self.creds_mgr = CredentialsManager()
        if default_mode:
            self.creds_mgr.set_auth_mode(default_mode)

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

    def action_export_html(self) -> None:
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.export_html()

    def action_open_html(self) -> None:
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.open_exported_html()

    def action_refresh_data(self) -> None:
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.load_data(force_refresh=True)

    def action_switch_auth(self) -> None:
        def on_auth_switched(mode: str):
            self.pop_screen()
            screen = self.screen
            if isinstance(screen, MainScreen):
                screen.initialize_client()

        self.push_screen(AuthScreen(on_auth_success=on_auth_switched))

    def action_toggle_dark(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"


def run_app(demo: bool = False):
    """Entry point helper to run the TUI application."""
    mode = "demo" if demo else None
    app = StravaTuiApp(default_mode=mode)
    app.run()
