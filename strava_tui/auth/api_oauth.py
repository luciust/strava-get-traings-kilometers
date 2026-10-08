"""Strava API OAuth2 authentication handler."""
import http.server
import socket
import threading
import time
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional, Tuple
import requests

from strava_tui.data.models import AthleteProfile

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE = "https://www.strava.com/api/v3"


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handles the OAuth redirect callback from Strava."""

    auth_code: Optional[str] = None
    error: Optional[str] = None

    def log_message(self, format, *args):
        # Suppress standard logging to keep terminal clean
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            query = urllib.parse.parse_qs(parsed.query)
            if "code" in query:
                OAuthCallbackHandler.auth_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Strava Authorization Successful</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                               background: #0f172a; color: #f8fafc; display: flex; align-items: center;
                               justify-content: center; height: 100vh; margin: 0; }
                        .card { background: #1e293b; border-radius: 12px; padding: 40px; text-align: center;
                                box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 450px; border: 1px solid #334155; }
                        h1 { color: #FC4C02; margin-top: 0; }
                        p { color: #94a3b8; font-size: 16px; line-height: 1.5; }
                        .badge { display: inline-block; background: #22c55e22; color: #22c55e;
                                 padding: 6px 14px; border-radius: 999px; font-weight: bold; margin-bottom: 20px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="badge">Connected!</div>
                        <h1>Strava Authorized</h1>
                        <p>Authorization code received successfully!</p>
                        <p>You can now close this browser tab and return to the <strong>Strava TUI</strong> terminal.</p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
            elif "error" in query:
                OAuthCallbackHandler.error = query["error"][0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h1>Authorization Failed</h1><p>{OAuthCallbackHandler.error}</p>".encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h1>Missing code parameter</h1>")
        else:
            self.send_response(404)
            self.end_headers()


def find_free_port(starting_port: int = 8000, max_tries: int = 20) -> int:
    """Find an available port starting from starting_port."""
    for port in range(starting_port, starting_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return starting_port


class StravaOAuthManager:
    """Handles OAuth 2.0 flow with Strava."""

    def __init__(self, client_id: str, client_secret: str, port: int = 8000):
        self.client_id = str(client_id).strip()
        self.client_secret = client_secret.strip()
        self.port = find_free_port(port)
        self.redirect_uri = f"http://localhost:{self.port}/callback"

    def get_authorization_url(self, scope: str = "read,activity:read_all") -> str:
        """Generate Strava OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "approval_prompt": "auto",
            "scope": scope,
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    def listen_for_code(self, timeout_seconds: int = 120) -> Optional[str]:
        """Start local HTTP server and wait for OAuth callback."""
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None

        server = http.server.HTTPServer(("127.0.0.1", self.port), OAuthCallbackHandler)
        server.timeout = 1.0

        start_time = time.time()
        try:
            while time.time() - start_time < timeout_seconds:
                server.handle_request()
                if OAuthCallbackHandler.auth_code:
                    return OAuthCallbackHandler.auth_code
                if OAuthCallbackHandler.error:
                    raise RuntimeError(f"Strava OAuth Error: {OAuthCallbackHandler.error}")
        finally:
            server.server_close()

        raise TimeoutError("Timed out waiting for Strava authorization in browser.")

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        response = requests.post(TOKEN_URL, data=payload, timeout=15)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to exchange token ({response.status_code}): {response.text}")
        return response.json()

    @staticmethod
    def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token using refresh_token."""
        payload = {
            "client_id": str(client_id).strip(),
            "client_secret": client_secret.strip(),
            "refresh_token": refresh_token.strip(),
            "grant_type": "refresh_token",
        }
        response = requests.post(TOKEN_URL, data=payload, timeout=15)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to refresh token ({response.status_code}): {response.text}")
        return response.json()

    @staticmethod
    def verify_token(access_token: str) -> Tuple[bool, Optional[AthleteProfile], Optional[str]]:
        """Verify an access token by fetching athlete profile."""
        headers = {"Authorization": f"Bearer {access_token.strip()}"}
        try:
            resp = requests.get(f"{API_BASE}/athlete", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                athlete = AthleteProfile(
                    id=str(data.get("id", "")),
                    username=data.get("username", "") or "",
                    firstname=data.get("firstname", "") or "",
                    lastname=data.get("lastname", "") or "",
                    city=data.get("city", "") or "",
                    country=data.get("country", "") or "",
                    profile_picture=data.get("profile_medium", "") or "",
                    auth_mode="api",
                )
                return True, athlete, None
            else:
                return False, None, f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, None, str(e)
