"""Abstract base class for Strava data clients."""
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from strava_tui.data.models import Activity, AthleteProfile


class BaseStravaClient(ABC):
    """Abstract interface for Strava activity fetching."""

    @abstractmethod
    def get_athlete(self) -> AthleteProfile:
        """Fetch profile of current user/athlete."""
        pass

    @abstractmethod
    def get_activities_for_year(
        self,
        year: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Activity]:
        """
        Fetch all activities for a given year.
        progress_callback: optional callback func(page, total_loaded_so_far)
        """
        pass
