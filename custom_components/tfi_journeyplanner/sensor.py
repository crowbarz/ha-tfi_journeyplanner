"""TFI Journey Planner sensor integration."""

from __future__ import annotations

from typing import Any

# import asyncio
import logging

from datetime import datetime, timedelta

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
    CONF_STOPS,
    CONF_STOP_IDS,
    CONF_SERVICE_IDS,
    CONF_DIRECTION,
    CONF_LIMIT_DEPARTURES,
    CONF_DEPARTURE_HORIZON,
    CONF_REALTIME_ONLY,
    CONF_INCLUDE_CANCELLED,
    DEFAULTS,
    DEFAULT_SENSOR_ICON,
    DEFAULT_DEPARTURE_HORIZON,
)
from .tfi_journeyplanner_api import TFIData
from .coordinator import TFIJourneyPlannerCoordinator
from .device import get_device_info, get_device_unique_id
from .util import get_duration_option

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
    options = entry.options

    entities = []
    entity_unique_ids = {}
    for stop in options[CONF_STOPS]:
        stop_ids = stop[CONF_STOP_IDS]
        stop_service_ids = stop.get(CONF_SERVICE_IDS)
        stop_direction = stop.get(CONF_DIRECTION)
        service_ids = stop_service_ids or options.get(CONF_SERVICE_IDS, [])
        direction = stop_direction or options.get(CONF_DIRECTION, [])
        limit_departures = stop.get(
            CONF_LIMIT_DEPARTURES, options.get(CONF_LIMIT_DEPARTURES)
        )
        departure_horizon = get_duration_option(
            stop,
            CONF_DEPARTURE_HORIZON,
            default=get_duration_option(
                options, CONF_DEPARTURE_HORIZON, default=DEFAULT_DEPARTURE_HORIZON
            ),
        )

        name = (
            "Stop "
            + ", ".join(stop_ids)
            + (" Service " + ", ".join(stop_service_ids) if stop_service_ids else "")
            + (" Direction " + ", ".join(stop_direction) if stop_direction else "")
        )
        unique_id = get_device_unique_id(entry, "+".join(stop_ids))
        if unique_id not in entity_unique_ids:
            entity_unique_ids[unique_id] = 1
        else:
            entity_unique_ids[unique_id] += 1
            unique_id += f"_{entity_unique_ids[unique_id]}"

        entities.append(
            TfiJourneyPlannerSensor(
                name,
                unique_id=unique_id,
                entry=entry,
                coordinator=coordinator,
                tfi_data=tfi_data,
                stop=stop,
                service_ids=service_ids,
                direction=direction,
                limit_departures=limit_departures,
                departure_horizon=departure_horizon,
            )
        )
    async_add_entities(entities)


class TfiJourneyPlannerSensor(CoordinatorEntity, SensorEntity):
    """TFI Journey Planner sensor class."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        name: str,
        unique_id: str,
        entry: ConfigEntry,
        coordinator: TFIJourneyPlannerCoordinator,
        tfi_data: TFIData,
        stop: dict[str, Any],
        service_ids: list[str] | None,
        direction: list[str] | None,
        limit_departures: int | None,
        departure_horizon: timedelta,
    ):
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = DEFAULT_SENSOR_ICON
        self._coordinator = coordinator
        self._tfi_data = tfi_data
        self._config_entry = entry
        self._stop = stop
        self._service_ids = service_ids
        self._direction = direction
        self._limit_departures = limit_departures
        self._departure_horizon = departure_horizon
        self._realtime_only = entry.options.get(
            CONF_INCLUDE_CANCELLED, DEFAULTS[CONF_INCLUDE_CANCELLED]
        )
        self._include_cancelled = entry.options.get(
            CONF_REALTIME_ONLY, DEFAULTS[CONF_REALTIME_ONLY]
        )

        super().__init__(coordinator, context=stop[CONF_STOP_IDS])
        _LOGGER.debug(
            "subscribing stop %s (unique_id=%s) to coordinator", self._stop, unique_id
        )

        self._departures = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return get_device_info(self._config_entry)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        stop = self._stop

        departures = self._tfi_data.get_filtered_departures(
            stop[CONF_STOP_IDS],
            service_ids=self._service_ids,
            direction=self._direction,
            limit_departures=self._limit_departures,
            departure_horizon=self._departure_horizon,
            realtime_only=self._realtime_only,
            include_cancelled=self._include_cancelled,
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
