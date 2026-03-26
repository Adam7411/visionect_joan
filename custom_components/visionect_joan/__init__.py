import logging
import urllib.parse
import voluptuous as vol
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import uuid
import hashlib
from functools import partial
import asyncio
import feedparser
import json
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID, EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from homeassistant.components.camera import async_get_image
from homeassistant.components.persistent_notification import async_create as async_create_persistent_notification
from homeassistant.helpers.network import get_url
from homeassistant.components.recorder import history, get_instance
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.helpers.network import get_internal_url
except ImportError:
    get_internal_url = None

from .api import VisionectAPI
from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY,
    SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE, EVENT_COMMAND_RESULT,
    NETWORK_RETRY_DELAY, ATTR_PREDEFINED_URL,
    CONF_VIEWS, CONF_MAIN_MENU_URL, CONF_CLEANUP_MAX_AGE, CONF_CLEANUP_INTERVAL,
    SERVICE_SEND_KEYPAD, SUPPORTED_IMAGE_FORMATS, SERVICE_SEND_BUTTON_PANEL,
    CONF_TABLET_LANGUAGE, API_TCLV_PARAM
)
from .html_generator import (
    create_status_panel_url, create_text_message_url, create_todo_list_url,
    create_rss_feed_url, create_energy_panel_url, create_qr_code_url,
    create_calendar_url, create_monthly_calendar_url, create_weather_url,
    create_weather_calendar_url,
    create_simple_cache_buster, _generate_graph_image,
    _add_interactive_layer_to_url, _get_lang, create_keypad_url,
    create_button_panel_url,
    create_crypto_panel_url, create_exchange_rates_url, async_get_icon_as_base64,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "text", "button", "select", "camera"]
URL_LENGTH_LIMIT = 4096
CACHE_DIR_NAME = "visionect_cache"

def _parse_views(views_data) -> list[dict]:
    if isinstance(views_data, list): return views_data
    if isinstance(views_data, str):
        views = []
        for line in views_data.strip().splitlines():
            if ":" in line:
                n, u = line.split(":", 1)
                views.append({"name": n.strip(), "url": u.strip()})
        return views
    return []

# Constants for attributes
ATTR_ADD_BACK_BUTTON = "add_back_button"
ATTR_CLICK_ANYWHERE_TO_RETURN = "click_anywhere_to_return"
ATTR_CLICK_ANYWHERE_TO_ACTION = "click_anywhere_to_action"
ATTR_BACK_BUTTON_URL = "back_button_url"
ATTR_ACTION_WEBHOOK_ID = "action_webhook_id"
ATTR_ACTION_WEBHOOK_2_ID = "action_webhook_2_id"
ATTR_SMALL_SCREEN = "small_screen_optimized"  # backwards compat alias
ATTR_SCREEN_SIZE = "screen_size"
ATTR_AUTO_RETURN_SECONDS = "auto_return_seconds"

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
ATTR_ENERGY_THEME = "theme"
ATTR_COINS = "coins"
ATTR_VS_CURRENCY = "vs_currency"
ATTR_BASE_CURRENCY = "base_currency"
ATTR_CURRENCIES = "currencies"
ATTR_HISTORY_HOURS = "history_hours"
ATTR_HISTORY_DAYS = "history_days"
ATTR_SHOW_HEADER = "show_header"

# CoinGecko symbol → ID map (common coins; user can also pass IDs directly)
CRYPTO_SYMBOL_MAP = {
    "BTC": "bitcoin",       "ETH": "ethereum",       "BNB": "binancecoin",
    "SOL": "solana",        "ADA": "cardano",         "XRP": "ripple",
    "DOT": "polkadot",      "DOGE": "dogecoin",       "AVAX": "avalanche-2",
    "MATIC": "matic-network","LINK": "chainlink",     "LTC": "litecoin",
    "UNI": "uniswap",       "ATOM": "cosmos",         "NEAR": "near",
    "TRX": "tron",          "SHIB": "shiba-inu",      "XLM": "stellar",
    "BCH": "bitcoin-cash",  "ETC": "ethereum-classic","APT": "aptos",
    "OP": "optimism",       "ARB": "arbitrum",        "FTM": "fantom",
    "USDT": "tether",       "USDC": "usd-coin",       "TON": "the-open-network",
    "ICP": "internet-computer", "INJ": "injective-protocol", "RNDR": "render-token",
    "PEPE": "pepe",         "WIF": "dogwifcoin",      "BONK": "bonk",
    "FET": "fetch-ai",      "TIA": "celestia",        "KAS": "kaspa",
    "LDO": "lido-dao",      "AR": "arweave",          "FIL": "filecoin",
    "STX": "stacks",        "XMR": "monero",          "VET": "vechain",
}

# Services
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
SERVICE_CLEAR_WEB_CACHE = "clear_web_cache"
SERVICE_START_SLIDESHOW = "start_slideshow"
SERVICE_SEND_IMAGE_URL = "send_image_url"
SERVICE_SET_SESSION_OPTIONS = "set_session_options"
SERVICE_SEND_CRYPTO = "send_crypto"

EINK_COLORS = ["black", "white"]
FONT_WEIGHTS = ["normal", "bold"]
LAYOUT_OPTIONS = ["text_only", "image_top", "image_bottom", "image_left", "image_right", "image_only"]

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

INTERACTIVE_SCHEMA_EXTENSION = {
    vol.Optional(ATTR_ADD_BACK_BUTTON, default=False): cv.boolean,
    vol.Optional(ATTR_CLICK_ANYWHERE_TO_RETURN, default=False): cv.boolean,
    vol.Optional(ATTR_CLICK_ANYWHERE_TO_ACTION, default=False): cv.boolean,
    vol.Optional(ATTR_BACK_BUTTON_URL): cv.string,
    vol.Optional(ATTR_ACTION_WEBHOOK_ID): cv.string,
    vol.Optional(ATTR_ACTION_WEBHOOK_2_ID): cv.string,
    vol.Optional(ATTR_SCREEN_SIZE, default="joan6"): vol.In(["joan6", "joan13"]),
    vol.Optional(ATTR_AUTO_RETURN_SECONDS, default=0): vol.Coerce(int),
}

SERVICE_DEVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
})

SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
    vol.Optional(ATTR_URL): cv.string,
    vol.Optional(ATTR_PREDEFINED_URL): cv.string,
})

SERVICE_SEND_TEXT_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
    vol.Required(ATTR_MESSAGE): cv.template,
    vol.Optional(ATTR_TEXT_COLOR, default="black"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_BACKGROUND_COLOR, default="white"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_TEXT_SIZE, default=28): vol.All(vol.Coerce(int), vol.Range(min=10, max=150)),
    vol.Optional(ATTR_TEXT_ALIGN, default="center"): vol.In(["left", "center", "right"]),
    vol.Optional(ATTR_FONT_FAMILY, default="Modern"): vol.In(list(THEMED_FONTS.keys())),
    vol.Optional(ATTR_FONT_WEIGHT, default="normal"): vol.In(FONT_WEIGHTS),
    vol.Optional(ATTR_LAYOUT, default="text_only"): vol.In(LAYOUT_OPTIONS),
    vol.Optional(ATTR_IMAGE_URL): cv.string,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SET_DISPLAY_ROTATION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string]),
    vol.Required(ATTR_DISPLAY_ROTATION): vol.In(list(DISPLAY_ROTATIONS.keys())),
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
    vol.Required(ATTR_CALENDAR_ENTITY): vol.Any(cv.entity_id, cv.entity_ids),
    vol.Optional(ATTR_DURATION_DAYS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
    vol.Optional(ATTR_DISPLAY_STYLE, default="modern"): vol.In(["modern", "minimalist", "monthly_grid", "weather_calendar"]),
    vol.Optional(ATTR_WEATHER_ENTITY): cv.entity_id,
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
    vol.Optional(ATTR_ENERGY_THEME, default="classic"): vol.In(["classic", "eink_donut"]),
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
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
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
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_RSS_FEED_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required("feed_url"): cv.url,
    vol.Optional("title", default="News"): cv.string,
    vol.Optional("max_items", default=5): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_CLEAR_WEB_CACHE_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional("restart_session", default=False): cv.boolean,
})

SERVICE_START_SLIDESHOW_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required("views"): vol.Any([cv.string], cv.string),
    vol.Optional("seconds_per_slide", default=30): vol.All(vol.Coerce(int), vol.Range(min=3, max=3600)),
    vol.Optional("loop", default=True): cv.boolean,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SEND_IMAGE_URL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_IMAGE_URL): cv.string,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
    vol.Optional(ATTR_DISPLAY_ROTATION, default="0"): vol.In(["0", "90", "180", "270"]),
    **INTERACTIVE_SCHEMA_EXTENSION,
})

SERVICE_SET_SESSION_OPTIONS_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional("encoding"): cv.string,
    vol.Optional("dithering"): cv.string,
})

SERVICE_SEND_KEYPAD_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_TITLE, default="Enter PIN"): cv.string,
    vol.Required(ATTR_ACTION_WEBHOOK_ID): cv.string,
})

BUTTON_PANEL_SCHEMA_DICT = {
    vol.Optional("title"): vol.Any(None, cv.string),
    **INTERACTIVE_SCHEMA_EXTENSION,
}
for i in range(1, 13):
    BUTTON_PANEL_SCHEMA_DICT[vol.Optional(f"button_{i}_webhook_id")] = cv.string
    BUTTON_PANEL_SCHEMA_DICT[vol.Optional(f"button_{i}_name")] = cv.string
    BUTTON_PANEL_SCHEMA_DICT[vol.Optional(f"button_{i}_icon")] = cv.string

SERVICE_SEND_BUTTON_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend(BUTTON_PANEL_SCHEMA_DICT)

SERVICE_SEND_CRYPTO_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_COINS): [cv.string],  # CoinGecko IDs or common symbols: ["bitcoin","ETH"]
    vol.Optional(ATTR_VS_CURRENCY, default="usd"): cv.string,  # e.g. usd, eur, pln
    vol.Optional(ATTR_HISTORY_HOURS, default=24): vol.All(vol.Coerce(int), vol.Range(min=0, max=168)),
    vol.Optional(ATTR_SHOW_HEADER, default=True): cv.boolean,
    **INTERACTIVE_SCHEMA_EXTENSION,
})

def _schedule_media_cleanup(hass: HomeAssistant) -> None:
    interval_h = max(1, int(hass.data[DOMAIN]["cleanup_interval_hours"]))
    async def _periodic_cleanup(now=None):
        await _async_cleanup_media_files(hass)
    hass.async_create_task(_periodic_cleanup())
    async_track_time_interval(hass, _periodic_cleanup, timedelta(hours=interval_h))

async def _async_cleanup_media_files(hass: HomeAssistant) -> None:
    MEDIA_PREFIXES = ("visionect_snapshot_", "visionect_graph_")
    max_age_h = max(1, int(hass.data[DOMAIN]["cleanup_max_age_hours"]))
    cutoff = dt_util.utcnow() - timedelta(hours=max_age_h)
    
    paths_to_clean = [Path(hass.config.path("www"))]
    cache_path = Path(hass.config.path(f"www/{CACHE_DIR_NAME}"))
    if cache_path.exists():
        paths_to_clean.append(cache_path)

    def _cleanup():
        removed = 0
        for directory in paths_to_clean:
            if not directory.exists():
                continue
            for p in directory.iterdir():
                if not p.is_file():
                    continue
                if directory.name == "www" and not p.name.startswith(MEDIA_PREFIXES):
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
    if isinstance(removed, int) and removed > 0:
        _LOGGER.info("Visionect cleanup: removed %s old media/cache files.", removed)

async def _process_final_url(hass: HomeAssistant, url: str) -> str:
    if len(url) <= URL_LENGTH_LIMIT and not url.startswith("data:text/html,"):
        return url
    
    if not url.startswith("data:text/html,"):
        return url
        
    try:
        encoded_content = url[len("data:text/html,"):]
        html_content = urllib.parse.unquote(encoded_content)
        content_hash = hashlib.md5(html_content.encode("utf-8")).hexdigest()
        filename = f"{content_hash}.html"
        www_path = Path(hass.config.path("www"))
        cache_dir = www_path / CACHE_DIR_NAME
        
        def _write_file():
            cache_dir.mkdir(parents=True, exist_ok=True)
            file_path = cache_dir / filename
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
        
        await hass.async_add_executor_job(_write_file)
        
        try:
            base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception:
            base_url = get_url(hass)
            
        final_file_url = f"{base_url}/local/{CACHE_DIR_NAME}/{filename}"
        return create_simple_cache_buster(final_file_url)
    except Exception as e:
        _LOGGER.error("Failed to save HTML to file: %s", e)
        return url

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config: hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Starting setup of Visionect Joan config entry.")
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    yaml_config = hass.data[DOMAIN].get("yaml_config", {})
    views_data_from_options = entry.options.get(CONF_VIEWS, [])
    views = _parse_views(views_data_from_options)
    if not views:
        views = yaml_config.get("views", [])

    main_menu = entry.options.get(CONF_MAIN_MENU_URL, yaml_config.get("main_menu_url"))
    cleanup_age = entry.options.get(CONF_CLEANUP_MAX_AGE, yaml_config.get("cleanup_max_age_hours", 24))
    cleanup_interval = entry.options.get(CONF_CLEANUP_INTERVAL, yaml_config.get("cleanup_interval_hours", 6))



    hass.data[DOMAIN]["views"] = views
    hass.data[DOMAIN]["main_menu_url"] = main_menu
    hass.data[DOMAIN]["cleanup_max_age_hours"] = cleanup_age
    hass.data[DOMAIN]["cleanup_interval_hours"] = cleanup_interval
    hass.data[DOMAIN]["tablet_language"] = entry.options.get(CONF_TABLET_LANGUAGE, "auto")

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

    guard_state = hass.data[DOMAIN].setdefault("guard_state", {
        "low_battery_notified": set(),
        "low_battery_tablet_alerted": set(),
        "offline_notified": set(),
        "last_seen": {},
        "low_battery_prev_url": {},
    })

    async def async_update_data():
        try:
            # Pobierz listę wszystkich urządzeń
            devices_summary = await api.async_get_all_devices()
            if not devices_summary:
                return {}
            
            # Pobierz listę orphans (problematycznych sesji)
            orphans = await api.async_get_orphans()
            
            data = {}
            for device_entry in devices_summary:
                if isinstance(device_entry, str):
                    uuid_val = str(device_entry).strip().rstrip("/")
                    device_details = await api.async_get_device_data(uuid_val)
                else:
                    uuid_val = str(device_entry.get("Uuid", "")).strip().rstrip("/")
                    device_details = device_entry

                if not uuid_val or not device_details: continue

                # ALWAYS fetch the full device data to merge it with SessionOptions
                device_details = await api.async_get_device_data(uuid_val)
                if not device_details: continue

                # Dodaj informację o orphan status
                if uuid_val in orphans:
                     device_details["OrphanError"] = orphans[uuid_val]
                else:
                     device_details["OrphanError"] = None

                # Status urządzenia - dokumentacja Visionect definiuje tylko: online/offline
                state_val = device_details.get("State", "").lower()
                is_online = state_val == "online"
                
                now_utc = datetime.now(timezone.utc)
                if is_online:
                    guard_state["last_seen"][uuid_val] = now_utc
                    if uuid_val in guard_state["offline_notified"]:
                        guard_state["offline_notified"].discard(uuid_val)
                elif uuid_val not in guard_state["last_seen"]:
                    # Inicjalizacja czasu "od startu HA", jeśli tablet nie był online
                    guard_state["last_seen"][uuid_val] = now_utc

                device_name = device_details.get("Options", {}).get("Name") or f"Device {uuid_val}"

                # Strażnik Baterii (< 10%)
                try:
                    battery = device_details.get("Status", {}).get("Battery")
                    if battery is not None:
                        batt_val = float(battery)
                        charger_raw = str(device_details.get("Status", {}).get("Charger", "")).strip().lower()
                        is_charging = charger_raw in {"1", "true", "yes", "on", "charging"}

                        # Soft threshold for HA notification
                        battery_notify_threshold = 10.0
                        # Critical threshold for tablet overlay
                        battery_tablet_threshold = 6.0
                        # Hysteresis to clear tablet alert and restore previous content
                        battery_tablet_clear_threshold = 8.0

                        if batt_val <= battery_notify_threshold:
                            if uuid_val not in guard_state["low_battery_notified"]:
                                _LOGGER.info(f"Battery guard triggered for {device_name} (<=10%)")
                                guard_state["low_battery_notified"].add(uuid_val)
                                try:
                                    notif_lang = hass.data[DOMAIN].get("tablet_language", "auto")
                                    if notif_lang == "auto":
                                        notif_lang = (getattr(getattr(hass, "config", None), "language", "en") or "en").lower()
                                    is_pl = str(notif_lang).startswith("pl")

                                    notif_msg = (
                                        f"Bateria w urządzeniu **{device_name}** spadła do {batt_val:.0f}%. "
                                        "Proszę podłącz je do ładowania."
                                        if is_pl
                                        else f"Battery on **{device_name}** dropped to {batt_val:.0f}%. "
                                        "Please connect charger."
                                    )
                                    notif_title = (
                                        "Niski stan baterii (Visionect)"
                                        if is_pl
                                        else "Low Battery (Visionect)"
                                    )
                                    async_create_persistent_notification(
                                        hass,
                                        notif_msg,
                                        title=notif_title,
                                        notification_id=f"visionect_battery_{uuid_val}",
                                    )
                                except Exception as notify_err:
                                    _LOGGER.debug(
                                        "Could not create low-battery persistent notification for %s: %s",
                                        device_name,
                                        notify_err,
                                    )

                        # Critical tablet warning screen with icon
                        if batt_val <= battery_tablet_threshold:
                            if uuid_val not in guard_state["low_battery_tablet_alerted"]:
                                prev_url = str(device_details.get("Config", {}).get("Url", "")).strip()
                                if prev_url:
                                    guard_state["low_battery_prev_url"][uuid_val] = prev_url

                                notif_lang = hass.data[DOMAIN].get("tablet_language", "auto")
                                if notif_lang == "auto":
                                    notif_lang = (getattr(getattr(hass, "config", None), "language", "en") or "en").lower()
                                is_pl = str(notif_lang).startswith("pl")

                                if is_pl:
                                    low_batt_msg = (
                                        "NISKI POZIOM BATERII\n\n"
                                        f"{device_name}\n"
                                        f"Bateria: {batt_val:.0f}%\n\n"
                                        "Podłącz ładowarkę."
                                    )
                                else:
                                    low_batt_msg = (
                                        "LOW BATTERY\n\n"
                                        f"{device_name}\n"
                                        f"Battery: {batt_val:.0f}%\n\n"
                                        "Please connect charger."
                                    )

                                battery_icon_url = await async_get_icon_as_base64(hass, "battery.svg")
                                low_batt_url = create_text_message_url(
                                    message=low_batt_msg,
                                    text_color="black",
                                    background_color="white",
                                    text_size="44px",
                                    text_align="center",
                                    font_family_key="Readable",
                                    font_weight="bold",
                                    layout="image_top",
                                    image_url=battery_icon_url,
                                    image_zoom=50,
                                    screen_size="joan6",
                                )
                                final_low_batt_url = await _process_final_url(hass, low_batt_url)
                                await api.async_set_device_url(uuid_val, final_low_batt_url)
                                guard_state["low_battery_tablet_alerted"].add(uuid_val)
                        elif batt_val >= battery_tablet_clear_threshold or is_charging:
                            if uuid_val in guard_state["low_battery_tablet_alerted"]:
                                guard_state["low_battery_tablet_alerted"].discard(uuid_val)
                                prev_url = guard_state["low_battery_prev_url"].pop(uuid_val, None)
                                if prev_url:
                                    await api.async_set_device_url(uuid_val, prev_url)

                        if batt_val >= 20.0 or is_charging:
                            if uuid_val in guard_state["low_battery_notified"]:
                                guard_state["low_battery_notified"].discard(uuid_val)
                except (ValueError, TypeError):
                    pass

                # Strażnik Połączenia (> 4h offline)
                offline_duration = now_utc - guard_state["last_seen"][uuid_val]
                if offline_duration > timedelta(hours=4):
                    if uuid_val not in guard_state["offline_notified"]:
                        _LOGGER.info(f"Connection guard triggered for {device_name} (>4h offline)")
                        guard_state["offline_notified"].add(uuid_val)
                        try:
                            async_create_persistent_notification(
                                hass,
                                f"Tablet **{device_name}** nie połączył się od ponad 4 godzin. Sprawdź, czy nie rozładowała się bateria lub czy nie stracił zasięgu Wi-Fi.",
                                title="Utrata połączenia (Visionect)",
                                notification_id=f"visionect_offline_{uuid_val}",
                            )
                        except Exception as notify_err:
                            _LOGGER.debug(
                                "Could not create offline persistent notification for %s: %s",
                                device_name,
                                notify_err,
                            )
                
                # VSS sam zarządza urządzeniami przez DeviceStatePolling - nie wysyłaj niepotrzebnych TCLV
                # które mogą zakłócać pracę e-ink i zużywać baterię
                
                final_data = device_details
                if "Config" not in final_data: final_data["Config"] = {}
                if device_name and device_name.lower() not in UNKNOWN_STRINGS:
                    final_data["Config"]["Name"] = device_name
                final_data["Options"] = device_details.get("Options", {})
                final_data["LastUpdated"] = now_utc
                data[uuid_val] = final_data
            return data
        except Exception as e:
            _LOGGER.error(f"Error during data update: {e}")
            raise UpdateFailed(f"Connection to VSS failed: {e}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"visionect_{entry.entry_id}",
        update_method=async_update_data, update_interval=SCAN_INTERVAL
    )
    coordinator.config_entry = entry
    # POPRAWKA: Przypisujemy API do koordynatora, aby encje (np. Button) miały do niego dostęp
    coordinator.api = api
    
    await coordinator.async_config_entry_first_refresh()

    # WATCHDOG: Continuously monitors VSS health and forces a session restart when VSS comes back online.
    # This acts as a robust recovery mechanism after HA hard restarts (which take 3-7 minutes) or Addon restarts.
    async def _async_vss_watchdog():
        """Watches VSS API and handles auto-restarts when VSS recovers."""
        # Initialize as True so that the very first successful connection triggers a recovery restart.
        vss_was_offline = True
        
        while True:
            try:
                # Sprawdzamy co 15 sekund
                await asyncio.sleep(15)
                
                is_healthy = await api.async_check_health()
                
                if is_healthy and vss_was_offline:
                    _LOGGER.info("VSS Watchdog: VSS is online! Fetching devices for recovery restart...")
                    vss_was_offline = False
                    
                    devices = await api.async_get_all_devices()
                    if devices:
                        uuids = []
                        for device_entry in devices:
                            if isinstance(device_entry, str):
                                uuids.append(str(device_entry).strip().rstrip("/"))
                            else:
                                uuid_val = str(device_entry.get("Uuid", "")).strip().rstrip("/")
                                state_val = str(device_entry.get("State", "")).strip().lower()
                                # Restart session only for online devices.
                                # Offline devices often have no active session and trigger noisy 500s.
                                if uuid_val and state_val == "online":
                                    uuids.append(uuid_val)
                        
                        if uuids:
                            _LOGGER.info(f"VSS Watchdog: Found {len(uuids)} devices. Waiting 30s for VSS WebKit to warm up...")
                            await asyncio.sleep(30)
                            
                            for u in uuids:
                                await api.async_set_session_options(u, encoding="4")
                            await asyncio.sleep(2)
                            await api.async_restart_sessions_batch(uuids)
                            _LOGGER.info(f"VSS Watchdog: Sessions restarted for {len(uuids)} devices after VSS recovery.")
                            
                            # Force a coordinator refresh to ensure Home Assistant gets the latest data immediately
                            await coordinator.async_request_refresh()
                
                elif not is_healthy:
                    if not vss_was_offline:
                        _LOGGER.warning("VSS Watchdog: VSS went offline. Waiting for recovery...")
                    vss_was_offline = True
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                if not vss_was_offline:
                    _LOGGER.warning(f"VSS Watchdog connection error: {e}")
                vss_was_offline = True

    entry.async_create_background_task(hass, _async_vss_watchdog(), "visionect_vss_watchdog")

    store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_prefs.json")
    prefs = await store.async_load() or {"back_targets": {}}

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "prefs_store": store,
        "prefs": prefs,
        "views": views,
        "main_menu_url": main_menu,
        "tablet_language": entry.options.get(CONF_TABLET_LANGUAGE, "auto"),
    }

    device_reg = dr.async_get(hass)

    def _get_url_from_predefined(predefined_name: str | None) -> str | None:
        if not predefined_name: return None
        candidate = str(predefined_name).strip()
        if candidate.startswith(("http", "data:")): return candidate
        for view in views or []:
            if str(view.get("name", "")).strip().lower() == candidate.lower():
                return view.get("url")
        return None

    def _get_url_from_params(call_data: dict, url_key: str, predefined_key: str) -> str | None:
        direct_url = call_data.get(url_key)
        if direct_url:
            direct_url = str(direct_url).strip()
            if direct_url.startswith(("http", "data:")): return direct_url
            resolved = _get_url_from_predefined(direct_url)
            if resolved: return resolved
        return _get_url_from_predefined(call_data.get(predefined_key))

    def _get_prefs() -> dict:
        return hass.data[DOMAIN][entry.entry_id].setdefault("prefs", {"back_targets": {}})

    def _get_back_url_for_uuid(device_uuid: str, call_data: dict) -> str | None:
        back_url = call_data.get(ATTR_BACK_BUTTON_URL)
        if back_url:
            if not back_url.startswith(("http", "data:")):
                resolved = _get_url_from_predefined(back_url)
                if resolved: return resolved
            return back_url
        prefs_local = _get_prefs()
        stored_url = prefs_local.get("back_targets", {}).get(device_uuid)
        if stored_url: return stored_url
        return main_menu

    def _effective_add_back_button(call: ServiceCall, back_url: str | None) -> bool:
        cd = call.data
        if cd.get(ATTR_CLICK_ANYWHERE_TO_RETURN) or cd.get(ATTR_CLICK_ANYWHERE_TO_ACTION): return False
        if cd.get(ATTR_ADD_BACK_BUTTON): return True
        if cd.get(ATTR_BACK_BUTTON_URL): return True
        if call.service == SERVICE_SEND_KEYPAD and cd.get(ATTR_ADD_BACK_BUTTON) and back_url: return True
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
        return uuids_list

    async def handle_set_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        original_url = _get_url_from_params(call.data, ATTR_URL, ATTR_PREDEFINED_URL)
        if not original_url:
            _LOGGER.error("No URL provided for set_url.")
            return
        
        final_url = await _process_final_url(hass, original_url)
        if not final_url.startswith("data:text/html,"):
            final_url = create_simple_cache_buster(final_url)
            
        tasks = [api.async_set_device_url(uuid, final_url) for uuid in uuids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, uuid_val in enumerate(uuids):
            status = "success" if results[i] is True else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_URL, "status": status})
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        if isinstance(message_template, Template): message_template.hass = hass
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        
        img_url = call.data.get(ATTR_IMAGE_URL)
        if img_url and not api.validate_image_url(img_url):
            _LOGGER.warning(f"Invalid image URL provided for text message: {img_url}")
            img_url = None
            
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        
        content_url = create_text_message_url(
            message,
            call.data.get(ATTR_TEXT_COLOR, "black"),
            call.data.get(ATTR_BACKGROUND_COLOR, "white"),
            f"{call.data.get(ATTR_TEXT_SIZE, 28)}px",
            call.data.get(ATTR_TEXT_ALIGN, "center"),
            call.data.get(ATTR_FONT_FAMILY, "Modern"),
            call.data.get(ATTR_FONT_WEIGHT, "normal"),
            call.data.get(ATTR_LAYOUT, "text_only"),
            img_url,
            call.data.get(ATTR_IMAGE_ZOOM, 100),
            0, # image_rotation
            screen_size
        )
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_TEXT, "status": status})

    async def handle_send_weather(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        weather_entity_id = call.data[ATTR_WEATHER_ENTITY]
        layout = call.data[ATTR_LAYOUT]
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, call.data.get(ATTR_SMALL_SCREEN) and "joan6" or "joan6")
        for device_uuid in uuids:
            device_data = coordinator.data.get(device_uuid, {})
            orientation = str(device_data.get("Config", {}).get("DisplayRotation", "0"))
            weather_state = hass.states.get(weather_entity_id)
            if not weather_state: continue
            
            daily_forecast, hourly_forecast = None, None
            try:
                dr = await hass.services.async_call("weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "daily"}, blocking=True, return_response=True)
                if dr: daily_forecast = dr.get(weather_entity_id, {}).get("forecast", [])
            except Exception: pass
            
            try:
                hr = await hass.services.async_call("weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "hourly"}, blocking=True, return_response=True)
                if hr: hourly_forecast = hr.get(weather_entity_id, {}).get("forecast", [])
            except Exception: pass

            content_url = await create_weather_url(hass, weather_state, daily_forecast, hourly_forecast, layout, orientation, lang, screen_size)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_WEATHER, "status": status})

    async def handle_send_energy_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_states = {key: hass.states.get(entity_id) for key, entity_id in call.data.items() if key.endswith("_entity") and entity_id}
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        energy_theme = call.data.get(ATTR_ENERGY_THEME, "classic")
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_energy_panel_url(hass, entity_states, orientation, lang, screen_size, theme=energy_theme)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_ENERGY_PANEL, "status": status})

    async def handle_send_todo_list(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        todo_entity_id, title = call.data[ATTR_TODO_ENTITY], call.data.get(ATTR_TITLE)
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        if not title:
            st = hass.states.get(todo_entity_id)
            title = st.name if st else "To-Do List"
        items = []
        try:
            resp = await hass.services.async_call("todo", "get_items", {"entity_id": todo_entity_id}, blocking=True, return_response=True)
            if resp:
                raw = resp.get(todo_entity_id, {}).get("items", [])
                items = [{'summary': i.get('summary'), 'status': i.get('status'), 'uid': i.get('uid')} for i in raw]
        except Exception: pass
        
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_todo_list_url(hass, title, items, lang, orientation, screen_size)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_TODO_LIST, "status": status})

    async def handle_send_rss_feed(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        feed_url, title, max_items = call.data["feed_url"], call.data.get("title", "News"), call.data.get("max_items", 5)
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        
        def _parse():
            try:
                f = feedparser.parse(feed_url)
                return [{"title": e.title} for e in f.entries[:max_items]]
            except Exception: return []
            
        items = await hass.async_add_executor_job(_parse)
        content_url = await create_rss_feed_url(hass, title, items, lang, screen_size)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_RSS_FEED, "status": status})

    async def handle_send_status_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        title, entity_ids = call.data.get(ATTR_TITLE, "Status Panel"), call.data[ATTR_ENTITIES]
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        
        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_status_panel_url(hass, title, entity_ids, lang, orientation, screen_size)
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_STATUS_PANEL, "status": status})

    async def handle_set_display_rotation(call: ServiceCall):
        uuids, rotation = await get_uuids_from_call(call), call.data[ATTR_DISPLAY_ROTATION]
        for uuid_val in uuids:
            status = "failure"
            if await api.async_set_display_rotation(uuid_val, rotation) and await api.async_reboot_device(uuid_val):
                status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status})
        await coordinator.async_request_refresh()

    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        status = "failure"
        if await api.async_restart_sessions_batch(uuids): status = "success"
        for uuid_val in uuids:
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_FORCE_REFRESH, "status": status})

    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        for uuid_val in uuids:
            status = "success" if await api.async_set_device_url(uuid_val, blank_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_CLEAR_DISPLAY, "status": status})

    async def handle_sleep_device(call: ServiceCall):
        uuids, duration = await get_uuids_from_call(call), call.data[ATTR_DURATION]
        sleep_url = f"data:text/html,<html><script>window.VECT = window.VECT || {{}}; window.VECT.setSleep({duration});</script></html>"
        for uuid_val in uuids:
            status = "success" if await api.async_set_device_url(uuid_val, sleep_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SLEEP_DEVICE, "status": status})

    async def handle_wake_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        wake_url = "data:text/html,<html><script>window.VECT = window.VECT || {}; window.VECT.setSleep(0);</script></html>"
        for uuid_val in uuids:
            status = "success" if await api.async_set_device_url(uuid_val, wake_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_WAKE_DEVICE, "status": status})

    async def handle_send_qr_code(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        try:
            content_url = create_qr_code_url(
                qr_data=call.data[ATTR_DATA], message=call.data.get(ATTR_MESSAGE, ""),
                qr_message_text_size=call.data.get(ATTR_QR_MESSAGE_TEXT_SIZE, 24), qr_message_position=call.data.get(ATTR_QR_MESSAGE_POSITION, "below"),
                box_size=call.data.get(ATTR_BOX_SIZE, 10), border=call.data.get(ATTR_BORDER, 4),
                fill_color=call.data.get(ATTR_FILL_COLOR, "black"), back_color=call.data.get(ATTR_BACK_COLOR, "white"),
                screen_size=screen_size
            )
        except Exception: return
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_QR_CODE, "status": status})

    async def handle_send_calendar(call: ServiceCall):
        """Handle send_calendar service with multi-calendar support."""
        uuids = await get_uuids_from_call(call)
        
        # ✅ ZMIANA: Pobierz calendar_entity (może być string lub lista)
        calendar_entity_raw = call.data.get(ATTR_CALENDAR_ENTITY)
        
        # Normalizuj do listy
        if isinstance(calendar_entity_raw, str):
            calendar_entities = [calendar_entity_raw]
        elif isinstance(calendar_entity_raw, list):
            calendar_entities = calendar_entity_raw
        else:
            _LOGGER.error("calendar_entity must be a string or list")
            return
        
        duration_days = call.data.get(ATTR_DURATION_DAYS, 1)
        display_style = call.data.get(ATTR_DISPLAY_STYLE, "modern")
        screen_size = call.data.get(ATTR_SCREEN_SIZE, call.data.get(ATTR_SMALL_SCREEN) and "joan6" or "joan6")
        
        # ✅ ZMIANA: Zbierz eventy z WSZYSTKICH kalendarzy RÓWNOLEGLE dla szybkości
        async def fetch_calendar_events(cal_entity):
            try:
                start = datetime.now(timezone.utc)
                end = start + timedelta(days=duration_days)
                
                events_response = await hass.services.async_call(
                    "calendar", "get_events",
                    {"entity_id": cal_entity, "start_date_time": start.isoformat(), "end_date_time": end.isoformat()},
                    blocking=True, return_response=True,
                )
                
                raw_events = events_response.get(cal_entity, {}).get("events", [])
                
                def normalize_to_aware_dt(val):
                    if val is None: return None
                    dt_out = None
                    if isinstance(val, dict):
                        s = val.get('dateTime') or val.get('date')
                        if s:
                            try: dt_out = dt_util.parse_datetime(s)
                            except: pass
                            if dt_out is None:
                                try: 
                                    d = dt_util.parse_date(s)
                                    if d: dt_out = datetime.combine(d, datetime.min.time())
                                except: pass
                    elif isinstance(val, datetime):
                        dt_out = val
                    elif isinstance(val, date):
                        dt_out = datetime.combine(val, datetime.min.time())
                    elif isinstance(val, str):
                        try: dt_out = dt_util.parse_datetime(val)
                        except: pass
                        if dt_out is None:
                            try: 
                                d = dt_util.parse_date(val)
                                if d: dt_out = datetime.combine(d, datetime.min.time())
                            except: pass
                    if dt_out:
                        if dt_out.tzinfo is None:
                            dt_out = dt_out.replace(tzinfo=timezone.utc)
                        return dt_out
                    return None

                parsed_events = []
                for event in raw_events:
                    if not isinstance(event, dict): continue
                    event['start'] = normalize_to_aware_dt(event.get('start'))
                    event['end'] = normalize_to_aware_dt(event.get('end'))
                    if event['start'] is not None:
                        parsed_events.append(event)
                _LOGGER.debug(f"Fetched {len(parsed_events)} events from {cal_entity}")
                return parsed_events
            except Exception as e:
                _LOGGER.error(f"Failed to fetch events from {cal_entity}: {e}")
                return []

        results = await asyncio.gather(*(fetch_calendar_events(cal) for cal in calendar_entities))
        
        all_events = []
        for event_list in results:
            all_events.extend(event_list)
        
        # ✅ ZMIANA: Sortuj wszystkie eventy po czasie
        def get_event_start(event):
            """Extract start datetime from event for sorting."""
            start_val = event.get("start")
            if isinstance(start_val, datetime):
                # Jeśli datetime nie ma timezone, dodaj UTC
                if start_val.tzinfo is None:
                    return start_val.replace(tzinfo=timezone.utc)
                return start_val
            return datetime.min.replace(tzinfo=timezone.utc)
        
        all_events.sort(key=get_event_start)
        
        # ✅ ZMIANA: Selektywne limity wydarzeń
        # Modern: 6 (default)
        if display_style == "modern":
            all_events = all_events[:6]
        # Minimalist: Wyświetlaj więcej (np. miesięczny widok), limit bezpieczeństwa 50
        elif display_style == "minimalist":
            all_events = all_events[:50]
        # Dla weather_calendar limit ustawiany jest niżej w wywołaniu create_weather_calendar_url (max_events=5)
        # Dla monthly_grid pokazujemy wszystko (bez slice)
        
        _LOGGER.info(f"Total merged events: {len(all_events)} for style {display_style} from {len(calendar_entities)} calendars")
        
        # RESZTA BEZ ZMIAN - generuj URL normalnie
        lang = _get_lang(hass)
        
        daily_forecast = None
        
        if display_style == "monthly_grid":
            today = datetime.now()
            year = today.year
            month = today.month
            
            content_url = create_monthly_calendar_url(
                year, month, all_events, lang=lang, screen_size=screen_size
            )
        elif display_style == "weather_calendar":
            # ✅ NOWA FUNKCJONALNOŚĆ: Kalendarz z pogodą
            weather_entity_id = call.data.get(ATTR_WEATHER_ENTITY)
            if not weather_entity_id:
                _LOGGER.warning("weather_calendar style requires weather_entity parameter, falling back to 'modern'")
                content_url = create_calendar_url(all_events, style="modern", lang=lang, screen_size=screen_size)
            else:
                # Pobierz prognozę pogody przez service call (raz dla wszystkich)
                daily_forecast = []
                try:
                    dr = await hass.services.async_call(
                        "weather", "get_forecasts", 
                        {"entity_id": weather_entity_id, "type": "daily"}, 
                        blocking=True, return_response=True
                    )
                    if dr and weather_entity_id in dr:
                        auths = dr[weather_entity_id].get("forecast", [])
                        daily_forecast = [f for f in auths if f.get("is_daytime", True)][:5]
                    else:
                        _LOGGER.warning(f"No forecast data for {weather_entity_id}")
                except Exception as e:
                    _LOGGER.warning(f"Failed to get weather forecast: {e}")
                
                # Content URL generated dynamically inside loop
                content_url = None 
        else:
            content_url = create_calendar_url(all_events, style=display_style, lang=lang, screen_size=screen_size)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            
            # Dla weather calendar generujemy URL dynamicznie per urządzenie
            current_content_url = content_url
            if display_style == "weather_calendar": 
                if daily_forecast is not None:
                    max_events = 5
                    current_content_url = await create_weather_calendar_url(
                        hass, all_events, weather_entity_id, lang=lang, 
                        screen_size=screen_size, daily_forecast=daily_forecast,
                        add_back_button=add_back, max_events=max_events
                    )
                else: 
                     # Fallback lub brak forecast - używamy content_url który powinien być ustawiony w fallbacku
                     pass
            
            if current_content_url is None:
                 # Safety fallback
                 current_content_url = create_calendar_url(all_events, style="modern", lang=lang, screen_size=screen_size)

            interactive_url = await _add_interactive_layer_to_url(
                hass, current_content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CALENDAR, "status": status})

    async def handle_send_camera_snapshot(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        camera_entity_id = call.data[ATTR_CAMERA_ENTITY]
        caption_template = call.data.get(ATTR_CAPTION, "")
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))

        if isinstance(caption_template, Template):
            caption_template.hass = hass
            caption = caption_template.async_render(parse_result=False)
        else:
            caption = caption_template

        try:
            image = await async_get_image(hass, camera_entity_id)
        except Exception: return

        www_dir = Path(hass.config.path("www"))
        await hass.async_add_executor_job(lambda: www_dir.mkdir(parents=True, exist_ok=True))
        image_path = www_dir / f"visionect_snapshot_{uuid.uuid4().hex}.jpg"
        await hass.async_add_executor_job(lambda: image_path.write_bytes(image.content))
        await _async_cleanup_media_files(hass)

        try:
            base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception: base_url = get_url(hass)
        image_url = create_simple_cache_buster(f"{base_url}/local/{image_path.name}")

        content_url = create_text_message_url(message=caption, layout="image_top", image_url=image_url, text_size="24px", image_zoom=image_zoom, image_rotation=image_rotation)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CAMERA_SNAPSHOT, "status": status})

    async def handle_send_sensor_graph(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_ids = call.data[ATTR_ENTITIES]
        duration_hours = call.data.get(ATTR_DURATION_HOURS, 24)
        graph_type = call.data.get(ATTR_GRAPH_TYPE, "line")
        show_points = call.data.get(ATTR_SHOW_POINTS, False)
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))
        start_time = dt_util.now() - timedelta(hours=duration_hours)


        history_data = await get_instance(hass).async_add_executor_job(
            partial(
                history.get_significant_states, 
                hass, 
                start_time, 
                entity_ids=entity_ids, 
                significant_changes_only=False, 
                include_start_time_state=True
            )
        )
        
        www_dir = Path(hass.config.path("www"))
        await hass.async_add_executor_job(lambda: www_dir.mkdir(parents=True, exist_ok=True))

        for device_uuid in uuids:
            orientation = str(coordinator.data.get(device_uuid, {}).get("Config", {}).get("DisplayRotation", "0"))
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            try:
                image_bytes = await hass.async_add_executor_job(_generate_graph_image, hass, history_data, entity_ids, graph_type, show_points, orientation)
            except Exception as e:
                _LOGGER.error(f"Graph generation exception: {e}")
                image_bytes = None

            if not image_bytes:
                # Debugging info
                data_points_count = sum(len(states) for states in history_data.values()) if history_data else 0
                _LOGGER.warning(f"Graph generation returned no data. Entity IDs: {entity_ids}, Data points found: {data_points_count}. Check if entities have numeric states.")
                content_url = f"data:text/html,{urllib.parse.quote('<html><body style=\"display:flex;align-items:center;justify-content:center;height:100vh;font-size:2em;\">No Data (Check Logs)</body></html>')}"
            else:
                image_path = www_dir / f"visionect_graph_{uuid.uuid4().hex}.png"
                await hass.async_add_executor_job(lambda: image_path.write_bytes(image_bytes))
                await _async_cleanup_media_files(hass)
                try: base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
                except Exception: base_url = get_url(hass)
                image_url = create_simple_cache_buster(f"{base_url}/local/{image_path.name}")
                content_url = create_text_message_url(message="", layout="image_only", image_url=image_url, image_zoom=image_zoom, image_rotation=image_rotation)

            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_SENSOR_GRAPH, "status": status})

    async def handle_clear_web_cache(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        restart = bool(call.data.get("restart_session", False))
        status = "failure"
        if await api.async_clear_webkit_cache(uuids):
            status = "success"
            if restart: await api.async_restart_sessions_batch(uuids)
        for uuid_val in uuids:
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_CLEAR_WEB_CACHE, "status": status})

    async def handle_send_image_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        image_url = call.data[ATTR_IMAGE_URL]
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))

        if not api.validate_image_url(image_url):
            _LOGGER.error(f"Unsupported image extension: {image_url}")
            return

        content_url = create_text_message_url(message="", layout="image_only", image_url=image_url, image_zoom=image_zoom, image_rotation=image_rotation)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_IMAGE_URL, "status": status})

    async def handle_start_slideshow(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        raw_views = call.data.get("views")
        seconds = int(call.data.get("seconds_per_slide", 30))
        loop = bool(call.data.get("loop", True))

        views_list = []
        if isinstance(raw_views, str):
            for line in raw_views.strip().splitlines():
                if line.strip(): views_list.append(line.strip())
        elif isinstance(raw_views, list):
            views_list = raw_views
        
        def _resolve_views_to_urls(items):
            out = []
            for it in items:
                if it.startswith(("http", "data:")): out.append(it)
                else:
                    resolved = _get_url_from_predefined(it)
                    if resolved: out.append(resolved)
            return out

        resolved_urls = _resolve_views_to_urls(views_list)
        processed_urls = []
        for u in resolved_urls:
            p = await _process_final_url(hass, u)
            processed_urls.append(p)
            
        def _build_slideshow_data_url(urls, sec, lp):
            processed = [create_simple_cache_buster(u) if not u.startswith("data:") else u for u in urls]
            js_urls = json.dumps(processed)
            loop_js = "true" if lp else "false"
            html_doc = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>html,body{{margin:0;height:100%;background:#fff}}#frame{{border:0;width:100%;height:100%;}}</style></head><body><iframe id="frame" referrerpolicy="no-referrer"></iframe><script>(function(){{var urls={js_urls};var idx=0;var loop={loop_js};var sec={int(sec)};function setSrc(){{try{{document.getElementById('frame').src=urls[idx];}}catch(e){{}}}}function next(){{idx++;if(idx>=urls.length){{if(loop)idx=0;else return;}}setSrc();}}setSrc();setInterval(next,Math.max(1,sec)*1000);}})();</script></body></html>"""
            return f"data:text/html,{urllib.parse.quote(html_doc, safe='')}"

        content_url = _build_slideshow_data_url(processed_urls, seconds, loop)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_START_SLIDESHOW, "status": status})

    async def handle_set_session_options(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        encoding = call.data.get("encoding")
        dithering = call.data.get("dithering")
        for uuid_val in uuids:
            status = "success" if await api.async_set_session_options(uuid_val, encoding=encoding, dithering=dithering) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_SESSION_OPTIONS, "status": status})

    async def handle_send_keypad(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        title = call.data[ATTR_TITLE]
        webhook_id = call.data[ATTR_ACTION_WEBHOOK_ID]
        
        try: base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception: base_url = get_url(hass)
        webhook_url = f"{base_url.rstrip('/')}/api/webhook/{webhook_id}"
        
        content_url = await create_keypad_url(hass, title, webhook_url)
        
        for device_uuid in uuids:
            interactive_url = await _add_interactive_layer_to_url(hass, content_url, None, False, False, False, None, None, call.data.get(ATTR_AUTO_RETURN_SECONDS, 0))
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_KEYPAD, "status": status})

    async def handle_send_crypto(call: ServiceCall):
        """Fetch crypto prices from CryptoCompare API (free, no key) and display on Joan."""
        uuids = await get_uuids_from_call(call)
        coins_input = call.data.get(ATTR_COINS, [])
        vs_currency = str(call.data.get(ATTR_VS_CURRENCY, "usd")).upper().strip()
        history_hours = call.data.get(ATTR_HISTORY_HOURS, 24)
        lang = _get_lang(hass)
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")
        show_header = call.data.get(ATTR_SHOW_HEADER, True)

        # Reverse map for CryptoCompare (e.g. "bitcoin" -> "BTC")
        comp_map = {v: k for k, v in CRYPTO_SYMBOL_MAP.items()}
        
        def _to_symbol(s: str) -> str:
            s_clean = s.strip().lower()
            return comp_map.get(s_clean, s.strip().upper())

        symbols = [_to_symbol(c) for c in coins_input]
        session = async_get_clientsession(hass)

        # --- Fetch current prices + 24h change ---
        price_data = {}
        try:
            syms_param = ",".join(symbols)
            price_url = (
                f"https://min-api.cryptocompare.com/data/pricemultifull"
                f"?fsyms={syms_param}&tsyms={vs_currency}"
            )
            async with session.get(price_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data_json = await resp.json()
                    price_data = data_json.get("RAW", {})
                else:
                    _LOGGER.warning("send_crypto: CryptoCompare returned HTTP %s", resp.status)
        except Exception as exc:
            _LOGGER.error("send_crypto: price fetch failed: %s", exc)

        coins_out = []
        for orig_input, sym in zip(coins_input, symbols):
            data = price_data.get(sym, {}).get(vs_currency, {})
            price = data.get("PRICE")
            change = data.get("CHANGEPCT24HOUR")
            high_24h = data.get("HIGHDAY")
            low_24h = data.get("LOWDAY")

            display_name = orig_input.title() if orig_input.lower() == orig_input else orig_input
            if sym in CRYPTO_SYMBOL_MAP:
                display_name = CRYPTO_SYMBOL_MAP[sym].replace("-", " ").title()

            # --- Fetch sparkline history ---
            hist_vals = []
            if history_hours > 0 and price is not None:
                try:
                    limit = max(1, history_hours)
                    hist_url = (
                        f"https://min-api.cryptocompare.com/data/v2/histohour"
                        f"?fsym={sym}&tsym={vs_currency}&limit={limit}"
                    )
                    async with session.get(hist_url, timeout=aiohttp.ClientTimeout(total=15)) as hr:
                        if hr.status == 200:
                            hist_json = await hr.json()
                            raw_data = hist_json.get("Data", {}).get("Data", [])
                            raw = [float(item.get("close")) for item in raw_data if item.get("close") is not None]
                            if len(raw) > 20:
                                step = max(1, len(raw) // 20)
                                raw = raw[::step][:20]
                            hist_vals = raw
                except Exception:
                    pass  # sparkline is optional

            coins_out.append({
                "name": display_name,
                "symbol": sym,
                "price": price,
                "change_pct": change,
                "history": hist_vals,
                "unit": vs_currency.upper(),
                "high_24h": high_24h,
                "low_24h": low_24h,
            })

        if not coins_out:
            _LOGGER.warning("send_crypto: no data from CryptoCompare.")
            return

        history_label = f"{history_hours}h" if history_hours > 0 else ""
        content_url = await create_crypto_panel_url(hass, coins_out, screen_size, lang, show_header, history_label)

        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CRYPTO, "status": status})



    async def handle_send_button_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        raw_title = call.data.get("title")
        title = raw_title.strip() if isinstance(raw_title, str) else ""
        screen_size = call.data.get(ATTR_SCREEN_SIZE, "joan6")

        try: base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception: base_url = get_url(hass)
        
        def _get_wh(wid): return f"{base_url.rstrip('/')}/api/webhook/{wid}"

        buttons = []
        for i in range(1, 13):
            wid = call.data.get(f"button_{i}_webhook_id")
            if wid:
                buttons.append({
                    "webhook_url": _get_wh(wid),
                    "name": call.data.get(f"button_{i}_name", ""),
                    "icon": call.data.get(f"button_{i}_icon", ""),
                    "sub_name": ""
                })
        
        if not buttons:
            _LOGGER.error("send_button_panel: No valid buttons.")
            return

        content_url = await create_button_panel_url(hass, title, buttons, screen_size)
        
        for device_uuid in uuids:
            back_url = _get_back_url_for_uuid(device_uuid, call.data)
            add_back = _effective_add_back_button(call, back_url)
            interactive_url = await _add_interactive_layer_to_url(
                hass, content_url, back_url, add_back,
                call.data.get(ATTR_CLICK_ANYWHERE_TO_RETURN),
                call.data.get(ATTR_CLICK_ANYWHERE_TO_ACTION),
                call.data.get(ATTR_ACTION_WEBHOOK_ID),
                call.data.get(ATTR_ACTION_WEBHOOK_2_ID),
                call.data.get(ATTR_AUTO_RETURN_SECONDS, 0)
            )
            final_url = await _process_final_url(hass, interactive_url)
            status = "success" if await api.async_set_device_url(device_uuid, final_url) else "failure"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_BUTTON_PANEL, "status": status})

    # Register services
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
    hass.services.async_register(DOMAIN, SERVICE_SEND_KEYPAD, handle_send_keypad, schema=SERVICE_SEND_KEYPAD_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_WEB_CACHE, handle_clear_web_cache, schema=SERVICE_CLEAR_WEB_CACHE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_START_SLIDESHOW, handle_start_slideshow, schema=SERVICE_START_SLIDESHOW_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE_URL, handle_send_image_url, schema=SERVICE_SEND_IMAGE_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_SESSION_OPTIONS, handle_set_session_options, schema=SERVICE_SET_SESSION_OPTIONS_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_BUTTON_PANEL, handle_send_button_panel, schema=SERVICE_SEND_BUTTON_PANEL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_CRYPTO, handle_send_crypto, schema=SERVICE_SEND_CRYPTO_SCHEMA)


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Visionect Joan config entry successfully initialized.")



    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Visionect Joan integration.")
    services_to_remove = [
        SERVICE_SET_URL, SERVICE_SEND_TEXT, SERVICE_SET_DISPLAY_ROTATION, SERVICE_FORCE_REFRESH,
        SERVICE_CLEAR_DISPLAY, SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE,
        SERVICE_SEND_CALENDAR, SERVICE_SEND_WEATHER, SERVICE_SEND_ENERGY_PANEL, SERVICE_SEND_TODO_LIST,
        SERVICE_SEND_CAMERA_SNAPSHOT, SERVICE_SEND_STATUS_PANEL, SERVICE_SEND_SENSOR_GRAPH,
        SERVICE_SEND_RSS_FEED, SERVICE_CLEAR_WEB_CACHE, SERVICE_START_SLIDESHOW, SERVICE_SEND_IMAGE_URL,
        SERVICE_SET_SESSION_OPTIONS, SERVICE_SEND_KEYPAD, SERVICE_SEND_BUTTON_PANEL,
        SERVICE_SEND_CRYPTO,
    ]
    for service in services_to_remove:
        hass.services.async_remove(DOMAIN, service)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Visionect Joan integration successfully unloaded.")
    else:
        _LOGGER.error("Error while unloading Visionect Joan integration.")

    return unload_ok
