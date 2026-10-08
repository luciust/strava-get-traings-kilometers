"""Mock client for offline testing and demoing Strava TUI features."""
import random
from datetime import datetime, timezone
from typing import Callable, List, Optional

from strava_tui.client.base import BaseStravaClient
from strava_tui.data.models import Activity, AthleteProfile


SAMPLE_TITLES = [
    ("Morning Interval Training - 5x1km", "Run", 11.2, 52, 45),
    ("Threshold Intervals on Track", "Run", 9.8, 44, 25),
    ("Zwift - FTP Interval Workout", "VirtualRide", 38.5, 65, 320),
    ("Sunday Long Ride with Sprint Intervals", "Ride", 84.6, 172, 890),
    ("Hill Repeats & Intervals", "Run", 8.4, 48, 185),
    ("Morning Commute to Office", "Ride", 15.4, 38, 120),
    ("Evening Commute Return", "Ride", 15.8, 42, 130),
    ("Sunday Long Run in the Forest", "Run", 22.4, 125, 240),
    ("Midweek Easy Recovery Jog", "Run", 6.5, 36, 40),
    ("Tempo Run along River", "Run", 12.0, 56, 55),
    ("Mountain Trail Hike with Poles", "Hike", 14.2, 210, 680),
    ("Gravel Ride Adventure", "Ride", 56.0, 140, 540),
    ("Indoor Interval Cycling", "Ride", 32.0, 55, 150),
    ("Fast 5K Interval Session", "Run", 6.2, 28, 18),
    ("Post-work Steady State Ride", "Ride", 44.5, 95, 360),
    ("Weekend Century Ride Part 1", "Ride", 102.5, 220, 1150),
    ("Morning Swim Laps", "Swim", 2.5, 48, 0),
    ("Interval Run - Pyramid Workout", "Run", 10.5, 51, 60),
    ("Commute by Bike (Sunny morning)", "Ride", 16.1, 39, 115),
    ("Evening Shakeout Run", "Run", 5.2, 29, 30),
]


class MockStravaClient(BaseStravaClient):
    """Generates realistic sample activities for offline use, testing, and demonstrations."""

    def __init__(self, athlete_name: str = "Alex Runner"):
        self.athlete_name = athlete_name

    def get_athlete(self) -> AthleteProfile:
        parts = self.athlete_name.split()
        first = parts[0] if parts else "Demo"
        last = parts[1] if len(parts) > 1 else "Athlete"
        return AthleteProfile(
            id="99988877",
            username="alex_runner",
            firstname=first,
            lastname=last,
            city="Boulder, CO",
            country="United States",
            profile_picture="",
            auth_mode="demo",
        )

    def get_activities_for_year(
        self,
        year: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Activity]:
        """Generate 100+ realistic activities distributed throughout the year."""
        random.seed(year * 42)
        activities: List[Activity] = []
        act_id_counter = 1000000 + year * 1000

        # Generate activities for each month (roughly 8 to 15 per month)
        for month in range(1, 13):
            num_activities = random.randint(8, 14)
            for _ in range(num_activities):
                act_id_counter += 1
                day = random.randint(1, 28)
                hour = random.choice([6, 7, 8, 12, 17, 18, 19])
                minute = random.choice([0, 15, 30, 45])
                dt = datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)

                template = random.choice(SAMPLE_TITLES)
                title, sport, base_dist, base_min, base_elev = template

                # Add some small variation
                dist_var = round(base_dist * random.uniform(0.9, 1.15), 2)
                time_var = int(base_min * 60 * random.uniform(0.92, 1.12))
                elev_var = round(base_elev * random.uniform(0.85, 1.25), 1)

                dist_m = dist_var * 1000.0
                avg_speed = (dist_m / time_var) if time_var > 0 else 0.0

                hr_avg = random.randint(135, 168) if sport in ("Run", "Ride") else None
                hr_max = hr_avg + random.randint(12, 25) if hr_avg else None

                activities.append(
                    Activity(
                        id=str(act_id_counter),
                        name=title,
                        distance_meters=dist_m,
                        moving_time_seconds=time_var,
                        elapsed_time_seconds=int(time_var * 1.08),
                        total_elevation_gain=elev_var,
                        sport_type=sport,
                        start_date=dt,
                        average_speed_ms=avg_speed,
                        max_speed_ms=avg_speed * 1.35,
                        average_heartrate=hr_avg,
                        max_heartrate=hr_max,
                        strava_url=f"https://www.strava.com/activities/{act_id_counter}",
                    )
                )

        if progress_callback:
            progress_callback(1, len(activities))

        # Sort descending by date
        activities.sort(key=lambda a: a.start_date, reverse=True)
        return activities
