"""Data models for Strava TUI application."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AthleteProfile:
    """Represents the authenticated Strava athlete."""
    id: str
    username: str = ""
    firstname: str = ""
    lastname: str = ""
    city: str = ""
    country: str = ""
    profile_picture: str = ""
    auth_mode: str = "api"  # "api", "session", or "mock"

    @property
    def full_name(self) -> str:
        name = f"{self.firstname} {self.lastname}".strip()
        return name if name else (self.username or f"Athlete #{self.id}")


@dataclass
class Activity:
    """Represents a Strava training activity."""
    id: str
    name: str
    distance_meters: float
    moving_time_seconds: int
    elapsed_time_seconds: int
    total_elevation_gain: float
    sport_type: str
    start_date: datetime
    average_speed_ms: float = 0.0
    max_speed_ms: float = 0.0
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    strava_url: str = ""

    def __post_init__(self):
        if not self.strava_url:
            self.strava_url = f"https://www.strava.com/activities/{self.id}"

    @property
    def distance_km(self) -> float:
        """Distance in kilometers."""
        return round(self.distance_meters / 1000.0, 2)

    @property
    def average_speed_kmh(self) -> float:
        """Average speed in km/h."""
        if self.moving_time_seconds > 0 and self.distance_meters > 0:
            return round((self.distance_meters / self.moving_time_seconds) * 3.6, 2)
        return round(self.average_speed_ms * 3.6, 2)

    @property
    def moving_time_formatted(self) -> str:
        """Formatted moving time (hh:mm:ss or mm:ss)."""
        hours = self.moving_time_seconds // 3600
        minutes = (self.moving_time_seconds % 3600) // 60
        seconds = self.moving_time_seconds % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        return f"{minutes}m {seconds:02d}s"

    @property
    def pace_per_km(self) -> str:
        """Pace in min:sec / km (primarily for running/walking/hiking)."""
        if self.distance_meters <= 0 or self.moving_time_seconds <= 0:
            return "--:--"
        sec_per_km = self.moving_time_seconds / (self.distance_meters / 1000.0)
        minutes = int(sec_per_km // 60)
        seconds = int(sec_per_km % 60)
        return f"{minutes}:{seconds:02d} /km"

    @property
    def date_formatted(self) -> str:
        """Formatted start date string."""
        return self.start_date.strftime("%Y-%m-%d %H:%M")


@dataclass
class MonthlyStat:
    """Statistics for a single month."""
    month_number: int  # 1 to 12
    month_name: str
    count: int = 0
    distance_km: float = 0.0
    moving_time_seconds: int = 0
    elevation_gain_m: float = 0.0


@dataclass
class SportStat:
    """Statistics for a specific sport/activity type."""
    sport_type: str
    count: int = 0
    distance_km: float = 0.0
    moving_time_seconds: int = 0
    elevation_gain_m: float = 0.0


@dataclass
class AggregatedStats:
    """Aggregated statistics for a set of filtered activities."""
    year: int
    phrase: str
    total_activities_in_year: int = 0
    matching_count: int = 0
    total_distance_km: float = 0.0
    total_moving_time_seconds: int = 0
    total_elevation_gain_m: float = 0.0
    avg_distance_km: float = 0.0
    avg_speed_kmh: float = 0.0
    longest_activity: Optional[Activity] = None
    highest_climb_activity: Optional[Activity] = None
    monthly_breakdown: List[MonthlyStat] = field(default_factory=list)
    sport_breakdown: List[SportStat] = field(default_factory=list)
    activities: List[Activity] = field(default_factory=list)

    @property
    def total_moving_time_formatted(self) -> str:
        hours = self.total_moving_time_seconds // 3600
        minutes = (self.total_moving_time_seconds % 3600) // 60
        return f"{hours}h {minutes:02d}m"
