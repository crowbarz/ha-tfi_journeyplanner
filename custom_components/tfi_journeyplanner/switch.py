"""TFI Journey Planner switch integration."""

from __future__ import annotations

import logging

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import TFIJourneyPlannerCoordinator
from .device import get_device_info, get_device_unique_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: TFIJourneyPlannerCoordinator = entry_data["coordinator"]
    name = "Polling Enabled"
    unique_id = get_device_unique_id(entry, "switch")
    async_add_entities([TfiJourneyPlannerSwitch(name, unique_id, entry, coordinator)])


class TfiJourneyPlannerSwitch(SwitchEntity):
    """TFI Journey Planner switch class."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        name: str,
        unique_id: str,
        entry: ConfigEntry,
        coordinator: TFIJourneyPlannerCoordinator,
    ):
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._config_entry = entry
        self._coordinator = coordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return get_device_info(self._config_entry)

    @property
    def is_on(self) -> bool:
        """Polling state."""
        return self._coordinator.polling_enabled

    async def async_turn_on(self, **_kwargs) -> None:
        """Enable polling."""
        if not self._coordinator.polling_enabled:
            self._coordinator.is_polling = True
            await self._coordinator.async_refresh()
            self.schedule_update_ha_state()

    async def async_turn_off(self, **_kwargs) -> None:
        """Disable polling."""
        if self._coordinator.polling_enabled:
            self._coordinator.is_polling = False
            await self._coordinator.async_refresh()
            self.schedule_update_ha_state()
