"""Authentication screen for selecting and configuring Strava access."""
import threading
import webbrowser
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static, TabbedContent, TabPane

from strava_tui.auth.api_oauth import StravaOAuthManager
from strava_tui.auth.credentials import CredentialsManager
from strava_tui.auth.web_session import StravaSessionLogin


class AuthScreen(Screen):
    """Screen for choosing login or API authentication method."""

    DEFAULT_CSS = """
    AuthScreen {
        align: center middle;
        background: $background;
    }
    #auth-box {
        width: 78;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #app-banner {
        text-align: center;
        color: #FC4C02;
        text-style: bold;
        margin-bottom: 1;
    }
    #app-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    .field-label {
        color: $text;
        text-style: bold;
        margin-top: 1;
    }
    .help-text {
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }
    .status-msg {
        margin-top: 1;
        text-align: center;
        text-style: bold;
    }
    .action-btn {
        margin-top: 1;
        width: 100%;
    }
    """

    def __init__(self, on_auth_success=None):
        super().__init__()
        self.creds_mgr = CredentialsManager()
        self.on_auth_success = on_auth_success
        self.oauth_manager = None

    def compose(self) -> ComposeResult:
        with Container(id="auth-box"):
            yield Static("🚴 Strava Training Analytics TUI", id="app-banner")
            yield Static("Select your connection method to get training kilometers", id="app-subtitle")

            with TabbedContent():
                # Tab 1: Strava API (OAuth2)
                with TabPane("1. API OAuth (Recommended)", id="tab-api"):
                    yield Label("Strava Client ID:", classes="field-label")
                    yield Input(placeholder="e.g. 123456", id="input-client-id")
                    yield Label("Strava Client Secret:", classes="field-label")
                    yield Input(placeholder="e.g. 40-character hex secret", password=True, id="input-client-secret")
                    yield Static(
                        "ℹ️ Get these free at: strava.com/settings/api (Set Callback Domain: localhost)",
                        classes="help-text",
                    )
                    yield Button("🚀 Connect with Strava (Opens Browser)", variant="primary", id="btn-oauth", classes="action-btn")

                # Tab 2: Direct Token
                with TabPane("2. Direct Token", id="tab-token"):
                    yield Label("Strava Personal Access Token:", classes="field-label")
                    yield Input(placeholder="e.g. da39a3ee5e6b4b0d3255bfef95601890afd80709", password=True, id="input-access-token")
                    yield Static(
                        "ℹ️ Found on your Strava API Application settings page.",
                        classes="help-text",
                    )
                    yield Button("🔑 Connect with Token", variant="success", id="btn-token", classes="action-btn")

                # Tab 3: Web Login (Username & Password)
                with TabPane("3. Password Login", id="tab-login"):
                    yield Label("Strava Email / Username:", classes="field-label")
                    yield Input(placeholder="athlete@example.com", id="input-login-email")
                    yield Label("Strava Password:", classes="field-label")
                    yield Input(placeholder="Your Strava Password", password=True, id="input-login-password")
                    yield Static(
                        "ℹ️ Authenticates directly with strava.com session.",
                        classes="help-text",
                    )
                    yield Button("🔓 Sign In with Password", variant="primary", id="btn-login", classes="action-btn")

                # Tab 4: Demo Mode
                with TabPane("4. Demo Mode (Sample Data)", id="tab-demo"):
                    yield Static(
                        "Want to test the app without entering credentials right now?\n\n"
                        "Demo mode loads realistic full-year training activities (Intervals, Rides, Commutes, Runs) "
                        "allowing you to test phrase filtering, kilometer totals, and HTML export immediately!",
                        classes="help-text",
                    )
                    yield Button("🌟 Launch in Demo Mode", variant="warning", id="btn-demo", classes="action-btn")

            yield Static("", id="auth-status-msg", classes="status-msg")

    def on_mount(self) -> None:
        # Pre-populate saved client_id if available
        creds = self.creds_mgr.get_api_credentials()
        if creds.get("client_id"):
            self.query_one("#input-client-id", Input).value = str(creds["client_id"])
        if creds.get("client_secret"):
            self.query_one("#input-client-secret", Input).value = str(creds["client_secret"])
        if creds.get("access_token"):
            self.query_one("#input-access-token", Input).value = str(creds["access_token"])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        status_lbl = self.query_one("#auth-status-msg", Static)

        if button_id == "btn-demo":
            self.creds_mgr.set_auth_mode("demo")
            status_lbl.update("[green]Launching Demo Mode...[/green]")
            self._finish_auth("demo")

        elif button_id == "btn-token":
            token = self.query_one("#input-access-token", Input).value.strip()
            if not token:
                status_lbl.update("[red]Please enter an Access Token.[/red]")
                return

            status_lbl.update("[yellow]Verifying Access Token with Strava...[/yellow]")

            def verify_bg():
                ok, athlete, err = StravaOAuthManager.verify_token(token)
                if ok and athlete:
                    self.creds_mgr.save({
                        "access_token": token,
                        "auth_mode": "api",
                        "athlete": {
                            "id": athlete.id,
                            "username": athlete.username,
                            "firstname": athlete.firstname,
                            "lastname": athlete.lastname,
                        },
                    })
                    self.app.call_from_thread(self._finish_auth, "api")
                else:
                    self.app.call_from_thread(
                        status_lbl.update,
                        f"[red]Token Verification Failed: {err}[/red]",
                    )

            threading.Thread(target=verify_bg, daemon=True).start()

        elif button_id == "btn-oauth":
            client_id = self.query_one("#input-client-id", Input).value.strip()
            client_secret = self.query_one("#input-client-secret", Input).value.strip()

            if not client_id or not client_secret:
                status_lbl.update("[red]Please provide both Client ID and Client Secret.[/red]")
                return

            status_lbl.update("[yellow]Starting local server & opening browser...[/yellow]")

            def oauth_bg():
                try:
                    self.oauth_manager = StravaOAuthManager(client_id, client_secret)
                    auth_url = self.oauth_manager.get_authorization_url()
                    webbrowser.open(auth_url)
                    self.app.call_from_thread(
                        status_lbl.update,
                        f"[cyan]Waiting for authorization in browser on port {self.oauth_manager.port}...[/cyan]",
                    )
                    code = self.oauth_manager.listen_for_code(timeout_seconds=90)
                    token_data = self.oauth_manager.exchange_code_for_token(code)
                    athlete_data = token_data.get("athlete", {})

                    self.creds_mgr.save({
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "access_token": token_data.get("access_token"),
                        "refresh_token": token_data.get("refresh_token"),
                        "expires_at": token_data.get("expires_at"),
                        "auth_mode": "api",
                        "athlete": {
                            "id": str(athlete_data.get("id", "")),
                            "username": athlete_data.get("username", ""),
                            "firstname": athlete_data.get("firstname", ""),
                            "lastname": athlete_data.get("lastname", ""),
                        },
                    })
                    self.app.call_from_thread(self._finish_auth, "api")
                except Exception as e:
                    self.app.call_from_thread(
                        status_lbl.update,
                        f"[red]OAuth Error: {str(e)}[/red]",
                    )

            threading.Thread(target=oauth_bg, daemon=True).start()

        elif button_id == "btn-login":
            email = self.query_one("#input-login-email", Input).value.strip()
            password = self.query_one("#input-login-password", Input).value.strip()

            if not email or not password:
                status_lbl.update("[red]Please enter both email and password.[/red]")
                return

            status_lbl.update("[yellow]Authenticating with Strava...[/yellow]")

            def login_bg():
                login_helper = StravaSessionLogin()
                ok, athlete, cookies, err = login_helper.login(email, password)
                if ok and athlete:
                    self.creds_mgr.save({
                        "session_cookies": cookies,
                        "auth_mode": "session",
                        "athlete": {
                            "id": athlete.id,
                            "username": athlete.username,
                            "firstname": athlete.firstname,
                            "lastname": athlete.lastname,
                        },
                    })
                    self.app.call_from_thread(self._finish_auth, "session")
                else:
                    self.app.call_from_thread(
                        status_lbl.update,
                        f"[red]{err or 'Login failed'}[/red]",
                    )

            threading.Thread(target=login_bg, daemon=True).start()

    def _finish_auth(self, mode: str):
        if self.on_auth_success:
            self.on_auth_success(mode)
        else:
            self.app.pop_screen()
