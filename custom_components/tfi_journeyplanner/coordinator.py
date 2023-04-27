"""TFI Journey Planner data update coordinator."""

from datetime import datetime, timedelta
import logging

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_UPDATE_NO_DATA_THRESHOLD
from .util import timedelta_to_str
from .tfi_journeyplanner_api import TFIData

_LOGGER = logging.getLogger(__name__)


class TFIJourneyPlannerCoordinator(DataUpdateCoordinator):
    """TFI Journey Planner coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        tfi_data: TFIData,
        update_interval: timedelta,
        update_interval_fast: timedelta,
        update_interval_no_data: timedelta,
        update_horizon_fast: timedelta,
    ) -> None:
        """Initialise TFI Journey Planner coordinator."""
        super().__init__(
            hass,
            _LOGGER.getChild("coordinator"),
            # Name of the data. For logging purposes.
            name="TFIData",
            ## short initial refresh after all platforms have completed setup
            update_interval=timedelta(seconds=3),
        )
        self._tfi_data = tfi_data
        self.update_interval_default = update_interval
        self.update_interval_fast = update_interval_fast
        self.update_interval_no_data = update_interval_no_data
        self.update_horizon_fast = update_horizon_fast
        self._next_update: datetime = None
        self._update_no_data = 0
        self.polling_enabled = True
        self.is_polling = True

    async def _async_update_data(self) -> None:
        """Fetch data from TFI Journey Planner API."""
        tfi_data: TFIData = self._tfi_data

        stop_ids = [stop for stops in self.async_contexts() for stop in stops]
        if not stop_ids:
            _LOGGER.debug("no stops registered, skipping update")
            return

        if self.is_polling and not self.polling_enabled:  ## polling enabled
            _LOGGER.debug("re-enabling coordinator polling")
            self.polling_enabled = True
            self._next_update = None
        elif not self.is_polling and self.polling_enabled:  ## polling disabled
            _LOGGER.debug("disabling coordinator polling")
            self.polling_enabled = False
            self.update_interval = None

        ## Continue refreshing sensors when polling is off
        if not self.is_polling:
            self.update_interval = timedelta(seconds=30)
            return

        now = datetime.now().astimezone()
        next_update = self._next_update
        if next_update is None:
            _LOGGER.debug("performing initial update")
            next_update = now
        if next_update > now + timedelta(seconds=15):
            _LOGGER.debug(
                "skipping update, next update in %s",
                timedelta_to_str(next_update - now),
            )
            return

        async with async_timeout.timeout(10):
            departures = await tfi_data.update_departures(stop_ids)
            first_departure = None
            departure_horizon = None
            update_interval = self.update_interval_default
            if len(departures) == 0:
                self._update_no_data += 1
                if self._update_no_data > DEFAULT_UPDATE_NO_DATA_THRESHOLD:
                    update_interval = self.update_interval_no_data
            else:
                self._update_no_data = 0
                first_departure: datetime = departures[0].get("departure", now)
                departure_horizon = first_departure - now
                update_horizon_fast = self.update_horizon_fast
                update_interval_default = self.update_interval_default
                update_interval_fast = self.update_interval_fast
                if departure_horizon < update_horizon_fast:
                    ## Next departure due within fast update horizon
                    update_interval = update_interval_fast
                elif departure_horizon < update_horizon_fast + update_interval_default:
                    ## Next departure will fall within fast update horizon before next update
                    update_interval = max(
                        departure_horizon - update_horizon_fast, update_interval_fast
                    )

            self._next_update = now + update_interval
            self.update_interval = timedelta(seconds=30)

            _LOGGER.debug(
                "retrieved %d departures, first departure in %s, next update in %s",
                len(departures),
                timedelta_to_str(departure_horizon),
                timedelta_to_str(update_interval),
            )
