"""Official Strava v3 REST API client implementation."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional
import requests

from strava_tui.auth.api_oauth import StravaOAuthManager
from strava_tui.auth.credentials import CredentialsManager, CACHE_DIR
from strava_tui.client.base import BaseStravaClient
from strava_tui.data.models import Activity, AthleteProfile

API_BASE = "https://www.strava.com/api/v3"


class StravaApiClient(BaseStravaClient):
    """Fetches activities via Strava's official v3 REST API."""

    def __init__(self, credentials_manager: Optional[CredentialsManager] = None):
        self.creds_mgr = credentials_manager or CredentialsManager()
        self.creds = self.creds_mgr.get_api_credentials()
        self.session = requests.Session()

    def _ensure_valid_token(self) -> str:
        """Check if access token is expired and refresh if necessary."""
        access_token = self.creds.get("access_token", "")
        refresh_token = self.creds.get("refresh_token", "")
        expires_at = self.creds.get("expires_at", 0)
        client_id = self.creds.get("client_id", "")
        client_secret = self.creds.get("client_secret", "")

        # If expires_at is in the past (or within 5 minutes of expiring) and we have refresh_token
        if refresh_token and client_id and client_secret:
            current_time = time.time()
            if expires_at and current_time >= (expires_at - 300):
                new_tokens = StravaOAuthManager.refresh_access_token(
                    client_id, client_secret, refresh_token
                )
                self.creds["access_token"] = new_tokens["access_token"]
                self.creds["refresh_token"] = new_tokens["refresh_token"]
                self.creds["expires_at"] = new_tokens["expires_at"]
                self.creds_mgr.save(new_tokens)
                access_token = new_tokens["access_token"]

        return access_token

    def get_athlete(self) -> AthleteProfile:
        """Fetch current athlete profile."""
        token = self._ensure_valid_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = self.session.get(f"{API_BASE}/athlete", headers=headers, timeout=15)
        if resp.status_code == 401:
            # Force refresh and retry once
            refresh_token = self.creds.get("refresh_token")
            client_id = self.creds.get("client_id")
            client_secret = self.creds.get("client_secret")
            if refresh_token and client_id and client_secret:
                new_tokens = StravaOAuthManager.refresh_access_token(client_id, client_secret, refresh_token)
                self.creds_mgr.save(new_tokens)
                headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
                resp = self.session.get(f"{API_BASE}/athlete", headers=headers, timeout=15)

        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch athlete: HTTP {resp.status_code} - {resp.text}")

        data = resp.json()
        return AthleteProfile(
            id=str(data.get("id", "")),
            username=data.get("username", "") or "",
            firstname=data.get("firstname", "") or "",
            lastname=data.get("lastname", "") or "",
            city=data.get("city", "") or "",
            country=data.get("country", "") or "",
            profile_picture=data.get("profile_medium", "") or "",
            auth_mode="api",
        )

    def get_activities_for_year(
        self,
        year: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        use_cache: bool = True,
    ) -> List[Activity]:
        """Fetch all activities for the specified year using pagination."""
        cache_file = CACHE_DIR / f"api_activities_{year}.json"

        # Check local cache if enabled
        if use_cache and cache_file.exists():
            try:
                # Use cache if file was modified recently (within 1 hour)
                if time.time() - cache_file.stat().st_mtime < 3600:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_raw = json.load(f)
                    return [self._parse_activity(item) for item in cached_raw]
            except Exception:
                pass

        token = self._ensure_valid_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Calculate epoch timestamps for year start and end
        start_dt = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        after_ts = int(start_dt.timestamp())
        before_ts = int(end_dt.timestamp())

        all_raw_activities = []
        page = 1
        per_page = 200

        while True:
            params = {
                "after": after_ts,
                "before": before_ts,
                "page": page,
                "per_page": per_page,
            }
            resp = self.session.get(
                f"{API_BASE}/athlete/activities",
                headers=headers,
                params=params,
                timeout=20,
            )

            if resp.status_code == 401:
                # Refresh token and retry
                token = self._ensure_valid_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = self.session.get(
                    f"{API_BASE}/athlete/activities",
                    headers=headers,
                    params=params,
                    timeout=20,
                )

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch activities on page {page}: HTTP {resp.status_code} - {resp.text}"
                )

            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                break

            all_raw_activities.extend(data)
            if progress_callback:
                progress_callback(page, len(all_raw_activities))

            if len(data) < per_page:
                break

            page += 1
            # Strava API rate limit compliance
            time.sleep(0.1)

        # Save to cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(all_raw_activities, f)
        except Exception:
            pass

        return [self._parse_activity(item) for item in all_raw_activities]

    @staticmethod
    def _parse_activity(item: dict) -> Activity:
        """Convert a Strava API activity dict to an Activity dataclass."""
        # Parse ISO date string
        start_str = item.get("start_date_local") or item.get("start_date") or ""
        try:
            # Handle ISO formats like 2024-05-12T08:30:00Z
            dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now()

        return Activity(
            id=str(item.get("id", "")),
            name=item.get("name", "Untitled Activity"),
            distance_meters=float(item.get("distance", 0.0)),
            moving_time_seconds=int(item.get("moving_time", 0)),
            elapsed_time_seconds=int(item.get("elapsed_time", 0)),
            total_elevation_gain=float(item.get("total_elevation_gain", 0.0)),
            sport_type=item.get("sport_type") or item.get("type", "Workout"),
            start_date=dt,
            average_speed_ms=float(item.get("average_speed", 0.0)),
            max_speed_ms=float(item.get("max_speed", 0.0)),
            average_heartrate=item.get("average_heartrate"),
            max_heartrate=item.get("max_heartrate"),
            strava_url=f"https://www.strava.com/activities/{item.get('id', '')}",
        )
