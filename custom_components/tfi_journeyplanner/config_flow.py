"""Config flow for TFI Journey Planner integration."""
from __future__ import annotations

import logging
from typing import Any, Tuple
import re
from datetime import datetime, timedelta

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_TITLE,
    CONF_STOPS,
    CONF_STOP_IDS,
    CONF_SERVICE_IDS,
    CONF_DIRECTION,
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
    DEFAULTS,
    DEFAULT_TITLE,
    DEFAULT_DEPARTURE_HORIZON,
)
from .util import duration_to_seconds, seconds_to_duration, timedelta_str

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA_ENTRIES = {
    vol.Optional(CONF_SERVICE_IDS): selector.SelectSelector(
        selector.SelectSelectorConfig(options=[], custom_value=True, multiple=True),
    ),
    vol.Optional(CONF_DIRECTION): selector.SelectSelector(
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
        CONF_DEPARTURE_HORIZON, default=seconds_to_duration(DEFAULT_DEPARTURE_HORIZON)
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_HORIZON_FAST,
        default=seconds_to_duration(DEFAULTS[CONF_UPDATE_HORIZON_FAST]),
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_INTERVAL,
        default=seconds_to_duration(DEFAULTS[CONF_UPDATE_INTERVAL]),
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_INTERVAL_FAST,
        default=seconds_to_duration(DEFAULTS[CONF_UPDATE_INTERVAL_FAST]),
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_UPDATE_INTERVAL_NO_DATA,
        default=seconds_to_duration(DEFAULTS[CONF_UPDATE_INTERVAL_NO_DATA]),
    ): selector.DurationSelector(selector.DurationSelectorConfig(enable_day=False)),
    vol.Required(
        CONF_REALTIME_ONLY, default=DEFAULTS[CONF_REALTIME_ONLY]
    ): selector.BooleanSelector(),
    vol.Required(
        CONF_INCLUDE_CANCELLED, default=DEFAULTS[CONF_INCLUDE_CANCELLED]
    ): selector.BooleanSelector(),
}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TITLE, default=DEFAULT_TITLE): selector.TextSelector(),
        vol.Required(CONF_STOPS): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[], custom_value=True, multiple=True),
        ),
        **OPTIONS_SCHEMA_ENTRIES,
    }
)

STEP_OPTIONS_SCHEMA = vol.Schema({**OPTIONS_SCHEMA_ENTRIES})


def convert_options(options: dict[str, Any]) -> dict[str, Any]:
    """Convert options for config flow."""
    flow_options = {**options}

    if CONF_STOPS in options:
        stop_list = []
        for stop in options[CONF_STOPS]:
            if isinstance(stop, dict):
                stop_list.append(
                    stop[CONF_STOP_IDS]
                    + (
                        "=" + stop[CONF_SERVICE_IDS].join(",")
                        if CONF_SERVICE_IDS in stop
                        else ""
                    )
                    + (
                        "/" + stop[CONF_DIRECTION].join(",")
                        if CONF_DIRECTION in stop
                        else ""
                    )
                    + (
                        "@"
                        + timedelta_str(timedelta(seconds=stop[CONF_DEPARTURE_HORIZON]))
                        if CONF_DEPARTURE_HORIZON in stop
                        else ""
                    )
                    + (
                        "#" + str(stop[CONF_LIMIT_DEPARTURES])
                        if CONF_LIMIT_DEPARTURES in stop
                        else ""
                    )
                )
            else:
                stop_list.append(stop)
        flow_options[CONF_STOPS] = stop_list

    flow_options[CONF_DEPARTURE_HORIZON] = seconds_to_duration(
        options.get(CONF_DEPARTURE_HORIZON), DEFAULT_DEPARTURE_HORIZON
    )
    flow_options[CONF_UPDATE_INTERVAL] = seconds_to_duration(
        options.get(CONF_UPDATE_INTERVAL), DEFAULTS[CONF_UPDATE_INTERVAL]
    )
    flow_options[CONF_UPDATE_INTERVAL_FAST] = seconds_to_duration(
        options.get(CONF_UPDATE_INTERVAL_FAST), DEFAULTS[CONF_UPDATE_INTERVAL_FAST]
    )
    flow_options[CONF_UPDATE_INTERVAL_NO_DATA] = seconds_to_duration(
        options.get(CONF_UPDATE_INTERVAL_NO_DATA),
        DEFAULTS[CONF_UPDATE_INTERVAL_NO_DATA],
    )
    flow_options[CONF_UPDATE_HORIZON_FAST] = seconds_to_duration(
        options.get(CONF_UPDATE_HORIZON_FAST), DEFAULTS[CONF_UPDATE_HORIZON_FAST]
    )

    return flow_options


def validate_input(
    user_input: dict[str, Any]
) -> Tuple[dict[str, Any], dict[str, Any], dict[str, str], dict[str, str]]:
    """Validate the user input."""
    errors: dict[str, str] = {}
    description_placeholders: dict[str, str] = {}

    data = {k: v for (k, v) in user_input.items() if k in ENTRY_DATA}
    options = {k: v for (k, v) in user_input.items() if k in ENTRY_OPTIONS}

    def parse_stop_raw(stop_raw: str) -> dict[str, Any]:
        stop_split = re.split(r"([=/@#])", stop_raw)
        stop = {CONF_STOP_IDS: stop_split.pop(0).split(",")}
        while len(stop_split) > 0:
            match stop_split.pop(0):
                case "=":  ## service_ids override
                    stop.update({CONF_SERVICE_IDS: stop_split.pop(0).split(",")})
                case "/":  ## direction override
                    stop.update({CONF_DIRECTION: stop_split.pop(0).split(",")})
                case "#":  ## limit_departures override
                    stop.update({CONF_LIMIT_DEPARTURES: int(stop_split.pop(0))})
                case "@":  ## departure_horizon override
                    stop.update(
                        {
                            CONF_DEPARTURE_HORIZON: timedelta(
                                datetime.strptime(stop_split.pop(0), "%H:%M:%S")
                            ).total_seconds()
                        }
                    )
        return stop

    try:
        if CONF_STOPS in user_input:
            stops_raw: list[str] = user_input[CONF_STOPS]
            stops = []
            if not stops_raw:
                errors[CONF_STOPS] = "missing_stops"
            else:
                for stop_raw in stops_raw:
                    try:
                        stop = parse_stop_raw(stop_raw)
                    except Exception:  # pylint: disable=broad-except
                        errors[CONF_STOPS] = "invalid_stop_ids"
                        description_placeholders.setdefault("stops", [])
                        description_placeholders["stops"].append(stop_raw)

                    stops.append(stop)
                data[CONF_STOPS] = stops

        if CONF_DEPARTURE_HORIZON in user_input:
            if duration := duration_to_seconds(user_input[CONF_DEPARTURE_HORIZON]):
                options[CONF_DEPARTURE_HORIZON] = duration
        if CONF_UPDATE_INTERVAL in user_input:
            if duration := duration_to_seconds(user_input[CONF_UPDATE_INTERVAL]):
                options[CONF_UPDATE_INTERVAL] = duration
        if CONF_UPDATE_INTERVAL_FAST in user_input:
            if duration := duration_to_seconds(user_input[CONF_UPDATE_INTERVAL_FAST]):
                options[CONF_UPDATE_INTERVAL_FAST] = duration
        if CONF_UPDATE_INTERVAL_NO_DATA in user_input:
            if duration := duration_to_seconds(
                user_input[CONF_UPDATE_INTERVAL_NO_DATA]
            ):
                options[CONF_UPDATE_INTERVAL_NO_DATA] = duration
        if CONF_UPDATE_HORIZON_FAST in user_input:
            if duration := duration_to_seconds(user_input[CONF_UPDATE_HORIZON_FAST]):
                options[CONF_UPDATE_HORIZON_FAST] = duration

        return (data, options, errors, description_placeholders)
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception: %s", str(exc))
        errors["base"] = "unknown"
        description_placeholders["exception"] = str(exc)
        return (data, options, errors, description_placeholders)


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
            (data, options, errors, description_placeholders) = validate_input(
                user_input
            )
            if not errors:
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
            (_, options, errors, description_placeholders) = validate_input(user_input)
            if not errors:
                return self.async_create_entry(title="", data=options)
            options = user_input
        else:
            options = convert_options(self.config_entry.options)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                STEP_OPTIONS_SCHEMA, options
            ),
            errors=errors,
            description_placeholders=description_placeholders,
        )
