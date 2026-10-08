"""Web session authenticator for username/password login to Strava."""
from typing import Dict, Optional, Tuple
import requests

from strava_tui.data.models import AthleteProfile

LOGIN_URL = "https://www.strava.com/login"
SESSION_URL = "https://www.strava.com/session"
DASHBOARD_URL = "https://www.strava.com/dashboard"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class StravaSessionLogin:
    """Handles username/password session login on strava.com."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def login(self, email: str, password: str) -> Tuple[bool, Optional[AthleteProfile], Dict[str, str], Optional[str]]:
        """
        Attempt to log in with email/username and password.
        Returns: (success, athlete_profile, cookies_dict, error_message)
        """
        email = email.strip()
        if not email or not password:
            return False, None, {}, "Email and password cannot be empty."

        try:
            # 1. First visit login page to establish session cookie
            init_resp = self.session.get(LOGIN_URL, timeout=15)
            if init_resp.status_code != 200:
                return False, None, {}, f"Unable to reach Strava login page (HTTP {init_resp.status_code})"

            # 2. Post credentials to /session
            headers = {
                "Origin": "https://www.strava.com",
                "Referer": LOGIN_URL,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            payload = {
                "email": email,
                "password": password,
            }

            resp = self.session.post(SESSION_URL, data=payload, headers=headers, allow_redirects=True, timeout=20)

            # Check if login succeeded
            # When login succeeds, Strava redirects to dashboard or athlete profile and sets session cookies
            cookies_dict = self.session.cookies.get_dict()

            if "two_factor" in resp.url or "verification" in resp.url:
                return False, None, cookies_dict, "Two-Factor Authentication is enabled on this account. Please use Strava API OAuth instead."

            # If redirected back to login page, credentials failed or bot protection triggered
            if resp.url.rstrip("/").endswith("/login"):
                # Check for Cloudflare / CAPTCHA indicators
                if "challenge" in resp.text.lower() or "captcha" in resp.text.lower():
                    return (
                        False,
                        None,
                        {},
                        "Strava triggered anti-bot Cloudflare CAPTCHA verification. "
                        "Please use the official API OAuth (Client ID / Secret) or Access Token method instead.",
                    )
                return False, None, {}, "Invalid Strava username or password."

            # Verify authenticated session by requesting training activities or athlete page
            test_resp = self.session.get("https://www.strava.com/athlete/training_activities", timeout=15)
            if test_resp.status_code == 200 and not test_resp.url.endswith("/login"):
                athlete = AthleteProfile(
                    id=email.split("@")[0],
                    username=email.split("@")[0],
                    firstname=email.split("@")[0],
                    lastname="",
                    auth_mode="session",
                )
                return True, athlete, cookies_dict, None

            # Fallback check on dashboard
            dash_resp = self.session.get(DASHBOARD_URL, timeout=15)
            if dash_resp.status_code == 200 and not dash_resp.url.endswith("/login"):
                athlete = AthleteProfile(
                    id=email.split("@")[0],
                    username=email.split("@")[0],
                    firstname=email.split("@")[0],
                    lastname="",
                    auth_mode="session",
                )
                return True, athlete, cookies_dict, None

            return False, None, {}, "Login failed. Strava did not grant a valid athlete session."

        except requests.exceptions.RequestException as e:
            return False, None, {}, f"Network error during login: {str(e)}"
        except Exception as e:
            return False, None, {}, f"Unexpected error: {str(e)}"
