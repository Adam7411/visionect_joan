import logging
import urllib.parse
import voluptuous as vol
from datetime import datetime, timezone, timedelta
from pathlib import Path
import uuid
from functools import partial
import asyncio
import feedparser

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from homeassistant.components.camera import async_get_image
from homeassistant.helpers.network import get_url
from homeassistant.components.recorder import history, get_instance
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .api import VisionectAPI
from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY,
    SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE, EVENT_COMMAND_RESULT,
    NETWORK_RETRY_DELAY, ATTR_PREDEFINED_URL,
    CONF_VIEWS, CONF_MAIN_MENU_URL, CONF_CLEANUP_MAX_AGE, CONF_CLEANUP_INTERVAL
)
from .html_generator import (
    create_status_panel_url, create_text_message_url, create_todo_list_url,
    create_rss_feed_url, create_energy_panel_url, create_qr_code_url,
    create_calendar_url, create_monthly_calendar_url, create_weather_url,
    create_simple_cache_buster, _generate_graph_image,
    _add_interactive_layer_to_url, _get_lang,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "text", "button", "select", "camera"]

# --- VIEW PARSING FUNCTION ---
def _parse_views(views_data) -> list[dict]:
    """Processes view data (text or list format) into a standardized list of dictionaries."""
    if isinstance(views_data, list):
        return views_data
    if isinstance(views_data, str):
        views = []
        for line in views_data.strip().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            try:
                name, url = line.split(":", 1)
                name = name.strip()
                url = url.strip()
                if name and url:
                    views.append({"name": name, "url": url})
            except Exception as e:
                _LOGGER.warning("Failed to parse view line: '%s'. Error: %s", line, e)
        return views
    return []


# --- SERVICE CONSTANTS AND SCHEMAS ---
ATTR_ADD_BACK_BUTTON = "add_back_button"
ATTR_CLICK_ANYWHERE_TO_RETURN = "click_anywhere_to_return"
ATTR_CLICK_ANYWHERE_TO_ACTION = "click_anywhere_to_action"
ATTR_BACK_BUTTON_URL = "back_button_url"
ATTR_ACTION_WEBHOOK_ID = "action_webhook_id"
# NOWY ATRYBUT DLA DRUGIEGO WEBHOOKA
ATTR_ACTION_WEBHOOK_2_ID = "action_webhook_2_id"
ATTR_SMALL_SCREEN = "small_screen_optimized"

# Service names we expose (kept for compatibility)
SERVICE_SET_URL = "set_url"
SERVICE_SEND_TEXT = "send_text"
SERVICE_SET_DISPLAY_ROTATION = "set_display_rotation"
SERVICE_SEND_CALENDAR = "send_calendar"
SERVICE_SEND_WEATHER = "send_weather"
SERVICE_SEND_ENERGY_PANEL = "send_energy_panel"
SERVICE_SEND_TODO_LIST = "send_todo_list"
SERVICE_SEND_CAMERA_SNAPSHOT = "send_camera_snapshot"
SERVICE_SEND_STATUS_PANEL = "send_status_panel"
SERVICE_SEND_SENSOR_GRAPH = "send_sensor_graph"
SERVICE_SEND_RSS_FEED = "send_rss_feed"

ATTR_URL = "url"
ATTR_MESSAGE = "message"
ATTR_TEXT_COLOR = "text_color"
ATTR_BACKGROUND_COLOR = "background_color"
ATTR_TEXT_SIZE = "text_size"
ATTR_TEXT_ALIGN = "text_align"
ATTR_FONT_FAMILY = "font_family"
ATTR_FONT_WEIGHT = "font_weight"
ATTR_DISPLAY_ROTATION = "display_rotation"
ATTR_LAYOUT = "layout"
ATTR_IMAGE_URL = "image_url"
ATTR_IMAGE_ZOOM = "image_zoom"
ATTR_DURATION = "duration"
ATTR_DATA = "data"
ATTR_BOX_SIZE = "box_size"
ATTR_BORDER = "border"
ATTR_FILL_COLOR = "fill_color"
ATTR_BACK_COLOR = "back_color"
ATTR_QR_MESSAGE_TEXT_SIZE = "qr_message_text_size"
ATTR_QR_MESSAGE_POSITION = "qr_message_position"
ATTR_CALENDAR_ENTITY = "calendar_entity"
ATTR_DURATION_DAYS = "duration_days"
ATTR_DISPLAY_STYLE = "display_style"
ATTR_WEATHER_ENTITY = "weather_entity"
ATTR_POWER_USAGE_ENTITY = "power_usage_entity"
ATTR_DAILY_CONSUMPTION_ENTITY = "daily_consumption_entity"
ATTR_DAILY_PRODUCTION_ENTITY = "daily_production_entity"
ATTR_DAILY_GRID_IMPORT_ENTITY = "daily_grid_import_entity"
ATTR_DAILY_GRID_EXPORT_ENTITY = "daily_grid_export_entity"
ATTR_TODO_ENTITY = "todo_entity"
ATTR_TITLE = "title"
ATTR_CAMERA_ENTITY = "camera_entity"
ATTR_CAPTION = "caption"
ATTR_ENTITIES = "entities"
ATTR_DURATION_HOURS = "duration_hours"
ATTR_GRAPH_TYPE = "graph_type"
ATTR_SHOW_POINTS = "show_points"

EINK_COLORS = ["black", "white"]
FONT_WEIGHTS = ["normal", "bold"]
LAYOUT_OPTIONS = ["text_only", "image_top", "image_bottom", "image_left", "image_right", "image_only"]

# Font list kept here for service schema validation
THEMED_FONTS = {
    "Modern": "'Trebuchet MS', Helvetica, sans-serif",
    "Readable": "Verdana, Geneva, sans-serif",
    "Archivo Black": "'Archivo Black', sans-serif",
    "Arbutus": "'Arbutus', serif",
    "Asimovian": "'Asimovian', sans-serif",
    "Bangers": "'Bangers', cursive",
    "Blaka": "'Blaka', cursive",
    "Bungee": "'Bungee', cursive",
    "Bungee Shade": "'Bungee Shade', cursive",
    "Cherry Bomb One": "'Cherry Bomb One', cursive",
    "Cinzel Decorative": "'Cinzel Decorative', serif",
    "Damion": "'Damion', cursive",
    "Diplomata SC": "'Diplomata SC', cursive",
    "Fascinate": "'Fascinate', cursive",
    "Joti One": "'Joti One', cursive",
    "Libertinus Keyboard": "'Libertinus Keyboard', serif",
    "MedievalSharp": "'MedievalSharp', cursive",
    "Michroma": "'Michroma', sans-serif",
    "New Rocker": "'New Rocker', cursive",
    "Rubik Wet Paint": "'Rubik Wet Paint', cursive",
    "Spicy Rice": "'Spicy Rice', cursive",
    "Story Script": "'Story Script', cursive",
}

GOOGLE_FONTS_IMPORT_URL = "https://fonts.googleapis.com/css2?family=Archivo+Black&family=Arbutus&family=Asimovian&family=Bangers&family=Blaka&family=Bungee&family=Bungee+Shade&family=Cherry+Bomb+One&family=Cinzel+Decorative:wght@400;700;900&family=Damion&family=Diplomata+SC&family=Fascinate&family=Joti+One&family=Libertinus+Keyboard&family=MedievalSharp&family=Michroma&family=New+Rocker&family=Rubik+Wet+Paint&family=Spicy+Rice&family=Story+Script&display=swap"

INTERACTIVE_SCHEMA_EXTENSION = {
    vol.Optional(ATTR_ADD_BACK_BUTTON, default=False): cv.boolean,
    vol.Optional(ATTR_CLICK_ANYWHERE_TO_RETURN, default=False): cv.boolean,
    vol.Optional(ATTR_CLICK_ANYWHERE_TO_ACTION, default=False): cv.boolean,
    vol.Optional(ATTR_BACK_BUTTON_URL): cv.string,
    vol.Optional(ATTR_ACTION_WEBHOOK_ID): cv.string,
    # DODANIE NOWEGO POLA DO SCHEMATU
    vol.Optional(ATTR_ACTION_WEBHOOK_2_ID): cv.string,
    vol.Optional(ATTR_SMALL_SCREEN, default=False): cv.boolean,
}

SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Optional(ATTR_URL): cv.string,
    vol.Optional(ATTR_PREDEFINED_URL): cv.string,
})

SERVICE_SEND_TEXT_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_MESSAGE): cv.template,
    vol.Optional(ATTR_TEXT_COLOR, default="black"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_BACKGROUND_COLOR, default="white"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_TEXT_SIZE, default=28): vol.All(vol.Coerce(int), vol.Range(min=10, max=150)),
    vol.Optional(ATTR_TEXT_ALIGN, default="center"): vol.In(["left", "center", "right"]),
    vol.Optional(ATTR_FONT_FAMILY, default="Modern"): vol.In(list(THEMED_FONTS.keys())),
    vol.Optional(ATTR_FONT_WEIGHT, default="normal"): vol.In(FONT_WEIGHTS),
    vol.Optional(ATTR_LAYOUT, default="text_only"): vol.In(LAYOUT_OPTIONS),
    vol.Optional(ATTR_IMAGE_URL): cv.string,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=50, max=200)),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SET_DISPLAY_ROTATION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_DISPLAY_ROTATION): vol.In(list(DISPLAY_ROTATIONS.keys())),
})

SERVICE_DEVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
})

SERVICE_SLEEP_DEVICE_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_DURATION, default=3600): vol.All(vol.Coerce(int), vol.Range(min=1)),
})

SERVICE_SEND_QR_CODE_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_DATA): cv.string,
    vol.Optional(ATTR_MESSAGE, default=""): cv.string,
    vol.Optional(ATTR_QR_MESSAGE_TEXT_SIZE, default=24): vol.All(vol.Coerce(int), vol.Range(min=10, max=100)),
    vol.Optional(ATTR_QR_MESSAGE_POSITION, default="below"): vol.In(["below", "above"]),
    vol.Optional(ATTR_BOX_SIZE, default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
    vol.Optional(ATTR_BORDER, default=4): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
    vol.Optional(ATTR_FILL_COLOR, default="black"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_BACK_COLOR, default="white"): vol.In(EINK_COLORS),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_CALENDAR_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_CALENDAR_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DURATION_DAYS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
    vol.Optional(ATTR_DISPLAY_STYLE, default="modern"): vol.In(["modern", "minimalist", "monthly_grid"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_WEATHER_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_WEATHER_ENTITY): cv.entity_id,
    vol.Optional(ATTR_LAYOUT, default="detailed_summary"): vol.In([
        "detailed_summary", "daily_forecast_list", "weather_graph_panel"
    ]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_ENERGY_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_POWER_USAGE_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_CONSUMPTION_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_PRODUCTION_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_GRID_IMPORT_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_GRID_EXPORT_ENTITY): cv.entity_id,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_TODO_LIST_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_TODO_ENTITY): cv.entity_id,
    vol.Optional(ATTR_TITLE): cv.string,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_CAMERA_SNAPSHOT_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
    vol.Optional(ATTR_CAPTION): cv.template,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=50, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_STATUS_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_TITLE, default="Status Panel"): cv.string,
    vol.Required(ATTR_ENTITIES): cv.entity_ids,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_SENSOR_GRAPH_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_ENTITIES): cv.entity_ids,
    vol.Optional(ATTR_DURATION_HOURS, default=24): vol.All(vol.Coerce(int), vol.Range(min=1, max=48)),
    vol.Optional(ATTR_GRAPH_TYPE, default="line"): vol.In(["line", "bar"]),
    vol.Optional(ATTR_SHOW_POINTS, default=False): cv.boolean,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=50, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_RSS_FEED_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required("feed_url"): cv.url,
    vol.Optional("title", default="Wiadomości"): cv.string,
    vol.Optional("max_items", default=5): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

# --- MEDIA CLEANUP FUNCTIONS ---
def _schedule_media_cleanup(hass: HomeAssistant) -> None:
    """Schedules periodic cleanup of old media files."""
    interval_h = max(1, int(hass.data[DOMAIN]["cleanup_interval_hours"]))
    async def _periodic_cleanup(now=None):
        await _async_cleanup_media_files(hass)
    hass.async_create_task(_periodic_cleanup())
    async_track_time_interval(hass, _periodic_cleanup, timedelta(hours=interval_h))

async def _async_cleanup_media_files(hass: HomeAssistant) -> None:
    """Removes old snapshots and graph files from the www folder."""
    MEDIA_PREFIXES = ("visionect_snapshot_", "visionect_graph_")
    max_age_h = max(1, int(hass.data[DOMAIN]["cleanup_max_age_hours"]))
    cutoff = dt_util.utcnow() - timedelta(hours=max_age_h)
    www_path = Path(hass.config.path("www"))
    if not www_path.exists():
        return
    def _cleanup():
        removed = 0
        for p in www_path.iterdir():
            if not p.is_file() or not p.name.startswith(MEDIA_PREFIXES):
                continue
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    p.unlink(missing_ok=True)
                    removed += 1
            except Exception:
                continue
        return removed
    removed = await hass.async_add_executor_job(_cleanup)
    if removed:
        _LOGGER.info(f"Visionect cleanup: removed {removed} old media files from www/")

# ----------------- Integration Setup -----------------

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Visionect integration from YAML configuration (legacy support)."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        # Save YAML configuration as fallback/initial data
        hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update listener."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Visionect from a config entry."""
    _LOGGER.info("Starting setup of Visionect Joan config entry.")
    
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    yaml_config = hass.data[DOMAIN].get("yaml_config", {})
    
    # 1. PROCESS VIEWS (Handle string/list format for configuration migration)
    views_data_from_options = entry.options.get(CONF_VIEWS, [])
    views = _parse_views(views_data_from_options)
    
    # Fallback to YAML views if UI options are empty
    if not views:
        views = yaml_config.get("views", [])

    # 2. LOAD OTHER OPTIONS (UI options take precedence over YAML)
    main_menu = entry.options.get(CONF_MAIN_MENU_URL, yaml_config.get("main_menu_url"))
    cleanup_age = entry.options.get(CONF_CLEANUP_MAX_AGE, yaml_config.get("cleanup_max_age_hours", 24))
    cleanup_interval = entry.options.get(CONF_CLEANUP_INTERVAL, yaml_config.get("cleanup_interval_hours", 6))

    # Save processed data to global hass.data
    hass.data[DOMAIN]["views"] = views
    hass.data[DOMAIN]["main_menu_url"] = main_menu
    hass.data[DOMAIN]["cleanup_max_age_hours"] = cleanup_age
    hass.data[DOMAIN]["cleanup_interval_hours"] = cleanup_interval

    _schedule_media_cleanup(hass)

    api = VisionectAPI(
        hass,
        entry.data[CONF_HOST],
        entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PASSWORD),
        entry.data.get(CONF_API_KEY),
        entry.data.get(CONF_API_SECRET),
    )
    if not await api.async_test_authentication():
        _LOGGER.error("Authentication failed. Cannot load integration.")
        return False

    async def async_update_data():
        try:
            devices_summary = await api.async_get_all_devices()
            if not devices_summary:
                _LOGGER.warning("No device data from API")
                return {}
            data = {}
            for device_summary in devices_summary:
                uuid_val = device_summary.get("Uuid")
                if not uuid_val:
                    _LOGGER.warning("Device without UUID was skipped")
                    continue
                device_details = await api.async_get_device_data(uuid_val)
                if not device_details:
                    _LOGGER.warning(f"Could not get details for device {uuid_val}")
                    continue
                final_data = device_details
                if "Config" not in final_data: final_data["Config"] = {}
                device_name = device_summary.get("Options", {}).get("Name")
                if device_name and device_name.lower() not in UNKNOWN_STRINGS:
                    final_data["Config"]["Name"] = device_name
                final_data["Options"] = device_summary.get("Options", {})
                final_data["LastUpdated"] = datetime.now(timezone.utc)
                data[uuid_val] = final_data
            _LOGGER.debug(f"Updated data for {len(data)} devices")
            return data
        except Exception as e:
            _LOGGER.error(f"Error during data update: {e}")
            return {}

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"visionect_{entry.entry_id}",
        update_method=async_update_data, update_interval=SCAN_INTERVAL
    )
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()
    
    store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_prefs.json")
    prefs = await store.async_load() or {"back_targets": {}}
    
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api, "coordinator": coordinator,
        "prefs_store": store, "prefs": prefs
    }

    device_reg = dr.async_get(hass)

    # --- Helper functions defined inside async_setup_entry for context access ---
    
    def _get_url_from_predefined(predefined_name: str | None) -> str | None:
        """
        Resolve a predefined view name to its URL (case-insensitive, trimmed).
        Also accept a direct URL pasted into the predefined field.
        """
        if not predefined_name:
            return None

        candidate = str(predefined_name).strip()

        # Allow full URL/HTML pasted into 'predefined_url' field
        if candidate.startswith("http://") or candidate.startswith("https://") or candidate.startswith("data:text/html,"):
            return candidate

        for view in hass.data[DOMAIN].get("views", []) or []:
            name = str(view.get("name", "")).strip()
            if name.lower() == candidate.lower():
                return view.get("url")
        return None

    def _get_url_from_params(call_data: dict, url_key: str, predefined_key: str) -> str | None:
        """
        Return the final URL from direct URL or a predefined view name.
        - url field can be either a full URL/data: or the name of a predefined view
        - predefined_url is resolved the same way, with case-insensitive matching
        """
        direct_url = call_data.get(url_key)
        if direct_url:
            direct_url = str(direct_url).strip()
            if direct_url.startswith("http://") or direct_url.startswith("https://") or direct_url.startswith("data:text/html,"):
                return direct_url
            # treat 'url' as predefined name if not a URL
            resolved = _get_url_from_predefined(direct_url)
            if resolved:
                return resolved

        predefined_name = call_data.get(predefined_key)
        return _get_url_from_predefined(predefined_name)

    def _get_prefs() -> dict:
        return hass.data[DOMAIN][entry.entry_id].setdefault("prefs", {"back_targets": {}})

    def _get_back_url_for_uuid(device_uuid: str, call_data: dict) -> str | None:
        back_url = call_data.get(ATTR_BACK_BUTTON_URL)
        if back_url:
            if not (back_url.startswith("http") or back_url.startswith("data:text/html,")):
                resolved = _get_url_from_predefined(back_url)
                if resolved: return resolved
            return back_url
        prefs = _get_prefs()
        stored_url = prefs.get("back_targets", {}).get(device_uuid)
        if stored_url:
            return stored_url
        return hass.data[DOMAIN].get("main_menu_url")

    def _effective_add_back_button(call_data: dict, back_url: str | None) -> bool:
        """
        Decide whether to show the Back button:
        - Hide if click-anywhere modes are enabled (screen is fully clickable).
        - If user explicitly enabled 'add_back_button', show it.
        - If user provided 'back_button_url' (including a predefined view name), auto-enable it.
        """
        if call_data.get(ATTR_CLICK_ANYWHERE_TO_RETURN) or call_data.get(ATTR_CLICK_ANYWHERE_TO_ACTION):
            return False
        if call_data.get(ATTR_ADD_BACK_BUTTON):
            return True
        # Auto-enable only when user provided the back_button_url explicitly
        if ATTR_BACK_BUTTON_URL in call_data and call_data.get(ATTR_BACK_BUTTON_URL):
            return True
        return False

    async def get_uuids_from_call(call: ServiceCall) -> list[str]:
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if isinstance(device_ids, str): device_ids = [device_ids]
        if not device_ids: return []
        uuids_list = []
        for device_id in device_ids:
            device_entry = device_reg.async_get(device_id)
            if device_entry and (uuid_val := next((i[1] for i in device_entry.identifiers if i[0] == DOMAIN), None)):
                uuids_list.append(uuid_val)
            else:
                _LOGGER.warning(f"Could not find UUID for device_id: {device_id}")
        return uuids_list
    
    # --- Service Handlers ---

    async def handle_set_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        original_url = _get_url_from_params(call.data, ATTR_URL, ATTR_PREDEFINED_URL)
        if not original_url:
            # Lepsza diagnostyka: pokaż co przyszło i jakie mamy widoki
            known = [v.get("name") for v in hass.data[DOMAIN].get("views", []) or []]
            _LOGGER.error(
                "No URL provided. url='%s', predefined_url='%s'. Known predefined view names: %s",
                call.data.get(ATTR_URL), call.data.get(ATTR_PREDEFINED_URL), known
            )
            return

        url_with_buster = create_simple_cache_buster(original_url)
        tasks = [api.async_set_device_url(uuid, url_with_buster) for uuid in uuids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, uuid_val in enumerate(uuids):
            result, status = results[i], "failure"
            if isinstance(result, Exception):
                _LOGGER.error(f"Error changing URL for {uuid_val}: {result}")
            elif result:
                status = "success"
                _LOGGER.info(f"URL for {uuid_val} changed to: {original_url}")
            else:
                _LOGGER.error(f"Failed to change URL for {uuid_val}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_URL, "status": status})
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        if isinstance(message_template, Template): message_template.hass = hass
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        content_url = create_text_message_url(
            message, call.data[ATTR_TEXT_COLOR], call.data[ATTR_BACKGROUND_COLOR], f"{call.data[ATTR_TEXT_SIZE]}px",
            call.data[ATTR_TEXT_ALIGN], call.data[ATTR_FONT_FAMILY], call.data[ATTR_FONT_WEIGHT],
            call.data[ATTR_LAYOUT], call.data.get(ATTR_IMAGE_URL), call.data.get(ATTR_IMAGE_ZOOM),
        )
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending text to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_TEXT, "status": status})

    async def handle_send_weather(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        weather_entity_id = call.data[ATTR_WEATHER_ENTITY]
        layout = call.data[ATTR_LAYOUT]
        lang = _get_lang(hass)
        small_screen = call.data[ATTR_SMALL_SCREEN]
        for device_uuid in uuids:
            device_data = coordinator.data.get(device_uuid, {})
            orientation = str(device_data.get("Config", {}).get("DisplayRotation", "0"))
            weather_state = hass.states.get(weather_entity_id)
            if not weather_state: _LOGGER.error(f"Weather entity not found: {weather_entity_id}"); continue
            daily_forecast, hourly_forecast = None, None
            try:
                daily_response: ServiceResponse = await hass.services.async_call("weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "daily"}, blocking=True, return_response=True)
                if daily_response: daily_forecast = daily_response.get(weather_entity_id, {}).get("forecast", [])
            except Exception as e: _LOGGER.warning(f"Error fetching daily forecast: {e}")
            try:
                hourly_response: ServiceResponse = await hass.services.async_call("weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "hourly"}, blocking=True, return_response=True)
                if hourly_response: hourly_forecast = hourly_response.get(weather_entity_id, {}).get("forecast", [])
            except Exception as e: _LOGGER.warning(f"Error fetching hourly forecast: {e}")
            content_url = await create_weather_url(hass, weather_state, daily_forecast, hourly_forecast, layout, orientation, lang, small_screen)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending weather to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_WEATHER, "status": status})

    async def handle_send_energy_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_states = {key: hass.states.get(entity_id) for key, entity_id in call.data.items() if key.endswith("_entity") and entity_id}
        if not any(entity_states.values()): _LOGGER.error("No valid entities provided."); return
        lang, small_screen = _get_lang(hass), call.data[ATTR_SMALL_SCREEN]
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_energy_panel_url(hass, entity_states, orientation, lang, small_screen)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending panel to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_ENERGY_PANEL, "status": status})

    async def handle_send_todo_list(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        todo_entity_id, title = call.data[ATTR_TODO_ENTITY], call.data.get(ATTR_TITLE)
        lang, small_screen = _get_lang(hass), call.data[ATTR_SMALL_SCREEN]
        if not title:
            todo_state = hass.states.get(todo_entity_id)
            title = todo_state.name if todo_state else ("Lista Zadań" if lang == "pl" else "To-Do List")
        items = []
        try:
            response: ServiceResponse = await hass.services.async_call("todo", "get_items", {"entity_id": todo_entity_id}, blocking=True, return_response=True)
            if response:
                raw_items = response.get(todo_entity_id, {}).get("items", [])
                items = [{'summary': item['summary'], 'status': item['status']} for item in raw_items]
        except Exception as e: _LOGGER.error(f"Error fetching to-do items: {e}"); return
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_todo_list_url(hass, title, items, lang, orientation, small_screen)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending to-do list to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_TODO_LIST, "status": status})

    async def handle_send_rss_feed(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        feed_url, title, max_items = call.data["feed_url"], call.data["title"], call.data["max_items"]
        lang, small_screen = _get_lang(hass), call.data[ATTR_SMALL_SCREEN]
        def _parse_feed():
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo: _LOGGER.warning(f"Malformed RSS feed: {feed.bozo_exception}")
                return [{"title": entry.title} for entry in feed.entries[:max_items]]
            except Exception as e: _LOGGER.error(f"Error fetching RSS feed: {e}"); return []
        items = await hass.async_add_executor_job(_parse_feed)
        content_url = await create_rss_feed_url(hass, title, items, lang, small_screen)
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending RSS feed to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_RSS_FEED, "status": status})

    async def handle_send_status_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        title, entity_ids = call.data[ATTR_TITLE], call.data[ATTR_ENTITIES]
        lang, small_screen = _get_lang(hass), call.data[ATTR_SMALL_SCREEN]
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_status_panel_url(hass, title, entity_ids, lang, orientation, small_screen)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending status panel to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_STATUS_PANEL, "status": status})

    async def handle_set_display_rotation(call: ServiceCall):
        uuids, rotation = await get_uuids_from_call(call), call.data[ATTR_DISPLAY_ROTATION]
        for uuid_val in uuids:
            status = "failure"
            try:
                if await api.async_set_display_rotation(uuid_val, rotation) and await api.async_reboot_device(uuid_val):
                    status = "success"; _LOGGER.info(f"Display rotation for {uuid_val} changed to: {rotation}")
            except Exception as e: _LOGGER.error(f"Error changing rotation for {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status})
        await coordinator.async_request_refresh()
        
    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        status = "failure"
        try:
            if await api.async_restart_sessions_batch(uuids): status = "success"; _LOGGER.info(f"Session restart for {len(uuids)} devices requested.")
        except Exception as e: _LOGGER.error(f"Error restarting sessions: {e}")
        for uuid_val in uuids: hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_FORCE_REFRESH, "status": status})
            
    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        for uuid_val in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, blank_url): status = "success"; _LOGGER.info(f"Display for {uuid_val} cleared")
            except Exception as e: _LOGGER.error(f"Error clearing display for {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_CLEAR_DISPLAY, "status": status})
            
    async def handle_sleep_device(call: ServiceCall):
        uuids, duration = await get_uuids_from_call(call), call.data[ATTR_DURATION]
        sleep_url = f"data:text/html,<html><script>window.VECT = window.VECT || {{}}; window.VECT.setSleep({duration});</script></html>"
        for uuid_val in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, sleep_url): status = "success"; _LOGGER.info(f"Device {uuid_val} put to sleep for {duration}s")
            except Exception as e: _LOGGER.error(f"Error putting {uuid_val} to sleep: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SLEEP_DEVICE, "status": status})
            
    async def handle_wake_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        wake_url = "data:text/html,<html><script>window.VECT = window.VECT || {}; window.VECT.setSleep(0);</script></html>"
        for uuid_val in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, wake_url): status = "success"; _LOGGER.info(f"Device {uuid_val} has been woken up")
            except Exception as e: _LOGGER.error(f"Error waking up {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_WAKE_DEVICE, "status": status})
            
    async def handle_send_qr_code(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        try:
            content_url = create_qr_code_url(
                qr_data=call.data[ATTR_DATA], message=call.data[ATTR_MESSAGE],
                qr_message_text_size=call.data[ATTR_QR_MESSAGE_TEXT_SIZE], qr_message_position=call.data[ATTR_QR_MESSAGE_POSITION],
                box_size=call.data[ATTR_BOX_SIZE], border=call.data[ATTR_BORDER],
                fill_color=call.data[ATTR_FILL_COLOR], back_color=call.data[ATTR_BACK_COLOR]
            )
        except Exception as e: _LOGGER.error(f"Error generating QR code: {e}"); return
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data[ATTR_CLICK_ANYWHERE_TO_RETURN], call.data[ATTR_CLICK_ANYWHERE_TO_ACTION],
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"; _LOGGER.info(f"QR code sent to {device_uuid}")
            except Exception as e: _LOGGER.error(f"Error sending QR code to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_QR_CODE, "status": status})
            
    async def handle_send_calendar(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        calendar_entity_id, duration_days, style, small_screen = call.data[ATTR_CALENDAR_ENTITY], call.data[ATTR_DURATION_DAYS], call.data[ATTR_DISPLAY_STYLE], call.data[ATTR_SMALL_SCREEN]
        now, lang = dt_util.now(), _get_lang(hass)
        if style == "monthly_grid":
            start_date, end_date = now.replace(day=1, hour=0, minute=0, second=0), (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            start_date, end_date = now.replace(hour=0, minute=0, second=0), now.replace(hour=0, minute=0, second=0) + timedelta(days=duration_days)
        try:
            response_data = await hass.services.async_call("calendar", "get_events", {"entity_id": calendar_entity_id, "start_date_time": start_date.isoformat(), "end_date_time": end_date.isoformat()}, blocking=True, return_response=True)
            raw_events, events = response_data.get(calendar_entity_id, {}).get("events", []), []
            for event in raw_events:
                if not isinstance(event, dict): continue
                start_info, end_info, start_str, end_str = event.get('start'), event.get('end'), None, None
                if isinstance(start_info, dict): start_str = start_info.get('dateTime') or start_info.get('date')
                elif isinstance(start_info, str): start_str = start_info
                if isinstance(end_info, dict): end_str = end_info.get('dateTime') or end_info.get('date')
                elif isinstance(end_info, str): end_str = end_info
                if start_str: event['start'] = dt_util.parse_datetime(start_str)
                if end_str: event['end'] = dt_util.parse_datetime(end_str)
                if 'start' in event: events.append(event)
        except Exception as e: _LOGGER.error(f"Error fetching events: {e}"); return
        content_url = create_monthly_calendar_url(now.year, now.month, events, lang=lang, small_screen=small_screen) if style == "monthly_grid" else create_calendar_url(events, style, lang=lang)
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"; _LOGGER.info(f"Calendar sent to {device_uuid}")
            except Exception as e: _LOGGER.error(f"Error sending calendar to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CALENDAR, "status": status})

    async def handle_send_camera_snapshot(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        camera_entity_id, caption_template, image_zoom, image_rotation = call.data[ATTR_CAMERA_ENTITY], call.data.get(ATTR_CAPTION, ""), call.data.get(ATTR_IMAGE_ZOOM, 100), int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))
        if isinstance(caption_template, Template): caption_template.hass = hass; caption = caption_template.async_render(parse_result=False)
        else: caption = caption_template
        try: image = await async_get_image(hass, camera_entity_id)
        except Exception as e: _LOGGER.error(f"Failed to get image from camera {camera_entity_id}: {e}"); return
        www_dir = Path(hass.config.path("www")); await hass.async_add_executor_job(lambda: www_dir.mkdir(parents=True, exist_ok=True))
        image_path = www_dir / f"visionect_snapshot_{uuid.uuid4().hex}.jpg"
        await hass.async_add_executor_job(lambda: image_path.write_bytes(image.content)); await _async_cleanup_media_files(hass)
        image_url = create_simple_cache_buster(f"{get_url(hass)}/local/{image_path.name}")
        content_url = create_text_message_url(message=caption, layout="image_top", image_url=image_url, text_size="24px", image_zoom=image_zoom, image_rotation=image_rotation)
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error while sending snapshot to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CAMERA_SNAPSHOT, "status": status})
    
    async def handle_send_sensor_graph(call: ServiceCall):
        uuids, entity_ids, duration_hours, graph_type, show_points, image_zoom, image_rotation = await get_uuids_from_call(call), call.data[ATTR_ENTITIES], call.data[ATTR_DURATION_HOURS], call.data[ATTR_GRAPH_TYPE], call.data[ATTR_SHOW_POINTS], call.data[ATTR_IMAGE_ZOOM], int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))
        start_time = dt_util.now() - timedelta(hours=duration_hours)
        history_data = await get_instance(hass).async_add_executor_job(partial(history.get_significant_states, hass, start_time, entity_ids=entity_ids, significant_changes_only=False))
        www_dir = Path(hass.config.path("www")); await hass.async_add_executor_job(lambda: www_dir.mkdir(parents=True, exist_ok=True))
        for device_uuid in uuids:
            orientation, back_url = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0")), _get_back_url_for_uuid(device_uuid, call.data)
            try: image_bytes = await hass.async_add_executor_job(_generate_graph_image, hass, history_data, entity_ids, graph_type, show_points, orientation)
            except Exception as e: _LOGGER.error(f"Failed to generate graph image: {e}"); image_bytes = None
            if not image_bytes:
                lang, msg = _get_lang(hass), "Brak danych lub błąd." if _get_lang(hass) == "pl" else "No data or error."
                content_url = f"data:text/html,{urllib.parse.quote(f'<html><body style=\"display:flex;align-items:center;justify-content:center;height:100vh;font-size:2em;\">{msg}</body></html>')}"
                add_back = _effective_add_back_button(call.data, back_url)
                final_url = await _add_interactive_layer_to_url(
                    hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                    call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                    call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
                )
                status = "failure"
                try:
                    if await api.async_set_device_url(device_uuid, final_url): status = "success"
                except Exception as e: _LOGGER.error(f"Error sending message to {device_uuid}: {e}")
                hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_SENSOR_GRAPH, "status": status}); continue
            image_path = www_dir / f"visionect_graph_{uuid.uuid4().hex}.png"
            await hass.async_add_executor_job(lambda: image_path.write_bytes(image_bytes)); await _async_cleanup_media_files(hass)
            image_url = create_simple_cache_buster(f"{get_url(hass)}/local/{image_path.name}")
            content_url = create_text_message_url(message="", layout="image_only", image_url=image_url, image_zoom=image_zoom, image_rotation=image_rotation)
            add_back = _effective_add_back_button(call.data, back_url)
            final_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back, call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                call.data[ATTR_CLICK_ANYWHERE_TO_ACTION], call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID)
            )
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending graph to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_SENSOR_GRAPH, "status": status})

    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SERVICE_SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DISPLAY_ROTATION, handle_set_display_rotation, schema=SERVICE_SET_DISPLAY_ROTATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_FORCE_REFRESH, handle_force_refresh, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_DISPLAY, handle_clear_display, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SLEEP_DEVICE, handle_sleep_device, schema=SERVICE_SLEEP_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_WAKE_DEVICE, handle_wake_device, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_QR_CODE, handle_send_qr_code, schema=SERVICE_SEND_QR_CODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_CALENDAR, handle_send_calendar, schema=SERVICE_SEND_CALENDAR_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_WEATHER, handle_send_weather, schema=SERVICE_SEND_WEATHER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_ENERGY_PANEL, handle_send_energy_panel, schema=SERVICE_SEND_ENERGY_PANEL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TODO_LIST, handle_send_todo_list, schema=SERVICE_SEND_TODO_LIST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_CAMERA_SNAPSHOT, handle_send_camera_snapshot, schema=SERVICE_SEND_CAMERA_SNAPSHOT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_STATUS_PANEL, handle_send_status_panel, schema=SERVICE_SEND_STATUS_PANEL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_SENSOR_GRAPH, handle_send_sensor_graph, schema=SERVICE_SEND_SENSOR_GRAPH_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_RSS_FEED, handle_send_rss_feed, schema=SERVICE_SEND_RSS_FEED_SCHEMA)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Visionect Joan config entry successfully initialized.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Visionect Joan integration.")
    services_to_remove = [
        SERVICE_SET_URL, SERVICE_SEND_TEXT, SERVICE_SET_DISPLAY_ROTATION, SERVICE_FORCE_REFRESH,
        SERVICE_CLEAR_DISPLAY, SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE,
        SERVICE_SEND_CALENDAR, SERVICE_SEND_WEATHER, SERVICE_SEND_ENERGY_PANEL, SERVICE_SEND_TODO_LIST,
        SERVICE_SEND_CAMERA_SNAPSHOT, SERVICE_SEND_STATUS_PANEL, SERVICE_SEND_SENSOR_GRAPH,
        SERVICE_SEND_RSS_FEED,
    ]
    for service in services_to_remove:
        hass.services.async_remove(DOMAIN, service)
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Visionect Joan integration successfully unloaded.")
    else:
        _LOGGER.error("Error while unloading Visionect Joan integration.")
    return unload_ok