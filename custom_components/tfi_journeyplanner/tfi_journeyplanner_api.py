"""TFI Journey Planner API."""

from datetime import datetime, timedelta, timezone
from typing import Any

# import json
import logging
import aiohttp

from .const import DEFAULT_DEPARTURE_HORIZON

_LOGGER = logging.getLogger(__name__)

TFI_DEPARTURES_API = (
    "https://api-lts.transportforireland.ie/lts/lts/v1/public/departures"
)
TFI_DEFAULT_HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-GB,en-IE;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    # "Content-Type": "application/json",
    "Dnt": "1",
    "Ocp-Apim-Subscription-Key": "630688984d38409689932a37a8641bb9",
    "Origin": "https://journeyplanner.transportforireland.ie",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
}


class NotConnected(Exception):
    """Journey planner not connected."""


class TFIData:
    """TFI Journey Planner Data class."""

    def __init__(self):
        self._session = None
        self._departures = None
        self._no_data_log_msg = False
        self._no_data_filtered_log_msg = False

    async def setup(self) -> None:
        """Set up TFI Journey Planner."""
        if not self._session:
            self._session = aiohttp.ClientSession(headers=TFI_DEFAULT_HEADERS)

    async def cleanup(self) -> None:
        """Clean up TFI Journey Planner."""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_departures(
        self,
        stop_ids: list[str],
        departure_time: datetime | None = None,
        service_ids: list[str] | None = None,
        direction: list[str] | None = None,
        limit_departures: int | None = None,
        departure_horizon: timedelta | None = None,
        realtime_only: bool = False,
        include_cancelled: bool = False,
    ) -> list[dict[str, Any]]:
        """Update cache and return filtered departures."""
        await self.update_departures(stop_ids, departure_time)
        return self.get_filtered_departures(
            stop_ids=stop_ids,
            service_ids=service_ids,
            direction=direction,
            limit_departures=limit_departures,
            departure_horizon=departure_horizon,
            realtime_only=realtime_only,
            include_cancelled=include_cancelled,
        )

    def get_filtered_departures(
        self,
        stop_ids: list[str],
        service_ids: list[str] | None = None,
        direction: list[str] | None = None,
        limit_departures: int | None = None,
        departure_horizon: timedelta | None = None,
        realtime_only: bool = False,
        include_cancelled: bool = False,
    ) -> list[dict[str, Any]]:
        """Return filtered departures from cache."""
        if self._departures is None:
            return []

        now = datetime.now().astimezone()
        if service_ids is None:
            service_ids = []
        if departure_horizon is None:
            departure_horizon = timedelta(**DEFAULT_DEPARTURE_HORIZON)

        def filter_departure(dep: dict[str, Any]) -> bool:
            """Filter departure based on options."""
            dep_stop_id = dep["stopRef"]
            dep_rt = dep["realTimeDeparture"]
            dep_sch = dep["scheduledDeparture"]
            dep_dir = dep["serviceDirection"]
            dep_time = dep_rt if dep_rt else dep_sch
            dep_cancelled = dep.get("cancelled", False)
            dep_service = dep.get("serviceNumber", "unknown")
            dep_time = dep_rt if dep_rt else dep_sch
            return (
                dep_stop_id in stop_ids
                and now <= dep_time <= now + departure_horizon
                and (not service_ids or dep_service in service_ids)
                and (not direction or dep_dir in direction)
                and (not realtime_only or dep_rt is not None)
                and (include_cancelled or not dep_cancelled)
            )

        departures = []
        dep_count = 0
        for dep in self._departures:
            if filter_departure(dep):
                dep_count += 1
                departures.append(dep)
                if limit_departures and dep_count >= limit_departures:
                    break
        return departures

    async def update_departures(
        self,
        stop_ids: list[str],
        departure_time: datetime | None = None,
    ) -> list[dict[str, Any]] | bool:
        """Update cached departures."""
        session = self._session
        if not session:
            raise NotConnected

        now = datetime.now().astimezone(timezone.utc)
        now_str = now.isoformat(timespec="milliseconds")

        if departure_time is None:
            departure_time = now
        departure_utc = departure_time.astimezone(timezone.utc)
        departure_str = departure_utc.isoformat(timespec="milliseconds")

        def parse_departure(dep: dict[str, Any]) -> None:
            """Parse departure information."""
            dep_rt_str = dep.get("realTimeDeparture")
            dep["realTimeDeparture"] = (
                dep_rt := datetime.fromisoformat(dep_rt_str).astimezone()
                if dep_rt_str
                else None
            )
            dep_sch_str = dep.get("scheduledDeparture")
            dep["scheduledDeparture"] = (
                dep_sch := datetime.fromisoformat(dep_sch_str).astimezone()
                if dep_sch_str
                else None
            )
            dep["departure"] = dep_rt if dep_rt is not None else dep_sch

        def filter_departure(dep: dict[str, Any]) -> bool:
            return dep["departure"] >= now - timedelta(minutes=1)

        tzoffset = -int(datetime.now().astimezone().utcoffset().total_seconds()) * 1000
        post_data = {
            "clientTimeZoneOffsetInMS": tzoffset,
            "departureDate": departure_str,
            "departureTime": departure_str,
            "stopIds": stop_ids,  ## ["8220DB000393"],
            "stopType": "BUS_STOP",
            # "stopName": "Tritonville Road, Sandymount",
            "requestTime": now_str,
            "departureOrArrival": "DEPARTURE",
            "refresh": True,
        }

        async with session.post(TFI_DEPARTURES_API, json=post_data) as resp:
            data: dict[str, Any] = {}
            if resp.status == 200:
                data = await resp.json()
            else:
                _LOGGER.warning("TFI API returned status %d, discarding response")
            departures = []
            if not (deps_raw := data.get("stopDepartures", [])):
                if not (deps_raw := self._departures):
                    if not self._no_data_log_msg:
                        _LOGGER.warning(
                            "no departures retrieved and no cached departures"
                        )
                        self._no_data_log_msg = True
                else:
                    if not self._no_data_filtered_log_msg:
                        self._no_data_filtered_log_msg = True
                        _LOGGER.debug(
                            "no departures retrieved, filtering cached departures"
                        )
                    for dep in deps_raw:
                        if filter_departure(dep):
                            departures.append(dep)
            else:
                self._no_data_log_msg = False
                self._no_data_filtered_log_msg = False
                for dep in deps_raw:
                    parse_departure(dep)
                    if filter_departure(dep):
                        departures.append(dep)
            self._departures = departures
            return departures
