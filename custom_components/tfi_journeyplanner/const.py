"""Constants for the tfi_journeyplanner integration."""

from datetime import timedelta

DOMAIN = "tfi_journeyplanner"

CONF_TITLE = "title"
CONF_STOPS = "stops"
CONF_STOP_IDS = "stop_ids"
CONF_SERVICE_IDS = "service_ids"
CONF_DIRECTION = "direction"
CONF_LIMIT_DEPARTURES = "limit_departures"
CONF_DEPARTURE_HORIZON = "departure_horizon"
CONF_UPDATE_HORIZON_FAST = "update_horizon_fast"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_UPDATE_INTERVAL_FAST = "update_interval_fast"
CONF_UPDATE_INTERVAL_NO_DATA = "update_interval_no_data"
CONF_REALTIME_ONLY = "realtime_only"
CONF_INCLUDE_CANCELLED = "include_cancelled"

ENTRY_DATA = {
    CONF_TITLE,
    CONF_STOPS,
}
ENTRY_OPTIONS = {
    CONF_SERVICE_IDS,
    CONF_DIRECTION,
    CONF_LIMIT_DEPARTURES,
    CONF_DEPARTURE_HORIZON,
    CONF_UPDATE_HORIZON_FAST,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_NO_DATA,
    CONF_REALTIME_ONLY,
    CONF_INCLUDE_CANCELLED,
}

DEFAULTS = {
    CONF_UPDATE_HORIZON_FAST: timedelta(minutes=7),
    CONF_UPDATE_INTERVAL: timedelta(minutes=5),
    CONF_UPDATE_INTERVAL_FAST: timedelta(minutes=1),
    CONF_UPDATE_INTERVAL_NO_DATA: timedelta(hours=1),
    CONF_LIMIT_DEPARTURES: 10,
    CONF_REALTIME_ONLY: False,
    CONF_INCLUDE_CANCELLED: False,
}
DEFAULT_TITLE = "TFI Journey Planner"
DEFAULT_DEPARTURE_HORIZON = timedelta(hours=1)
DEFAULT_UPDATE_NO_DATA_THRESHOLD = 3
