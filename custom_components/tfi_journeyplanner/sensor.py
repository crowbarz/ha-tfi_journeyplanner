"""TFI Journey Planner sensor integration."""

from __future__ import annotations

from typing import Any

# import asyncio
import logging

from datetime import datetime  # , timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_STOP_IDS,
    # CONF_SERVICE_IDS,
    # CONF_LIMIT_DEPARTURES,
    # CONF_DEPARTURE_HORIZON,
    CONF_REALTIME_ONLY,
    CONF_INCLUDE_CANCELLED,
    # DEFAULT_DEPARTURE_HORIZON,
)
from .tfi_journeyplanner_api import TFIData
from .coordinator import TFIJourneyPlannerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: TFIJourneyPlannerCoordinator = entry_data["coordinator"]
    tfi_data: TFIData = entry_data["tfi_data"]
    data = entry.data

    async_add_entities(
        [
            TfiJourneyPlannerSensor(coordinator, tfi_data, stop_id, entry)
            for stop_id in data[CONF_STOP_IDS]
        ]
    )


class TfiJourneyPlannerSensor(CoordinatorEntity, SensorEntity):
    """TFI Journey Planner sensor class."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: TFIJourneyPlannerCoordinator,
        tfi_data: TFIData,
        stop_id: str,
        entry: ConfigEntry,
    ):
        self._coordinator = coordinator
        self._tfi_data = tfi_data
        self._config_entry = entry
        # data: dict[str, Any] = entry.data
        options: dict[str, Any] = entry.options

        self._stop_ids = (stop_ids := [stop_id])
        super().__init__(coordinator, context=self._stop_ids)
        _LOGGER.debug("adding stops %s to coordinator", self._stop_ids)

        # self._limit_departures = config.get(CONF_LIMIT_DEPARTURES)
        # self._service_ids = config.get(CONF_SERVICE_IDS)
        # self._departure_horizon = config.get(CONF_DEPARTURE_HORIZON)

        self._attr_name = ("Stop " if len(stop_ids) == 1 else "Stops ") + ", ".join(
            stop_ids
        )

        self._realtime_only = options.get(CONF_REALTIME_ONLY, False)
        self._include_cancelled = options.get(CONF_INCLUDE_CANCELLED, False)

        self._attr_unique_id = DOMAIN + "_" + "+".join([str(stop) for stop in stop_ids])
        self._departures = None

    # async def async_added_to_hass(self) -> None:
    #     """Complete the initialization."""
    #     await super().async_added_to_hass()
    #     await self._coordinator.async_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, *self._config_entry.data[CONF_STOP_IDS])
            },
            name=self._config_entry.title,
            # manufacturer=self.light.manufacturername,
            # model=self.light.productname,
            # sw_version=self.light.swversion,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        departures = self._tfi_data.get_filtered_departures(
            self._stop_ids,
            # service_ids=self._service_ids,
            # limit_departures=self._limit_departures,
            # departure_horizon=self._departure_horizon,
            include_cancelled=self._include_cancelled,
            realtime_only=self._realtime_only,
        )
        self._departures = departures
        first_departure = None
        if len(departures) > 0:
            first_departure: datetime = departures[0].get("departure")

        self._attr_native_value = first_departure
        attrs = {
            "attribution": "Data provided by transportforireland.ie "
            "per conditions of reuse at https://data.gov.ie/licence",
            "source": "tfi_journeyplanner",
            "departures": departures,
        }
        if first_departure:
            now = datetime.now().astimezone()
            attrs["first_departure"] = (first_departure - now).total_seconds()
        self._attr_extra_state_attributes = attrs

        self.async_write_ha_state()
