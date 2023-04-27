"""TFI Journey Planner device settings."""

from __future__ import annotations

import logging

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_STOPS, CONF_STOP_IDS

_LOGGER = logging.getLogger(__name__)


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device info."""
    return DeviceInfo(
        identifiers={
            # Serial numbers are unique identifiers within a specific domain
            (
                DOMAIN,
                *[
                    stop_id
                    for stop in entry.data[CONF_STOPS]
                    for stop_id in stop[CONF_STOP_IDS]
                ],
            )
        },
        name=entry.title,
        manufacturer="Transport for Ireland",
        configuration_url="https://journeyplanner.transportforireland.ie/",
        # model=self.light.productname,
        # sw_version=self.light.swversion,
    )


def get_device_unique_id(entry: ConfigEntry, suffix: str = None) -> str:
    """Return the unique ID for the device with optional suffix."""
    return DOMAIN + "_" + entry.entry_id + ("_" + suffix if suffix else "")
