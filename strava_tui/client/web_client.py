"""Strava web session client for fetching activities without API keys."""
import json
import time
from datetime import datetime
from typing import Callable, List, Optional
import requests

from strava_tui.auth.credentials import CredentialsManager, CACHE_DIR
from strava_tui.client.base import BaseStravaClient
from strava_tui.data.models import Activity, AthleteProfile

TRAINING_ACTIVITIES_URL = "https://www.strava.com/athlete/training_activities"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class StravaWebClient(BaseStravaClient):
    """Fetches activities using Strava web session cookies."""

    def __init__(self, credentials_manager: Optional[CredentialsManager] = None):
        self.creds_mgr = credentials_manager or CredentialsManager()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        })
        # Load saved cookies
        cookies = self.creds_mgr.get_session_cookies()
        self.session.cookies.update(cookies)

    def get_athlete(self) -> AthleteProfile:
        athlete_data = self.creds_mgr.load().get("athlete", {})
        return AthleteProfile(
            id=str(athlete_data.get("id", "web-user")),
            username=athlete_data.get("username", "Strava Athlete"),
            firstname=athlete_data.get("firstname", "Strava"),
            lastname=athlete_data.get("lastname", "Athlete"),
            auth_mode="session",
        )

    def get_activities_for_year(
        self,
        year: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        use_cache: bool = True,
    ) -> List[Activity]:
        cache_file = CACHE_DIR / f"web_activities_{year}.json"
        if use_cache and cache_file.exists():
            try:
                if time.time() - cache_file.stat().st_mtime < 3600:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_raw = json.load(f)
                    return [self._parse_web_activity(item) for item in cached_raw]
            except Exception:
                pass

        all_activities: List[dict] = []
        page = 1
        per_page = 50

        while True:
            params = {
                "page": page,
                "per_page": per_page,
            }
            resp = self.session.get(TRAINING_ACTIVITIES_URL, params=params, timeout=15)
            if resp.status_code != 200 or resp.url.endswith("/login"):
                raise RuntimeError("Strava session has expired or is invalid. Please log in again.")

            try:
                data = resp.json()
            except Exception:
                break

            models = data.get("models", [])
            if not models:
                break

            reached_prior_year = False
            for act in models:
                parsed = self._parse_web_activity(act)
                if parsed.start_date.year == year:
                    all_activities.append(act)
                elif parsed.start_date.year < year:
                    # Activities are ordered descending; if we are past target year, stop
                    reached_prior_year = True

            if progress_callback:
                progress_callback(page, len(all_activities))

            if reached_prior_year or len(models) < per_page:
                break

            page += 1
            time.sleep(0.2)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(all_activities, f)
        except Exception:
            pass

        return [self._parse_web_activity(item) for item in all_activities]

    @staticmethod
    def _parse_web_activity(item: dict) -> Activity:
        act_id = str(item.get("id", ""))
        name = item.get("name", "Training")
        sport_type = item.get("type", "Workout")

        # Distance might be in meters or string like '12.4 km'
        dist_raw = item.get("distance", 0.0)
        if isinstance(dist_raw, str):
            dist_str = dist_raw.replace("km", "").replace("mi", "").replace(",", "").strip()
            try:
                distance_meters = float(dist_str) * 1000.0
            except ValueError:
                distance_meters = 0.0
        else:
            distance_meters = float(dist_raw or 0.0)

        moving_time = int(item.get("moving_time_raw") or item.get("moving_time", 0))
        elapsed_time = int(item.get("elapsed_time_raw") or item.get("elapsed_time", moving_time))
        elevation_gain = float(item.get("elevation_gain_raw") or item.get("elevation_gain", 0.0))

        start_time_str = item.get("start_time") or item.get("start_date") or ""
        try:
            dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now()

        return Activity(
            id=act_id,
            name=name,
            distance_meters=distance_meters,
            moving_time_seconds=moving_time,
            elapsed_time_seconds=elapsed_time,
            total_elevation_gain=elevation_gain,
            sport_type=sport_type,
            start_date=dt,
            strava_url=f"https://www.strava.com/activities/{act_id}",
        )
