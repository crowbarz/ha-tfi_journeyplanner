"""The TFI Journey Planner integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_NO_DATA,
    CONF_UPDATE_HORIZON_FAST,
)
from .tfi_journeyplanner_api import TFIData
from .coordinator import TFIJourneyPlannerCoordinator
from .util import get_duration_option

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up tfi_journeyplanner from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    ## Set up platform data update coordinator
    try:
        tfi_data = TFIData()
        await tfi_data.setup()
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.error(
            "Could not set up integration: %s: %s", type(exc).__name__, str(exc)
        )
        raise PlatformNotReady  # pylint: disable=raise-missing-from

    options = entry.options
    coordinator = TFIJourneyPlannerCoordinator(
        hass,
        tfi_data,
        # departure_horizon,
        get_duration_option(options, CONF_UPDATE_INTERVAL),
        get_duration_option(options, CONF_UPDATE_INTERVAL_FAST),
        get_duration_option(options, CONF_UPDATE_INTERVAL_NO_DATA),
        get_duration_option(options, CONF_UPDATE_HORIZON_FAST),
    )

    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["tfi_data"] = tfi_data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    # coordinator: TFIJourneyPlannerCoordinator = entry_data["coordinator"]
    tfi_data: TFIData = entry_data["tfi_data"]

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await tfi_data.cleanup()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
