"""Config flow for TFI Journey Planner integration."""
from __future__ import annotations

import logging
from typing import Any, Tuple

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_TITLE,
    CONF_STOP_IDS,
    CONF_SERVICE_IDS,
    CONF_LIMIT_DEPARTURES,
    CONF_DEPARTURE_HORIZON,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_NO_DATA,
    CONF_UPDATE_HORIZON_FAST,
    CONF_REALTIME_ONLY,
    CONF_INCLUDE_CANCELLED,
    ENTRY_DATA,
    ENTRY_OPTIONS,
    DEFAULT_TITLE,
    DEFAULT_DEPARTURE_HORIZON,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_FAST,
    DEFAULT_UPDATE_INTERVAL_NO_DATA,
    DEFAULT_UPDATE_HORIZON_FAST,
)

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA_ENTRIES = {
    vol.Optional(CONF_SERVICE_IDS): selector.SelectSelector(
        selector.SelectSelectorConfig(options=[], custom_value=True, multiple=True),
    ),
    vol.Required(CONF_LIMIT_DEPARTURES, default=0): vol.Coerce(
        int,
        selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=99, mode=selector.NumberSelectorMode.SLIDER
            )
        ),
    ),
    vol.Required(
        CONF_DEPARTURE_HORIZON, default=DEFAULT_DEPARTURE_HORIZON
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_HORIZON_FAST, default=DEFAULT_UPDATE_HORIZON_FAST
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_INTERVAL_FAST, default=DEFAULT_UPDATE_INTERVAL_FAST
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_INTERVAL_NO_DATA, default=DEFAULT_UPDATE_INTERVAL_NO_DATA
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(CONF_REALTIME_ONLY, default=False): selector.BooleanSelector(),
    vol.Required(CONF_INCLUDE_CANCELLED, default=False): selector.BooleanSelector(),
}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TITLE, default=DEFAULT_TITLE): selector.TextSelector(),
        vol.Required(CONF_STOP_IDS): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[], custom_value=True, multiple=True),
        ),
        **OPTIONS_SCHEMA_ENTRIES,
    }
)

STEP_OPTIONS_SCHEMA = vol.Schema({**OPTIONS_SCHEMA_ENTRIES})


async def validate_input(
    _hass: HomeAssistant, user_input: dict[str, Any]
) -> Tuple[dict[str, Any], dict[str, Any]]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    if CONF_STOP_IDS in user_input:
        stop_ids: list[str] = user_input[CONF_STOP_IDS]
        if not stop_ids:
            raise MissingStopIds

    # Return info that you want to store in the config entry.
    # title = DEFAULT_TITLE  # + (" Stop " if len(stop_ids) == 1 else " Stops ")
    # title += ", ".join([str(stop) for stop in stop_ids])
    # return {"title": title, **data}
    data = {k: v for (k, v) in user_input.items() if k in ENTRY_DATA}
    options = {k: v for (k, v) in user_input.items() if k in ENTRY_OPTIONS}
    return (data, options)


class TFIJourneyPlannerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for tfi_journeyplanner."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TFIJourneyPlannerOptionsFlow:
        """Get the options flow for this handler."""
        return TFIJourneyPlannerOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}

        if user_input is not None:
            try:
                (data, options) = await validate_input(self.hass, user_input)
            except MissingStopIds:
                errors["base"] = "missing_stop_ids"
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", str(exc))
                errors["base"] = "unknown"
                description_placeholders["exception"] = str(exc)
            else:
                return self.async_create_entry(
                    title=data["title"], data=data, options=options
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders=description_placeholders,
        )


class TFIJourneyPlannerOptionsFlow(config_entries.OptionsFlow):
    """Handle TFI Journey Planner options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise TFI Journey Planner options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow for TFI Journey Planner."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}

        if user_input is not None:
            try:
                (_, options) = await validate_input(self.hass, user_input)
            except MissingStopIds:
                errors["base"] = "missing_stop_ids"
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", str(exc))
                errors["base"] = "unknown"
                description_placeholders["exception"] = str(exc)
            else:
                return self.async_create_entry(title="", data=options)
            options = user_input
        else:
            options = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                STEP_OPTIONS_SCHEMA, options
            ),
            errors=errors,
            description_placeholders=description_placeholders,
        )


class MissingStopIds(HomeAssistantError):
    """Error to indicate we cannot connect."""
