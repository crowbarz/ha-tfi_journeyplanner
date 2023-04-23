"""The tfi_journeyplanner integration."""
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
    # CONF_DEPARTURE_HORIZON,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_NO_DATA,
    CONF_UPDATE_HORIZON_FAST,
    # DEFAULT_DEPARTURE_HORIZON,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_FAST,
    DEFAULT_UPDATE_INTERVAL_NO_DATA,
    DEFAULT_UPDATE_HORIZON_FAST,
)
from .tfi_journeyplanner_api import TFIData
from .coordinator import TFIJourneyPlannerCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

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
    # departure_horizon = timedelta(
    #     **options.get(CONF_DEPARTURE_HORIZON, DEFAULT_DEPARTURE_HORIZON)
    # )
    update_interval = timedelta(
        **options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )
    update_interval_fast = timedelta(
        **options.get(CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST)
    )
    update_interval_no_data = timedelta(
        **options.get(CONF_UPDATE_INTERVAL_NO_DATA, DEFAULT_UPDATE_INTERVAL_NO_DATA)
    )
    update_horizon_fast = timedelta(
        **options.get(CONF_UPDATE_HORIZON_FAST, DEFAULT_UPDATE_HORIZON_FAST)
    )
    coordinator = TFIJourneyPlannerCoordinator(
        hass,
        tfi_data,
        # departure_horizon,
        update_interval,
        update_interval_fast,
        update_interval_no_data,
        update_horizon_fast,
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
