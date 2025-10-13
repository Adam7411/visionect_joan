import logging
import time
import urllib.parse
import voluptuous as vol
import html
import re
from datetime import datetime, timezone, timedelta, date
import io
import base64
import qrcode
import calendar
from pathlib import Path
import uuid
from functools import partial
import asyncio

# --- NOWE IMPORTY DLA WYKRESU POGODY ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cycler import cycler
# --- KONIEC NOWYCH IMPORTÓW ---

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, State, ServiceResponse, SupportsResponse
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID, UnitOfPower, UnitOfEnergy
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

from .api import VisionectAPI
from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY,
    SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE, EVENT_COMMAND_RESULT,
    NETWORK_RETRY_DELAY
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "text", "button", "select", "camera"]

# --- NOWE I ZAKTUALIZOWANE ATRYBUTY ---
ATTR_ADD_BACK_BUTTON = "add_back_button"
ATTR_CLICK_ANYWHERE_TO_RETURN = "click_anywhere_to_return"
ATTR_BACK_BUTTON_URL = "back_button_url"
ATTR_ACTION_WEBHOOK_ID = "action_webhook_id"
ATTR_SMALL_SCREEN = "small_screen_optimized"

VIEW_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Required("url"): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional("views", default=[]): vol.All(cv.ensure_list, [VIEW_SCHEMA]),
        vol.Optional("main_menu_url"): cv.url,
        vol.Optional("cleanup_max_age_hours", default=24): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
        vol.Optional("cleanup_interval_hours", default=6): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
    })
}, extra=vol.ALLOW_EXTRA)

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
    vol.Optional(ATTR_BACK_BUTTON_URL): cv.string,
    vol.Optional(ATTR_ACTION_WEBHOOK_ID): cv.string,
    vol.Optional(ATTR_SMALL_SCREEN, default=False): cv.boolean,
}

SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_URL): cv.string,
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

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        hass.data[DOMAIN]["views"] = config[DOMAIN].get("views", [])
        hass.data[DOMAIN]["main_menu_url"] = config[DOMAIN].get("main_menu_url")
        hass.data[DOMAIN]["cleanup_max_age_hours"] = config[DOMAIN].get("cleanup_max_age_hours", 24)
        hass.data[DOMAIN]["cleanup_interval_hours"] = config[DOMAIN].get("cleanup_interval_hours", 6)
    else:
        hass.data[DOMAIN]["views"] = []
        hass.data[DOMAIN]["main_menu_url"] = None
        hass.data[DOMAIN]["cleanup_max_age_hours"] = 24
        hass.data[DOMAIN]["cleanup_interval_hours"] = 6

    _schedule_media_cleanup(hass)
    return True

MEDIA_PREFIXES = ("visionect_snapshot_", "visionect_graph_")

def _schedule_media_cleanup(hass: HomeAssistant) -> None:
    interval_h = max(1, int(hass.data[DOMAIN]["cleanup_interval_hours"]))
    async def _periodic_cleanup(now=None):
        await _async_cleanup_media_files(hass)
    hass.async_create_task(_periodic_cleanup())
    async_track_time_interval(hass, _periodic_cleanup, timedelta(hours=interval_h))

async def _async_cleanup_media_files(hass: HomeAssistant) -> None:
    max_age_h = max(1, int(hass.data[DOMAIN]["cleanup_max_age_hours"]))
    cutoff = dt_util.utcnow() - timedelta(hours=max_age_h)
    www_path = Path(hass.config.path("www"))
    if not www_path.exists():
        return
    def _cleanup():
        removed = 0
        for p in www_path.iterdir():
            if not p.is_file():
                continue
            if not p.name.startswith(MEDIA_PREFIXES):
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

def _add_interactive_layer_to_url(
    hass: HomeAssistant,
    data_url: str,
    back_url: str,
    add_back_button: bool,
    click_anywhere: bool,
    action_webhook_id: str | None = None,
) -> str:
    """Decode a data:text/html URL, inject buttons/actions, and encode it back."""
    if not (add_back_button or click_anywhere or action_webhook_id):
        return data_url

    try:
        header, encoded_html = data_url.split(",", 1)
        decoded_html = urllib.parse.unquote(encoded_html)

        if not re.search(r"<html\b", decoded_html, re.IGNORECASE):
            decoded_html = f"<!DOCTYPE html><html><head></head><body>{decoded_html}</body></html>"
        if not re.search(r"<head\b", decoded_html, re.IGNORECASE):
            decoded_html = re.sub(r"(<html\b[^>]*>)", r"\1<head></head>", decoded_html, count=1, flags=re.IGNORECASE)
        if not re.search(r"<body\b", decoded_html, re.IGNORECASE):
            decoded_html = re.sub(r"(</head>)", r"\1<body>", decoded_html, count=1, flags=re.IGNORECASE) + "</body>"

        # Inject a style block to add padding for the buttons if they exist.
        common_css = """
        html { box-sizing: border-box; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; padding-top: 100px !important; }
        .visionect-interactive-button {
            position: absolute;
            top: 20px;
            width: 30%;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 12px 10px;
            background-color: #f2f2f2;
            color: #000;
            border: 3px solid #000;
            border-radius: 2px;
            text-decoration: none;
            font-size: 22px;
            font-weight: 700;
            line-height: 1;
            z-index: 1000;
            cursor: pointer;
            white-space: nowrap;
        }
        .visionect-interactive-button:active { opacity: 0.6; }
        .visionect-back-button { left: 15%; }
        .visionect-action-button { right: 15%; }
        """

        if re.search(r"</style>", decoded_html, re.IGNORECASE):
            decoded_html = re.sub(r"</style>", common_css + "</style>", decoded_html, count=1, flags=re.IGNORECASE)
        else:
            decoded_html = re.sub(r"</head>", f"<style>{common_css}</style></head>", decoded_html, count=1, flags=re.IGNORECASE)

        if add_back_button and back_url:
            button_html = f'<a href="{back_url}" class="visionect-interactive-button visionect-back-button" onclick="event.stopPropagation();">&#x2190; Back</a>'
            decoded_html = re.sub(r"(<body\b[^>]*>)", r"\1" + button_html, decoded_html, count=1, flags=re.IGNORECASE)
            
        if action_webhook_id:
            internal_base_url = "http://homeassistant:8123"
            webhook_url = f"{internal_base_url}/api/webhook/{action_webhook_id}"
            actions_html = f'<div class="visionect-interactive-button visionect-action-button" onclick="triggerWebhook(event, \'{webhook_url}\')">Actions &#x2714;</div>'
            decoded_html = re.sub(r"(<body\b[^>]*>)", r"\1" + actions_html, decoded_html, count=1, flags=re.IGNORECASE)

        interactive_scripts = ""
        if action_webhook_id:
            interactive_scripts += """
            function triggerWebhook(event, url) {
                event.stopPropagation();
                try {
                    fetch(url, { method: 'POST', body: '{}' })
                        .catch(err => console.error('Webhook failed:', err));
                } catch(e) { console.error('Error in fetch:', e); }
            }
            """
        
        if click_anywhere and back_url:
            interactive_scripts += f"""
            (function() {{
                function goBack() {{ try {{ window.location.href = "{back_url}"; }} catch(e) {{}} }}
                document.addEventListener('DOMContentLoaded', function() {{ document.body.addEventListener('click', goBack, {{ capture: false }}); }});
            }})();
            """

        if interactive_scripts:
            script_html = f"<script>{interactive_scripts}</script>"
            decoded_html = re.sub(r"</body>", script_html + "</body>", decoded_html, count=1, flags=re.IGNORECASE)

        return f"{header},{urllib.parse.quote(decoded_html, safe='')}"
    except Exception as e:
        _LOGGER.error(f"Failed to add interactive layer to URL: {e}")
        return data_url

ICON_CACHE = {}

async def _get_icon_filename_for_entity(state: State) -> str:
    device_class = state.attributes.get("device_class")
    domain = state.domain
    entity_id = state.entity_id.lower()
    is_on_state = state.state in ["on", "open", "unlocked", "armed", "armed_away", "armed_home", "playing"]
    if device_class == "door": return "door-open.svg" if is_on_state else "door-closed.svg"
    if device_class == "window": return "window-open.svg" if is_on_state else "window-closed.svg"
    if device_class == "lock": return "lock-open.svg" if is_on_state else "lock.svg"
    if device_class == "cover" or "roleta" in entity_id or "blinds" in entity_id: return "blinds-open.svg" if is_on_state else "blinds-closed.svg"
    if domain == "light": return "light-on.svg" if is_on_state else "light-off.svg"
    if domain == "alarm_control_panel": return "shield-check.svg" if is_on_state else "shield-off.svg"
    if device_class == "motion": return "motion-sensor.svg"
    if device_class == "smoke" or device_class == "gas": return "smoke-detector.svg"
    if device_class == "moisture": return "water-alert.svg"
    if device_class == "humidity": return "humidity.svg"
    if device_class == "temperature": return "temperature.svg"
    if device_class == "energy": return "energy.svg"
    if device_class in ["power", "switch", "plug"]: return "power-plug.svg"
    if device_class == "timestamp": return "clock.svg"
    if domain == "person" or domain == "device_tracker": return "account.svg"
    if domain == "camera": return "camera.svg"
    if domain == "weather": return "weather.svg"
    if domain == "media_player": return "speaker.svg"
    if domain == "update": return "update.svg"
    if "drzwi" in entity_id: return "door-open.svg" if is_on_state else "door-closed.svg"
    if "okno" in entity_id: return "window-open.svg" if is_on_state else "window-closed.svg"
    if "brama" in entity_id: return "gate.svg"
    if "ruch" in entity_id: return "motion-sensor.svg"
    if "swiatlo" in entity_id or "lampa" in entity_id or "led" in entity_id: return "light-on.svg" if is_on_state else "light-off.svg"
    if "zamek" in entity_id: return "lock-open.svg" if is_on_state else "lock.svg"
    if "wilgotnosc" in entity_id: return "humidity.svg"
    if "temperatury" in entity_id: return "temperature.svg"
    if "energia" in entity_id or "energy" in entity_id or "fazy" in entity_id: return "energy.svg"
    if "licznik" in entity_id: return "counter.svg"
    if "gniazdko" in entity_id: return "power-plug.svg"
    if "alarm" in entity_id: return "shield-check.svg" if is_on_state else "shield-off.svg"
    if "czas" in entity_id or "time" in entity_id: return "clock.svg"
    if "kamera" in entity_id: return "camera.svg"
    if "glosnik" in entity_id or "speaker" in entity_id or "radio" in entity_id: return "speaker.svg"
    if "tv" in entity_id or "telewizor" in entity_id: return "television.svg"
    if "pralka" in entity_id or "washing" in entity_id: return "washing-machine.svg"
    if "suszarka" in entity_id or "dryer" in entity_id: return "tumble-dryer.svg"
    if "zmywarka" in entity_id or "dishwasher" in entity_id: return "dishwasher.svg"
    if "piec" in entity_id or "kociol" in entity_id or "boiler" in entity_id: return "fire-circle.svg"
    if "zawor" in entity_id or "valve" in entity_id: return "valve.svg"
    if "pompa" in entity_id or "pump" in entity_id: return "pump.svg"
    if "hydrofor" in entity_id or "woda" in entity_id: return "water-pump.svg"
    if "gaz" in entity_id: return "fire-circle.svg"
    if "klima" in entity_id or "ac" in entity_id: return "air-conditioner.svg"
    if "wentylator" in entity_id or "fan" in entity_id: return "fan.svg"
    if "rekuperator" in entity_id: return "air-filter.svg"
    if "grzejnik" in entity_id or "radiator" in entity_id: return "radiator.svg"
    if "wifi" in entity_id: return "wifi.svg"
    if "zigbee" in entity_id: return "zigbee.svg"
    if "ip" in entity_id and "adres" in entity_id: return "ip-network-outline.svg"
    if domain == "sensor": return "gauge.svg"
    return "default.svg"

async def async_get_icon_as_base64(hass: HomeAssistant, icon_name: str) -> str:
    if icon_name in ICON_CACHE: return ICON_CACHE[icon_name]
    icon_file = Path(__file__).parent / "svg" / icon_name
    if not icon_file.is_file():
        _LOGGER.warning(f"Icon file not found: {icon_file}, using default.")
        default_icon_file = Path(__file__).parent / "svg" / "default.svg"
        if not default_icon_file.is_file():
            _LOGGER.error("Even the default icon (default.svg) is missing!")
            return ""
        icon_file = default_icon_file
    def _load_icon():
        try:
            with open(icon_file, "rb") as f: encoded_string = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/svg+xml;base64,{encoded_string}"
        except Exception as e:
            _LOGGER.error(f"Error encoding icon {icon_name}: {e}")
            return ""
    data_url = await hass.async_add_executor_job(_load_icon)
    if data_url: ICON_CACHE[icon_name] = data_url
    return data_url

def _get_lang(hass: HomeAssistant) -> str:
    try:
        lang = (hass.config.language or "en").lower()
        return "pl" if lang.startswith("pl") else "en"
    except Exception:
        return "en"

_PL_DAY_NAMES = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
_EN_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_PL_DAY_ABBR = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
_EN_DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_PL_MONTH_NAMES = ["styczeń","luty","marzec","kwiecień","maj","czerwiec","lipiec","sierpień","wrzesień","październik","listopad","grudzień"]
_EN_MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def _format_long_date(d: date, lang: str) -> str:
    if lang == "pl":
        return f"{_PL_DAY_NAMES[d.weekday()]}, {d.day} {_PL_MONTH_NAMES[d.month-1]}"
    return f"{_EN_DAY_NAMES[d.weekday()]}, {d.day} {_EN_MONTH_NAMES[d.month-1]}"

async def create_status_panel_url(hass: HomeAssistant, title: str, entity_ids: list[str], lang: str, orientation: str, small_screen: bool) -> str:
    STATE_TRANSLATIONS_PL = { "on": "Włączone", "off": "Wyłączone", "open": "Otwarte", "closed": "Zamknięte", "home": "w Domu", "not_home": "Poza domem", "locked": "Zamknięte", "unlocked": "Otwarte", "unavailable": "Niedostępny", "unknown": "Nieznany", }
    STATE_TRANSLATIONS_EN = { "on": "On", "off": "Off", "open": "Open", "closed": "Closed", "home": "Home", "not_home": "Away", "locked": "Locked", "unlocked": "Unlocked", "unavailable": "Unavailable", "unknown": "Unknown", }
    translations = STATE_TRANSLATIONS_PL if lang == "pl" else STATE_TRANSLATIONS_EN
    
    header_fs = "2.4em" if small_screen else "2.8em"
    grid_fs = "1.6em" if small_screen else "1.8em"
    
    style_css = f""" body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: white; color: black; margin: 0; padding: 30px; box-sizing: border-box; }} .header {{ text-align: center; font-size: {header_fs}; font-weight: bold; border-bottom: 3px solid black; padding-bottom: 20px; margin-bottom: 25px; }} .grid {{ display: grid; grid-template-columns: auto 1fr auto; gap: 20px 15px; align-items: center; font-size: {grid_fs}; }} .icon {{ width: 1.5em; height: 1.5em; }} .name {{ text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }} .state {{ text-align: right; font-weight: bold; }} .state-active {{ color: #d32f2f; }} """
    items_html = ""
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if not state: continue
        name = state.attributes.get('friendly_name', entity_id)
        icon_filename = await _get_icon_filename_for_entity(state)
        icon_data_url = await async_get_icon_as_base64(hass, icon_filename)
        display_state_val = state.state
        display_state_val = translations.get(display_state_val.lower(), display_state_val)
        unit = state.attributes.get('unit_of_measurement', '')
        if unit: display_state_val = f"{state.state} {unit}"
        state_class = "state-active" if state.state in ["on", "open", "unlocked", "problem", "detected", "arming", "armed", "armed_away", "armed_home"] else ""
        items_html += f""" <img src="{icon_data_url}" class="icon" /> <div class="name">{html.escape(name)}</div> <div class="state {state_class}">{html.escape(display_state_val)}</div> """
    html_body = f""" <div class="header">{html.escape(title)}</div> <div class="grid">{items_html}</div> """
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style_css}</style></head><body>{html_body}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_text_message_url(message: str, text_color: str = "black", background_color: str = "white", text_size: str = "28px", text_align: str = "center", font_family_key: str = "Modern", font_weight: str = "normal", layout: str = "text_only", image_url: str = None, image_zoom: int = 100, image_rotation: int = 0) -> str:
    font_family_css = THEMED_FONTS.get(font_family_key, "'Trebuchet MS', sans-serif")
    font_import_rule = f"@import url('{GOOGLE_FONTS_IMPORT_URL}');"
    escaped_message = html.escape(message).replace('\n', '<br>')
    style_css, body_html = "", ""

    scale_factor = image_zoom / 100.0
    transform_style = f"transform: scale({scale_factor}) rotate({image_rotation}deg);"
    
    if layout == "image_only":
        style_css = f"""
            body {{ margin: 0; padding: 20px; width: 100vw; height: 100vh; background-color: {background_color}; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }}
            img {{ max-width: 100%; max-height: 100%; object-fit: contain; {transform_style} }}
        """
        body_html = f'<img src="{image_url}" />'
    else:
        image_html = f'<div class="image-container"><img src="{image_url}" style="{transform_style}" /></div>' if layout != "text_only" and image_url else ""
        flex_direction = "column"
        if layout == "image_bottom": flex_direction = "column-reverse"
        elif layout == "image_left": flex_direction = "row"
        elif layout == "image_right": flex_direction = "row-reverse"
        
        style_css = f"""
            {font_import_rule}
            body {{ font-family: {font_family_css}; color: {text_color}; background-color: {background_color}; margin: 0; padding: 20px; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; text-align: {text_align}; box-sizing: border-box; -webkit-font-smoothing: none; font-smooth: never; }}
            .container {{ display: flex; flex-direction: {flex_direction}; align-items: center; justify-content: center; width: 100%; height: 100%; gap: 20px; }}
            .text-container {{ font-size: {text_size}; font-weight: {font_weight}; line-height: 1.5; word-wrap: break-word; flex-shrink: 1; }}
            .image-container {{ flex-shrink: 0; max-width: {'40%' if layout in ['image_left', 'image_right'] else '90%'}; max-height: {'90%' if layout in ['image_left', 'image_right'] else '80%'}; display: flex; align-items: center; justify-content: center;}}
            img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
            .timestamp {{ position: absolute; bottom: 10px; right: 10px; font-size: 16px; opacity: 0.8; font-family: 'Courier New', Courier, monospace; font-weight: 700; }}
        """
        body_html = f"""
            <div class="container">
                {image_html}
                <div class="text-container">{escaped_message}</div>
            </div>
            <div class="timestamp">{time.strftime("%Y-%m-%d %H:%M")}</div>
        """

    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style_css}</style></head><body>{body_html}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_todo_list_url(hass: HomeAssistant, title: str, items: list, lang: str, orientation: str, small_screen: bool) -> str:
    num_items = len(items)
    if small_screen:
        if num_items <= 7: header_size, item_size, li_padding, icon_margin = "2.8em", "2.5em", "15px 0", "15px"
        elif num_items <= 12: header_size, item_size, li_padding, icon_margin = "2.2em", "2.0em", "10px 0", "12px"
        else: header_size, item_size, li_padding, icon_margin = "1.8em", "1.6em", "8px 0", "10px"
    else:
        if num_items <= 5: header_size, item_size, li_padding, icon_margin = "4.0em", "3.5em", "20px 0", "20px"
        elif num_items <= 9: header_size, item_size, li_padding, icon_margin = "3.2em", "2.8em", "15px 0", "18px"
        elif num_items <= 14: header_size, item_size, li_padding, icon_margin = "2.5em", "2.2em", "12px 0", "15px"
        else: header_size, item_size, li_padding, icon_margin = "2.0em", "1.8em", "10px 0", "12px"

    style_css = f"""
        body {{ font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 30px; box-sizing: border-box; }}
        .header {{ text-align: center; font-size: {header_size}; font-weight: bold; border-bottom: 3px solid black; padding-bottom: 20px; margin-bottom: 25px; }}
        ul {{ list-style: none; padding: 0; margin: 0; }}
        li {{ display: flex; align-items: center; font-size: {item_size}; padding: {li_padding}; border-bottom: 2px solid #eee; }}
        .icon {{ width: 1.2em; height: 1.2em; margin-right: {icon_margin}; flex-shrink: 0; }}
        .summary {{ flex-grow: 1; }}
        li.completed .summary {{ text-decoration: line-through; color: #888; }}
        .no-tasks {{ text-align: center; font-size: 3.0em; padding-top: 50px; color: #888; }}
    """

    icon_unchecked = await async_get_icon_as_base64(hass, "checkbox-blank-outline.svg")
    icon_checked = await async_get_icon_as_base64(hass, "checkbox-marked.svg")

    items_html = ""
    no_tasks_text = "Brak zadań na liście" if lang == "pl" else "No tasks on the list"
    no_description_text = "Brak opisu" if lang == "pl" else "No description"
    
    if not items:
        items_html = f"<div class='no-tasks'>{no_tasks_text}</div>"
    else:
        sorted_items = sorted(items, key=lambda x: x.get('status', 'needs_action') == 'completed')
        
        for item in sorted_items:
            summary = html.escape(item.get('summary') or item.get('name', no_description_text))
            is_complete = item.get('status') == 'completed'
            
            icon_data = icon_checked if is_complete else icon_unchecked
            css_class = "completed" if is_complete else ""
            
            items_html += f"""
            <li class="{css_class}">
                <img src="{icon_data}" class="icon" />
                <span class="summary">{summary}</span>
            </li>
            """

    html_body = f"""
    <div class="header">{html.escape(title)}</div>
    <ul>{items_html}</ul>
    """

    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{html.escape(title)}</title><style>{style_css}</style></head><body>{html_body}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_energy_panel_url(hass: HomeAssistant, states: dict[str, State | None], orientation: str, lang: str, small_screen: bool) -> str:
    panel_title = "Panel Energetyczny" if lang == "pl" else "Energy Panel"
    current_usage_label = "Aktualne zużycie" if lang == "pl" else "Current Usage"
    production_label = "Produkcja" if lang == "pl" else "Production"
    import_label = "Pobór" if lang == "pl" else "Import"
    export_label = "Eksport" if lang == "pl" else "Export"
    consumption_label = "Zużycie" if lang == "pl" else "Consumption"

    async def get_icon(name):
        return await async_get_icon_as_base64(hass, name)

    def get_state_val(state: State | None, precision: int = 2) -> str:
        if state is None or state.state in UNKNOWN_STRINGS:
            return "---"
        try:
            return str(round(float(state.state), precision))
        except (ValueError, TypeError):
            return "---"

    icons = {
        "usage": await get_icon("power-plug.svg"),
        "solar": await get_icon("solar-power.svg"),
        "import": await get_icon("transmission-tower-import.svg"),
        "export": await get_icon("transmission-tower-export.svg"),
        "home": await get_icon("home-lightning-bolt.svg"),
    }
    
    is_portrait = orientation in ["1", "3"]
    main_val_fs = "5.5em" if small_screen else "8em"
    main_lbl_fs = "1.5em" if small_screen else "1.8em"
    card_val_fs = "2.0em" if small_screen else "2.5em"
    card_lbl_fs = "1.1em" if small_screen else "1.3em"
    icon_size = "48px" if small_screen else "60px"
    flex_direction = "column" if is_portrait else "row"
    main_stat_margin = "10px 0" if is_portrait else "20px 0"
    stat_card_basis = "45%"

    style_css = f"""
        body {{ font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 20px; box-sizing: border-box; display: flex; flex-direction: {flex_direction}; height: 100vh; width: 100vw; }}
        .header {{ text-align: center; font-size: 2em; font-weight: bold; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 10px; flex-shrink: 0; }}
        .main-content {{ display: flex; flex-direction: column; flex-grow: 1; justify-content: center; }}
        .main-stat {{ text-align: center; margin: {main_stat_margin}; }}
        .main-stat .value {{ font-size: {main_val_fs}; font-weight: bold; line-height: 1.1; display: inline-flex; align-items: flex-start; gap: 5px; }}
        .main-stat .unit {{ font-size: 0.3em; font-weight: bold; opacity: 0.9; padding-top: 1em; }}
        .main-stat .label {{ font-size: {main_lbl_fs}; }}
        .stats-grid {{ display: flex; flex-wrap: wrap; justify-content: space-around; width: 100%; flex-grow: 1; align-content: center; gap: 15px; }}
        .stat-card {{ flex-basis: {stat_card_basis}; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
        .stat-card .icon {{ width: {icon_size}; height: {icon_size}; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: {card_val_fs}; font-weight: bold; }}
        .stat-card .label {{ font-size: {card_lbl_fs}; opacity: 0.8; }}
    """

    power_usage_state = states.get(ATTR_POWER_USAGE_ENTITY)
    daily_consumption_state = states.get(ATTR_DAILY_CONSUMPTION_ENTITY)
    daily_production_state = states.get(ATTR_DAILY_PRODUCTION_ENTITY)
    daily_import_state = states.get(ATTR_DAILY_GRID_IMPORT_ENTITY)
    daily_export_state = states.get(ATTR_DAILY_GRID_EXPORT_ENTITY)

    main_stat_html = ""
    if power_usage_state:
        unit = power_usage_state.attributes.get("unit_of_measurement", UnitOfPower.WATT)
        main_stat_html = f"""
        <div class="main-stat">
            <div class="value">
                <span>{get_state_val(power_usage_state, 0)}</span>
                <span class="unit">{unit}</span>
            </div>
            <div class="label">{current_usage_label}</div>
        </div>
        """

    grid_html = ""
    
    if daily_production_state:
        unit = daily_production_state.attributes.get("unit_of_measurement", UnitOfEnergy.KILO_WATT_HOUR)
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['solar']}" class="icon" />
            <div class="value">{get_state_val(daily_production_state)} {unit}</div>
            <div class="label">{production_label}</div>
        </div>
        """
    
    if daily_import_state:
        unit = daily_import_state.attributes.get("unit_of_measurement", UnitOfEnergy.KILO_WATT_HOUR)
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['import']}" class="icon" />
            <div class="value">{get_state_val(daily_import_state)} {unit}</div>
            <div class="label">{import_label}</div>
        </div>
        """

    if daily_export_state:
        unit = daily_export_state.attributes.get("unit_of_measurement", UnitOfEnergy.KILO_WATT_HOUR)
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['export']}" class="icon" />
            <div class="value">{get_state_val(daily_export_state)} {unit}</div>
            <div class="label">{export_label}</div>
        </div>
        """

    if daily_consumption_state:
        unit = daily_consumption_state.attributes.get("unit_of_measurement", UnitOfEnergy.KILO_WATT_HOUR)
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['home']}" class="icon" />
            <div class="value">{get_state_val(daily_consumption_state)} {unit}</div>
            <div class="label">{consumption_label}</div>
        </div>
        """

    html_body = f"""
    <div class="header">{panel_title}</div>
    <div class="main-content">
        {main_stat_html}
        <div class="stats-grid">{grid_html}</div>
    </div>
    """

    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{panel_title}</title><style>{style_css}</style></head><body>{html_body}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_qr_code_url(qr_data: str, message: str = "", qr_message_text_size: int = 24, qr_message_position: str = "below", box_size: int = 10, border: int = 4, fill_color: str = "black", back_color: str = "white") -> str:
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=box_size, border=border)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        img_data_url = f"data:image/png;base64,{img_str}"
        escaped_message = html.escape(message).replace('\n', '<br>')
        message_margin = "margin-top: 20px;" if qr_message_position == "below" else "margin-bottom: 20px;"
        message_html = f'<div style="{message_margin} font-size: {qr_message_text_size}px; font-family: sans-serif;">{escaped_message}</div>' if message else ""
        flex_direction = "column-reverse" if qr_message_position == "above" else "column"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>QR Code</title></head>
        <body style="margin: 0; padding: 20px; width: 100vw; height: 100vh; display: flex; flex-direction: {flex_direction}; align-items: center; justify-content: center; background-color: {back_color}; color: {fill_color}; box-sizing: border-box;">
            <div><img src="{img_data_url}" /></div>
            {message_html}
        </body>
        </html>
        """
        encoded = urllib.parse.quote(html_content, safe='')
        return f"data:text/html,{encoded}"
    except Exception as e:
        _LOGGER.error(f"Error generating QR code: {e}")
        return "data:text/html,<html><body>Error generating QR code.</body></html>"

def create_calendar_list_view_html(events: list, style: str = "modern", add_back_button: bool = False, day_date: datetime.date = None, lang: str = "en") -> str:
    html_body_content = ""
    
    no_events_text = "Brak wydarzeń tego dnia" if lang == "pl" else "No events on this day"
    no_title_text = "Brak tytułu" if lang == "pl" else "No title"

    if add_back_button:
        html_body_content += '<a href="#" onclick="showView(\'monthly-view\'); return false;" class="back-button">&#x2190;</a>'
    
    if day_date:
        html_body_content += f'<div class="date-header">{_format_long_date(day_date, lang)}</div>'

    if not events:
        html_body_content += f'<div class="no-events">{no_events_text}</div>'
    else:
        sorted_events = sorted(events, key=lambda x: x['start'])
        
        if not day_date:
            events_by_day = {}
            for event in sorted_events:
                event_date = event['start'].date()
                if event_date not in events_by_day:
                    events_by_day[event_date] = []
                events_by_day[event_date].append(event)
            
            for event_date, day_events in events_by_day.items():
                html_body_content += f'<div class="date-header">{_format_long_date(event_date, lang)}</div>'
                for event in day_events:
                    html_body_content += _generate_event_html(event, no_title_text)
        else:
            for event in sorted_events:
                html_body_content += _generate_event_html(event, no_title_text)

    return html_body_content

def _generate_event_html(event: dict, no_title_text: str) -> str:
    start_time_str = event['start'].strftime('%H:%M')
    time_html = start_time_str

    if event.get('end') and isinstance(event['end'], datetime):
        if event['start'] != event['end']:
            end_time_str = event['end'].strftime('%H:%M')
            time_html = f"{start_time_str} - {end_time_str}"

    summary = html.escape(event.get('summary', no_title_text))
    location = html.escape(event.get('location', ''))
    description = html.escape(event.get('description', ''))

    location_html = f'<div class="location">{location}</div>' if location else ''
    description_html = f'<div class="description">{description.replace(chr(10), "<br>")}</div>' if description else ''

    return f'''
    <div class="event">
        <div class="time">{time_html}</div>
        <div class="details">
            <div class="summary">{summary}</div>
            {location_html}
            {description_html}
        </div>
    </div>
    '''

def create_calendar_url(events: list, style: str = "modern", lang: str = "en") -> str:
    calendar_title = "Kalendarz" if lang == "pl" else "Calendar"
    
    if style == "modern":
        style_css = """
            body { font-family: 'Trebuchet MS', sans-serif; background-color: white; color: black; margin: 0; padding: 20px; box-sizing: border-box; }
            .date-header { text-align: center; font-size: 1.5em; border-bottom: 2px solid black; padding-bottom: 10px; margin-top: 20px; margin-bottom: 15px; }
            .event { display: flex; margin-bottom: 15px; padding: 10px; border-left: 5px solid black; background-color: #f9f9f9; }
            .time { font-weight: bold; font-size: 1.2em; flex: 0 0 150px; }
            .details { display: flex; flex-direction: column; flex-grow: 1; }
            .summary { font-size: 1.1em; margin-bottom: 5px; }
            .location { font-style: italic; color: #555; font-size: 1em; }
            .description { margin-top: 8px; font-size: 0.9em; color: #333; white-space: pre-wrap; }
            .no-events { text-align: center; font-size: 1.5em; padding-top: 50px; }
        """
    else: # minimalist
        style_css = """
            body { font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; }
            .date-header { font-size: 1.2em; font-weight: bold; margin-top: 25px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px;}
            .event { display: flex; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid #eee; }
            .time { flex: 0 0 120px; font-weight: bold; }
            .details { display: flex; flex-direction: column; flex-grow: 1; }
            .summary { font-size: 1.1em; }
            .location, .description { display: none; }
            .no-events { text-align: center; font-size: 1.2em; padding-top: 20%; }
        """
    html_body_content = create_calendar_list_view_html(events, style, add_back_button=False, lang=lang)
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{calendar_title}</title><style>{style_css}</style></head><body>{html_body_content}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_monthly_calendar_url(year: int, month: int, events: list, lang: str = "en", small_screen: bool = False) -> str:
    calendar_title = "Kalendarz Miesięczny" if lang == "pl" else "Monthly Calendar"

    if small_screen:
        header_fs = "2.6em"
        day_fs = "2.2em"
        week_style = "height: calc(100% / 6); border-bottom: 1px solid #ccc;"
        day_cell_style = "border-top: none;"
    else:
        header_fs = "3.5em"
        day_fs = "3.2em"
        week_style = "flex-grow: 1;"
        day_cell_style = "border-top: 1px solid #ccc;"

    style_css = f"""
        body {{ font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 15px; box-sizing: border-box; }}
        a {{ text-decoration: none; color: inherit; }}
        #monthly-view {{ display: flex; flex-direction: column; height: calc(100vh - 130px); }}
        .month-header {{ text-align: center; font-size: {header_fs}; padding-bottom: 15px; font-weight: bold; }}
        .calendar-grid {{ display: flex; flex-direction: column; flex-grow: 1; }}
        .week-header {{ display: flex; flex-grow: 1; max-height: 40px; }}
        .week {{ display: flex; {week_style} }}
        .day-name, .day-cell {{ flex-basis: 0; flex-grow: 1; text-align: center; display: flex; align-items: center; justify-content: center; }}
        .day-name {{ font-weight: bold; font-size: 1.5em; }}
        .day-cell {{ {day_cell_style} position: relative; font-size: {day_fs}; font-weight: bold; cursor: pointer; }}
        .day-cell.empty {{ background-color: #f8f8f8; cursor: default; }}
        .day-cell a {{ display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }}
        .day-cell .day-number {{ z-index: 1; }}
        .day-cell.today .day-number {{ background-color: black; color: white; border-radius: 50%; width: 1.5em; height: 1.5em; line-height: 1.5em; display: inline-block; }}
        .day-number.has-event {{ color: black; border: 3px solid black; border-radius: 50%; width: calc(1.5em - 6px); height: calc(1.5em - 6px); line-height: calc(1.5em - 6px); display: inline-block; }}
        .daily-view-container {{ padding: 25px; }}
        .back-button {{ font-size: 2.5em; text-decoration: none; color: black; position: absolute; top: 20px; left: 25px; cursor: pointer; z-index: 1001; }}
        .date-header {{ text-align: center; font-size: 2.2em; border-bottom: 2px solid black; padding-bottom: 15px; margin-bottom: 20px; }}
        .event {{ display: flex; margin-bottom: 20px; padding: 15px; border-left: 5px solid black; background-color: #f9f9f9; }}
        .time {{ font-weight: bold; font-size: 1.8em; flex: 0 0 220px; }}
        .details {{ display: flex; flex-direction: column; flex-grow: 1; }}
        .summary {{ font-size: 1.6em; margin-bottom: 8px; }}
        .location {{ font-style: italic; color: #555; font-size: 1.4em; }}
        .description {{ margin-top: 10px; font-size: 1.2em; color: #333; white-space: pre-wrap; }}
        .no-events {{ text-align: center; font-size: 2em; padding-top: 60px; }}
    """
    js_script = """
        function showView(viewId) {
            document.getElementById('monthly-view').style.display = 'none';
            var dailyViews = document.getElementsByClassName('daily-view');
            for (var i = 0; i < dailyViews.length; i++) {
                dailyViews[i].style.display = 'none';
            }
            var viewToShow = document.getElementById(viewId);
            if (viewToShow) {
                if (viewId === 'monthly-view') {
                    viewToShow.style.display = 'flex';
                } else {
                    viewToShow.style.display = 'block';
                }
            }
        }
    """
    cal = calendar.Calendar()
    month_matrix = cal.monthdatescalendar(year, month)
    today = dt_util.now().date()
    event_dates = {e['start'].date() for e in events if isinstance(e.get('start'), datetime)}
    if lang == "pl":
        month_name = f"{_PL_MONTH_NAMES[month-1].capitalize()} {year}"
    else:
        month_name = f"{_EN_MONTH_NAMES[month-1]} {year}"

    monthly_view_html = f'<div id="monthly-view"><div class="month-header">{month_name}</div><div class="calendar-grid">'
    day_names = _PL_DAY_ABBR if lang == "pl" else _EN_DAY_ABBR
    monthly_view_html += '<div class="week-header">'
    for name in day_names: monthly_view_html += f'<div class="day-name">{name}</div>'
    monthly_view_html += '</div>'
    daily_views_html = ""
    for week in month_matrix:
        monthly_view_html += '<div class="week">'
        for day_date in week:
            class_list = ["day-cell"]
            if day_date.month != month:
                class_list.append("empty")
                monthly_view_html += f'<div class="{" ".join(class_list)}"></div>'
                continue
            if day_date == today: class_list.append("today")
            day_number_classes = ["day-number"]
            if day_date in event_dates and day_date != today: day_number_classes.append("has-event")
            day_number_html = f'<span class="{" ".join(day_number_classes)}">{day_date.day}</span>'
            view_id = f'view-{day_date.isoformat()}'
            events_for_day = [e for e in events if isinstance(e.get('start'), datetime) and e['start'].date() == day_date]
            daily_list_html = create_calendar_list_view_html(events_for_day, style="modern", add_back_button=True, day_date=day_date, lang=lang)
            daily_views_html += f'<div id="{view_id}" class="daily-view" style="display: none;"><div class="daily-view-container">{daily_list_html}</div></div>'
            monthly_view_html += f'<a href="#" onclick="showView(\'{view_id}\'); return false;" class="{" ".join(class_list)}">{day_number_html}</a>'
        monthly_view_html += '</div>'
    monthly_view_html += '</div></div>'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{calendar_title}</title><style>{style_css}</style><script>{js_script}</script></head><body>{monthly_view_html}{daily_views_html}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def wind_deg_to_direction(deg, lang: str):
    if deg is None: return ""
    try:
        deg = float(deg)
        if lang == "pl":
            dirs = ["Pn", "Pn-Wsch", "Wsch", "Pd-Wsch", "Pd", "Pd-Zach", "Zach", "Pn-Zach"]
        else:
            dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ix = round(deg / (360. / len(dirs)))
        return dirs[ix % len(dirs)]
    except (ValueError, TypeError): return ""

def _generate_weather_forecast_graph(
    hourly_forecast: list,
    lang: str,
    temp_unit: str,
    is_portrait: bool
) -> bytes | None:
    if not hourly_forecast:
        return None

    try:
        timestamps, temperatures = [], []
        for forecast in hourly_forecast[:25]:
            if 'datetime' in forecast and 'temperature' in forecast:
                timestamps.append(dt_util.parse_datetime(forecast['datetime']))
                temperatures.append(forecast['temperature'])

        if not timestamps:
            return None

        plt.style.use('grayscale')
        matplotlib.rcParams.update({
            'font.size': 20, 'axes.titlesize': 24, 'axes.labelsize': 18,
            'xtick.labelsize': 16, 'ytick.labelsize': 16, 'lines.linewidth': 3.5,
            'lines.markersize': 8, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
            'savefig.facecolor': 'white', 'text.color': 'black', 'axes.labelcolor': 'black',
            'xtick.color': 'black', 'ytick.color': 'black', 'axes.edgecolor': 'black',
        })
        
        figsize = (8, 6) if is_portrait else (10, 4.5)
        fig, ax = plt.subplots(figsize=figsize, dpi=100)

        ax.plot(timestamps, temperatures, marker='o', linestyle='-')

        title = "Prognoza 24h" if lang == "pl" else "24h Forecast"
        ax.set_title(title, fontweight='bold')
        ax.set_ylabel(f"{'Temperatura' if lang == 'pl' else 'Temperature'} ({temp_unit})")
        ax.grid(True, which='major', linestyle='--', linewidth=1.0)
        
        if is_portrait:
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            fig.autofmt_xdate(rotation=30, ha='right')
            plt.subplots_adjust(left=0.18, right=0.95, top=0.88, bottom=0.20)
        else:
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
            fig.autofmt_xdate(rotation=0, ha='center')
            plt.subplots_adjust(left=0.12, right=0.97, top=0.85, bottom=0.15)
            
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    except Exception as e:
        _LOGGER.error(f"Failed to generate weather forecast graph: {e}")
        return None

async def create_weather_url(
    hass: HomeAssistant, 
    weather_state: State, 
    daily_forecast: list | None,
    hourly_forecast: list | None,
    layout: str,
    orientation: str,
    lang: str,
    small_screen: bool
) -> str:
    weather_title = "Pogoda" if lang == "pl" else "Weather"
    feels_like_label = "Odczuwalna" if lang == "pl" else "Feels like"
    wind_label = "Wiatr" if lang == "pl" else "Wind"
    pressure_label = "Ciśnienie" if lang == "pl" else "Pressure"
    humidity_label = "Wilgotność" if lang == "pl" else "Humidity"
    no_daily_data_label = "Brak prognozy dziennej." if lang == "pl" else "No daily forecast data."
    no_graph_data_label = "Błąd generowania wykresu" if lang == 'pl' else "Error generating graph"
    
    state = weather_state.state
    attrs = weather_state.attributes

    def _get_attr_as_float(attributes, key, default=0.0):
        val = attributes.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    
    sun_state = hass.states.get("sun.sun")
    is_day = sun_state and sun_state.state == "above_horizon"
    
    icon_map = {
        "sunny": "wi-day-sunny.svg", "clear-night": "wi-night-clear.svg", "cloudy": "wi-cloudy.svg",
        "fog": "wi-fog.svg", "hail": "wi-hail.svg", "lightning": "wi-lightning.svg",
        "lightning-rainy": "wi-storm-showers.svg",
        "partlycloudy": "wi-day-cloudy.svg" if is_day else "wi-night-alt-cloudy.svg",
        "pouring": "wi-showers.svg", "rainy": "wi-rain.svg", "snowy": "wi-snow.svg",
        "snowy-rainy": "wi-rain-mix.svg", "windy": "wi-strong-wind.svg",
        "windy-variant": "wi-cloudy-gusts.svg", "exceptional": "wi-tornado.svg",
    }

    async def get_weather_icon(condition_state):
        icon_name = icon_map.get(condition_state, "wi-cloud.svg")
        return await async_get_icon_as_base64(hass, icon_name)
    
    is_portrait = orientation in ["1", "3"]

    style_css = f"""
        body {{ font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; display: flex; flex-direction: column; height: 100vh; width: 100vw; }}
        hr {{ border: 0; border-top: 2px solid #000; margin: 15px 0; }}
        .flex {{ display: flex; }} .col {{ flex-direction: column; }} .center {{ align-items: center; justify-content: center; }}
        .space-around {{ justify-content: space-around; }} .space-between {{ justify-content: space-between; }}
        .icon {{ width: 1em; height: 1em; vertical-align: middle; }}
        
        .weather-graph-panel {{ display: flex; flex-direction: column; height: 100%; width: 100%; }}
        .graph-section {{ flex: 5; display: flex; align-items: center; justify-content: center; width: 100%; }}
        .graph-section img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .current-conditions-section {{ flex: 3; border-top: 3px solid black; margin-top: 20px; padding-top: 15px; }}
        
        .summary-header {{ width: 100%; text-align: center; }}
        .summary-main {{ display: flex; align-items: center; justify-content: center; margin: 10px 0; }}
        .summary-main .temp {{ font-size: {'10em' if small_screen else '12em'}; font-weight: bold; line-height: 1; }}
        .summary-main .icon {{ width: {'180px' if small_screen else '220px'}; height: {'180px' if small_screen else '220px'}; margin-left: 20px; }}
        .feels-like {{ font-size: {'1.8em' if small_screen else '2.2em'}; opacity: 0.8; margin-top: -15px; }}
        
        .summary-details {{ font-size: {'1.5em' if small_screen else '1.8em'}; display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; text-align: left; padding: 0 10px; }}
        .detail-item {{ display: flex; align-items: center; }}
        .detail-item .icon {{ width: 2em; height: 2em; margin-right: 10px; }}
        
        .hourly-forecast {{ text-align: center; }}
        .hourly-list {{ display: flex; justify-content: space-around; margin-top: 10px; }}
        .hourly-item {{ font-size: {'1.6em' if small_screen else '2em'}; }}
        .hourly-item .icon {{ width: {'60px' if small_screen else '80px'}; height: {'60px' if small_screen else '80px'}; }}
        
        .daily-forecast-summary {{ margin-top: 10px; }}
        .daily-item-summary {{ display: flex; align-items: center; font-size: {'1.7em' if small_screen else '2.1em'}; padding: 5px 0; border-bottom: 2px solid #eee; }}
        .daily-item-summary:last-child {{ border-bottom: none; }}
        .daily-item-summary .day {{ font-weight: bold; flex-basis: 25%; }}
        .daily-item-summary .icon {{ width: {'50px' if small_screen else '60px'}; height: {'50px' if small_screen else '60px'}; margin: 0 15px; }}
        .daily-item-summary .temps {{ flex-grow: 1; text-align: right; }}

        .daily-list-standalone {{ padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-around; flex-grow: 1; }}
        .daily-list-standalone .daily-item {{ font-size: {'2.8em' if small_screen else '3.5em'}; padding: 20px 0; display: flex; align-items: center; border-bottom: 2px solid #ccc; }}
        .daily-list-standalone .daily-item:last-child {{ border-bottom: none; }}
        .daily-list-standalone .daily-item .day {{ flex: 0 0 {'140px' if small_screen else '180px'}; font-weight: bold; }}
        .daily-list-standalone .daily-item .icon {{ width: {'80px' if small_screen else '100px'}; height: {'80px' if small_screen else '100px'}; margin: 0 20px; }}
        .daily-list-standalone .daily-item .temps {{ flex-grow: 1; text-align: center; }}
        .daily-list-standalone .daily-item .precip {{ display: flex; align-items: center; justify-content: flex-end; flex: 0 0 {'140px' if small_screen else '180px'}; }}
        .daily-list-standalone .daily-item .precip .icon {{ width: {'32px' if small_screen else '40px'}; height: {'32px' if small_screen else '40px'}; margin-right: 10px; }}
    """
    
    html_body = ""
    temp = f"{round(_get_attr_as_float(attrs, 'temperature'))}&deg;"
    apparent_temp_val = _get_attr_as_float(attrs, 'apparent_temperature', default=_get_attr_as_float(attrs, 'temperature'))
    feels_like = f"{round(apparent_temp_val)}&deg;"
    main_icon_url = await get_weather_icon(state)

    if layout == "weather_graph_panel":
        html_body += '<div class="weather-graph-panel">'
        temp_unit = attrs.get("temperature_unit", "°C")
        image_bytes = await hass.async_add_executor_job(
            _generate_weather_forecast_graph, hourly_forecast, lang, temp_unit, is_portrait
        )
        graph_section_html = '<div class="graph-section">'
        if image_bytes:
            img_str = base64.b64encode(image_bytes).decode("utf-8")
            img_data_url = f"data:image/png;base64,{img_str}"
            graph_section_html += f'<img src="{img_data_url}" />'
        else:
            graph_section_html += f'<div style="font-size: 2em;">{no_graph_data_label}</div>'
        graph_section_html += '</div>'
        html_body += graph_section_html
        
        current_conditions_html = '<div class="current-conditions-section">'
        current_conditions_html += f"""
        <div class="summary-header">
            <div class="summary-main">
                <div class="temp" style="font-size: {'7em' if small_screen else '9em'};">{temp}</div>
                <img src="{main_icon_url}" class="icon" style="width: {'140px' if small_screen else '180px'}; height: {'140px' if small_screen else '180px'};" />
            </div>
            <div class="feels-like" style="font-size: {'1.6em' if small_screen else '2em'}; margin-top: -10px;">{feels_like_label}: {feels_like}</div>
        </div>"""
        current_conditions_html += '</div>'
        html_body += current_conditions_html
        html_body += '</div>'

    elif layout == "daily_forecast_list":
        html_body += '<div class="daily-list-standalone">'
        if daily_forecast:
            umbrella_icon = await async_get_icon_as_base64(hass, "wi-umbrella.svg")
            for day in daily_forecast[:5]:
                if not isinstance(day, dict): continue
                day_name = dt_util.parse_datetime(day.get('datetime')).strftime("%a")
                temp_high = f"{round(day.get('temperature', 0))}&deg;"
                temp_low = f"{round(day.get('templow', 0))}&deg;"
                precip_chance = day.get('precipitation_probability', 0)
                icon_url = await get_weather_icon(day.get('condition'))
                
                html_body += f"""
                <div class="daily-item">
                    <div class="day">{day_name}</div>
                    <img src="{icon_url}" class="icon" />
                    <div class="temps">{temp_high} / {temp_low}</div>
                    <div class="precip"><img src="{umbrella_icon}" class="icon" /><span>{precip_chance}%</span></div>
                </div>"""
        else:
            html_body += f'<div style="font-size: 2em; text-align: center;">{no_daily_data_label}</div>'
        html_body += '</div>'

    else: # Detailed Summary
        html_body += f"""
        <div class="summary-header">
            <div class="summary-main">
                <div class="temp">{temp}</div>
                <img src="{main_icon_url}" class="icon" />
            </div>
            <div class="feels-like">{feels_like_label}: {feels_like}</div>
        </div>"""

        humidity = f"{attrs.get('humidity', 0)}%"
        wind_speed = f"{attrs.get('wind_speed', 0)} {attrs.get('wind_speed_unit', 'km/h')}"
        wind_dir = wind_deg_to_direction(attrs.get('wind_bearing'), lang)
        pressure = f"{attrs.get('pressure', 0)} {attrs.get('pressure_unit', 'hPa')}"
        
        sunrise, sunset = "---", "---"
        if sun_state and sun_state.attributes:
            sunrise_dt = dt_util.parse_datetime(sun_state.attributes.get("next_rising", ""))
            sunset_dt = dt_util.parse_datetime(sun_state.attributes.get("next_setting", ""))
            if sunrise_dt: sunrise = sunrise_dt.strftime("%H:%M")
            if sunset_dt: sunset = sunset_dt.strftime("%H:%M")

        html_body += f"""
        <div class="summary-details">
            <div class="detail-item">{wind_label}: {wind_dir} {wind_speed}</div>
            <div class="detail-item">{pressure_label}: {pressure}</div>
            <div class="detail-item">{humidity_label}: {humidity}</div>
            <div class="detail-item">
                <img src="{await async_get_icon_as_base64(hass, 'wi-sunrise.svg')}" class="icon" /> {sunrise} / 
                <img src="{await async_get_icon_as_base64(hass, 'wi-sunset.svg')}" class="icon" /> {sunset}
            </div>
        </div>"""
        
        html_body += "<hr/>"

        if hourly_forecast:
            html_body += '<div class="hourly-forecast"><div class="hourly-list">'
            for hour in hourly_forecast[:4]: 
                if not isinstance(hour, dict): continue
                hour_str = dt_util.parse_datetime(hour.get('datetime')).strftime("%H:00")
                hour_temp = f"{round(hour.get('temperature', 0))}&deg;"
                hour_icon = await get_weather_icon(hour.get('condition'))
                html_body += f"""
                <div class="hourly-item">
                    <div>{hour_str}</div><img src="{hour_icon}" class="icon" /><div class="temp">{hour_temp}</div>
                </div>"""
            html_body += '</div></div>'
        
        if daily_forecast:
            html_body += "<hr/>"
            html_body += '<div class="daily-forecast-summary">'
            for day in daily_forecast[:5]:
                if not isinstance(day, dict): continue
                day_name = dt_util.parse_datetime(day.get('datetime')).strftime("%a") if lang == "en" else _PL_DAY_ABBR[dt_util.parse_datetime(day.get('datetime')).weekday()]
                temp_high = f"{round(day.get('temperature', 0))}&deg;"
                temp_low = f"{round(day.get('templow', 0))}&deg;"
                icon_url = await get_weather_icon(day.get('condition'))
                html_body += f"""
                <div class="daily-item-summary">
                    <div class="day">{day_name}</div>
                    <img src="{icon_url}" class="icon" />
                    <div class="temps">{temp_high} / {temp_low}</div>
                </div>
                """
            html_body += '</div>'

    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{weather_title}</title><style>{style_css}</style></head><body>{html_body}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_simple_cache_buster(url: str) -> str:
    timestamp, separator = int(time.time()), "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}&reload_timeout=300"

def _generate_graph_image(
    hass: HomeAssistant,
    history_data: dict,
    entity_ids: list[str],
    graph_type: str,
    show_points: bool,
    orientation: str,
) -> bytes | None:
    try:
        import numpy as np
    except ImportError:
        _LOGGER.error("The 'matplotlib' library is not installed.")
        return None

    if not history_data:
        _LOGGER.warning(f"No historical data provided for entities: {entity_ids}")
        return None

    plt.style.use('grayscale')
    matplotlib.rcParams.update({
        'font.size': 24, 'axes.titlesize': 30, 'axes.labelsize': 22,
        'xtick.labelsize': 18, 'ytick.labelsize': 18, 'lines.linewidth': 4,
        'lines.markersize': 10, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
        'savefig.facecolor': 'white', 'text.color': 'black', 'axes.labelcolor': 'black',
        'xtick.color': 'black', 'ytick.color': 'black', 'axes.edgecolor': 'black',
        'legend.fontsize': 20
    })
    
    line_cycler = (cycler('linestyle', ['-', '--', ':', '-.']))
    bar_colors = ['#222222', '#666666', '#999999', '#BBBBBB']
    
    is_portrait = orientation in ["1", "3"]
    figsize = (7.5, 10) if is_portrait else (10, 7.5)
    
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    has_data = False
    
    ax.set_prop_cycle(line_cycler)
    
    num_entities = len(entity_ids)

    for i, entity_id in enumerate(entity_ids):
        if entity_id not in history_data:
            continue
        states = history_data[entity_id]
        timestamps, values = [], []
        for state in states:
            try:
                if state.state not in UNKNOWN_STRINGS:
                    values.append(float(state.state))
                    timestamps.append(state.last_updated)
            except (ValueError, TypeError):
                continue
        if not values:
            continue
        has_data = True
        entity_state = hass.states.get(entity_id)
        entity_name = entity_state.name if entity_state else entity_id
        
        plot_args = {'label': entity_name}
        if graph_type == 'line':
            if show_points:
                plot_args['marker'] = 'o'
            ax.plot(timestamps, values, **plot_args)
        elif graph_type == 'bar':
            total_bar_width = timedelta(hours=0.8)
            bar_width = total_bar_width / num_entities
            offset = (i - (num_entities - 1) / 2) * bar_width
            bar_timestamps = [ts + offset for ts in timestamps]
            plot_args['color'] = bar_colors[i % len(bar_colors)]
            ax.bar(bar_timestamps, values, **plot_args, width=bar_width)

    if not has_data:
        _LOGGER.warning("After filtering, no valid data was found to draw the graph.")
        plt.close(fig)
        return None

    handles, labels = ax.get_legend_handles_labels()
    if len(entity_ids) > 1:
        fig.legend(
            handles, 
            labels, 
            loc='upper center',
            bbox_to_anchor=(0.5, 0.98),
            ncol=1,
            frameon=False
        )
    
    ax.grid(True, which='major', linestyle='--', linewidth=1.0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d-%m'))
    fig.autofmt_xdate(bottom=0.2, rotation=30, ha='right')
        
    try:
        ax.set_ylabel(hass.states.get(entity_ids[0]).attributes.get('unit_of_measurement', ''))
    except (IndexError, AttributeError):
        pass

    if len(labels) > 1:
        top_margin = 1 - (0.05 * len(labels)) - 0.05
        top_margin = max(0.80, min(0.92, top_margin))
    else:
        top_margin = 0.95
        
    plt.subplots_adjust(left=0.15, right=0.95, top=top_margin, bottom=0.18)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Starting setup of Visionect Joan config entry.")
    api = VisionectAPI(hass, entry.data[CONF_HOST], entry.data.get(CONF_USERNAME), entry.data.get(CONF_PASSWORD), entry.data.get(CONF_API_KEY), entry.data.get(CONF_API_SECRET))
    if not await api.async_test_authentication():
        _LOGGER.error("Authentication failed. Cannot load integration.")
        return False
    async def async_update_data():
        try:
            devices_summary = await api.async_get_all_devices()
            if not devices_summary: _LOGGER.warning("No device data from API"); return {}
            data = {}
            for device_summary in devices_summary:
                uuid_val = device_summary.get("Uuid")
                if not uuid_val: _LOGGER.warning("Device without UUID was skipped"); continue
                device_details = await api.async_get_device_data(uuid_val)
                if not device_details: _LOGGER.warning(f"Could not get details for device {uuid_val}"); continue
                final_data = device_details
                if "Config" not in final_data: final_data["Config"] = {}
                device_name = device_summary.get("Options", {}).get("Name")
                if device_name and device_name.lower() not in UNKNOWN_STRINGS: final_data["Config"]["Name"] = device_name
                final_data["Options"] = device_summary.get("Options", {})
                final_data["LastUpdated"] = datetime.now(timezone.utc)
                data[uuid_val] = final_data
            _LOGGER.debug(f"Updated data for {len(data)} devices")
            return data
        except Exception as e: _LOGGER.error(f"Error during data update: {e}"); return {}
    coordinator = DataUpdateCoordinator(hass, _LOGGER, name=f"visionect_{entry.entry_id}", update_method=async_update_data, update_interval=SCAN_INTERVAL)
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {"api": api, "coordinator": coordinator}
    device_reg = dr.async_get(hass)
    async def get_uuids_from_call(call: ServiceCall) -> list[str]:
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if isinstance(device_ids, str): device_ids = [device_ids]
        if not device_ids: return []
        uuids_list = []
        for device_id in device_ids:
            device_entry = device_reg.async_get(device_id)
            if device_entry and (uuid_val := next((i[1] for i in device_entry.identifiers if i[0] == DOMAIN), None)): uuids_list.append(uuid_val)
            else: _LOGGER.warning(f"Could not find UUID for device_id: {device_id}")
        return uuids_list
    
    async def handle_set_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        original_url = call.data[ATTR_URL]
        if not original_url.strip(): _LOGGER.error("Empty URL was rejected"); return
        url_with_buster = create_simple_cache_buster(original_url)
        tasks = [api.async_set_device_url(uuid, url_with_buster) for uuid in uuids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, uuid_val in enumerate(uuids):
            result = results[i]
            status = "failure"
            if isinstance(result, Exception):
                _LOGGER.error(f"Error while changing URL for {uuid_val}: {result}")
            elif result:
                status = "success"
                _LOGGER.info(f"URL for {uuid_val} successfully changed to: {original_url}")
            else:
                _LOGGER.error(f"Failed to change URL for {uuid_val}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_URL, "status": status, "params": {"url": original_url}})

        await coordinator.async_request_refresh()
        
    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        if isinstance(message_template, Template): message_template.hass = hass
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        image_url = call.data.get(ATTR_IMAGE_URL)
        if image_url and call.data[ATTR_LAYOUT] != "text_only":
            if not api.validate_image_url(image_url): _LOGGER.warning(f"Image URL may not be supported: {image_url}")
        
        content_url = create_text_message_url(message, call.data[ATTR_TEXT_COLOR], call.data[ATTR_BACKGROUND_COLOR], f"{call.data[ATTR_TEXT_SIZE]}px", call.data[ATTR_TEXT_ALIGN], call.data[ATTR_FONT_FAMILY], call.data[ATTR_FONT_WEIGHT], call.data[ATTR_LAYOUT], image_url, call.data.get(ATTR_IMAGE_ZOOM))
        
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        final_url = _add_interactive_layer_to_url(
            hass=hass,
            data_url=content_url,
            back_url=back_url,
            add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
            click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
            action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
        )

        tasks = [api.async_set_device_url(uuid, final_url) for uuid in uuids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, uuid_val in enumerate(uuids):
            status = "failure"
            if not isinstance(results[i], Exception) and results[i]: status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_TEXT, "status": status, "params": {"message": message}})

    async def handle_send_weather(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        weather_entity_id = call.data[ATTR_WEATHER_ENTITY]
        layout = call.data[ATTR_LAYOUT]
        lang = _get_lang(hass)
        small_screen = call.data[ATTR_SMALL_SCREEN]
        
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url

        async def send_to_device(uuid_val):
            device_data = coordinator.data.get(uuid_val, {})
            config = device_data.get("Config", {})
            orientation = str(config.get("DisplayRotation", "0"))
            weather_state = hass.states.get(weather_entity_id)
            if not weather_state:
                _LOGGER.error(f"Weather entity not found: {weather_entity_id}")
                return
                
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
            final_url = _add_interactive_layer_to_url(
                hass=hass,
                data_url=content_url,
                back_url=back_url,
                add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
                click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
            )

            _LOGGER.info(f"Sending weather '{weather_entity_id}' to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending weather to {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_WEATHER, "status": status})

        await asyncio.gather(*(send_to_device(uuid) for uuid in uuids))

    async def handle_send_energy_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_states = {key: hass.states.get(entity_id) for key, entity_id in call.data.items() if key.endswith("_entity") and entity_id}
        if not any(entity_states.values()): _LOGGER.error("No valid entities were provided for the energy panel."); return
        lang = _get_lang(hass)
        small_screen = call.data[ATTR_SMALL_SCREEN]
        
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url

        async def send_to_device(uuid_val):
            device_data = coordinator.data.get(uuid_val, {})
            orientation = str(device_data.get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_energy_panel_url(hass, entity_states, orientation, lang, small_screen)
            final_url = _add_interactive_layer_to_url(
                hass=hass, data_url=content_url, back_url=back_url,
                add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
                click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
            )
            _LOGGER.info(f"Sending energy panel to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending panel to {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_ENERGY_PANEL, "status": status})

        await asyncio.gather(*(send_to_device(uuid) for uuid in uuids))

    async def handle_send_todo_list(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        todo_entity_id = call.data[ATTR_TODO_ENTITY]
        title = call.data.get(ATTR_TITLE)
        lang = _get_lang(hass)
        small_screen = call.data[ATTR_SMALL_SCREEN]
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

        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        
        async def send_to_device(uuid_val):
            device_data = coordinator.data.get(uuid_val, {})
            orientation = str(device_data.get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_todo_list_url(hass, title, items, lang, orientation, small_screen)
            final_url = _add_interactive_layer_to_url(
                hass=hass, data_url=content_url, back_url=back_url,
                add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
                click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
            )
            _LOGGER.info(f"Sending to-do list '{todo_entity_id}' to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending to-do list to {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_TODO_LIST, "status": status})
        
        await asyncio.gather(*(send_to_device(uuid) for uuid in uuids))

    async def handle_send_status_panel(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        title = call.data[ATTR_TITLE]
        entity_ids = call.data[ATTR_ENTITIES]
        lang = _get_lang(hass)
        small_screen = call.data[ATTR_SMALL_SCREEN]
        
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        
        async def send_to_device(uuid_val):
            device_data = coordinator.data.get(uuid_val, {})
            orientation = str(device_data.get("Config", {}).get("DisplayRotation", "0"))
            content_url = await create_status_panel_url(hass, title, entity_ids, lang, orientation, small_screen)
            final_url = _add_interactive_layer_to_url(
                hass=hass, data_url=content_url, back_url=back_url,
                add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
                click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
            )
            _LOGGER.info(f"Sending status panel to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending status panel to {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_STATUS_PANEL, "status": status})

        await asyncio.gather(*(send_to_device(uuid) for uuid in uuids))
    
    async def handle_set_display_rotation(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        rotation = call.data[ATTR_DISPLAY_ROTATION]
        for uuid_val in uuids:
            status = "failure"
            try:
                if await api.async_set_display_rotation(uuid_val, rotation) and await api.async_reboot_device(uuid_val): status = "success"; _LOGGER.info(f"Display rotation for {uuid_val} changed to: {rotation}")
            except Exception as e: _LOGGER.error(f"Error changing rotation for {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status, "params": {"display_rotation": rotation}})
        await coordinator.async_request_refresh()
        
    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        status = "failure"
        try:
            if await api.async_restart_sessions_batch(uuids):
                status = "success"
                _LOGGER.info(f"Session restart for {len(uuids)} devices has been requested.")
        except Exception as e:
            _LOGGER.error(f"Error restarting sessions: {e}")

        for uuid_val in uuids:
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_FORCE_REFRESH, "status": status})
            
    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        for uuid_val in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, blank_url): status = "success"; _LOGGER.info(f"Display for {uuid_val} has been cleared")
            except Exception as e: _LOGGER.error(f"Error clearing display for {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_CLEAR_DISPLAY, "status": status})
            
    async def handle_sleep_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        duration = call.data[ATTR_DURATION]
        sleep_url = f"data:text/html,<html><script>window.VECT = window.VECT || {{}}; window.VECT.setSleep({duration});</script></html>"
        for uuid_val in uuids:
            _LOGGER.info(f"Sending sleep command to {uuid_val} for {duration} seconds.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, sleep_url): status = "success"; _LOGGER.info(f"Device {uuid_val} has been put to sleep for {duration} seconds")
            except Exception as e: _LOGGER.error(f"Error putting {uuid_val} to sleep: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SLEEP_DEVICE, "status": status, "params": {"duration": duration}})
            
    async def handle_wake_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        wake_url = "data:text/html,<html><script>window.VECT = window.VECT || {}; window.VECT.setSleep(0);</script></html>"
        for uuid_val in uuids:
            _LOGGER.info(f"Sending wake command to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, wake_url): status = "success"; _LOGGER.info(f"Device {uuid_val} has been woken up")
            except Exception as e: _LOGGER.error(f"Error waking up {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_WAKE_DEVICE, "status": status})
            
    async def handle_send_qr_code(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        try:
            content_url = create_qr_code_url(qr_data=call.data[ATTR_DATA], message=call.data[ATTR_MESSAGE], qr_message_text_size=call.data[ATTR_QR_MESSAGE_TEXT_SIZE], qr_message_position=call.data[ATTR_QR_MESSAGE_POSITION], box_size=call.data[ATTR_BOX_SIZE], border=call.data[ATTR_BORDER], fill_color=call.data[ATTR_FILL_COLOR], back_color=call.data[ATTR_BACK_COLOR])
        except Exception as e: _LOGGER.error(f"Error generating QR code: {e}"); return
        
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        final_url = _add_interactive_layer_to_url(
            hass=hass,
            data_url=content_url,
            back_url=back_url,
            add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
            click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
            action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
        )

        for uuid_val in uuids:
            _LOGGER.info(f"Sending QR code to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, final_url): status = "success"; _LOGGER.info(f"QR code successfully sent to {uuid_val}")
            except Exception as e: _LOGGER.error(f"Error sending QR code to {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_QR_CODE, "status": status})
            
    async def handle_send_calendar(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        calendar_entity_id = call.data[ATTR_CALENDAR_ENTITY]
        duration_days = call.data[ATTR_DURATION_DAYS]
        style = call.data[ATTR_DISPLAY_STYLE]
        small_screen = call.data[ATTR_SMALL_SCREEN]
        now = dt_util.now()
        lang = _get_lang(hass)
        if style == "monthly_grid":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=duration_days)
        try:
            response_data = await hass.services.async_call("calendar", "get_events", {"entity_id": calendar_entity_id, "start_date_time": start_date.isoformat(), "end_date_time": end_date.isoformat()}, blocking=True, return_response=True)
            raw_events, events = response_data.get(calendar_entity_id, {}).get("events", []), []
            for event in raw_events:
                if not isinstance(event, dict): _LOGGER.debug(f"Skipped invalid event item: {event}"); continue
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
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        final_url = _add_interactive_layer_to_url(
            hass=hass,
            data_url=content_url,
            back_url=back_url,
            add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
            click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
            action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
        )

        for uuid_val in uuids:
            _LOGGER.info(f"Sending calendar '{calendar_entity_id}' to {uuid_val}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid_val, final_url): status = "success"; _LOGGER.info(f"Calendar sent to {uuid_val}")
            except Exception as e: _LOGGER.error(f"Error sending calendar to {uuid_val}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid_val, "service": SERVICE_SEND_CALENDAR, "status": status, "params": {"calendar": calendar_entity_id}})

    async def handle_send_camera_snapshot(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        camera_entity_id = call.data[ATTR_CAMERA_ENTITY]
        caption_template = call.data.get(ATTR_CAPTION, "")
        image_zoom = call.data.get(ATTR_IMAGE_ZOOM, 100)
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))
        
        if isinstance(caption_template, Template):
            caption_template.hass = hass
            caption = caption_template.async_render(parse_result=False)
        else: caption = caption_template
        try: image = await async_get_image(hass, camera_entity_id)
        except Exception as e: _LOGGER.error(f"Failed to get image from camera {camera_entity_id}: {e}"); return

        www_dir = Path(hass.config.path("www"))
        def _ensure_www():
            www_dir.mkdir(parents=True, exist_ok=True)
        await hass.async_add_executor_job(_ensure_www)

        image_filename = f"visionect_snapshot_{uuid.uuid4().hex}.jpg"
        image_path = www_dir / image_filename
        def _write_image():
            with open(image_path, "wb") as f: f.write(image.content)
        await hass.async_add_executor_job(_write_image)
        await _async_cleanup_media_files(hass)

        base_url = get_url(hass)
        image_url = f"{base_url}/local/{image_filename}"
        image_url = create_simple_cache_buster(image_url)
        
        content_url = create_text_message_url(message=caption, layout="image_top", image_url=image_url, text_size="24px", image_zoom=image_zoom, image_rotation=image_rotation)
        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        final_url = _add_interactive_layer_to_url(
            hass=hass, data_url=content_url, back_url=back_url,
            add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
            click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
            action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
        )

        for device_uuid in uuids:
            _LOGGER.info(f"Sending snapshot from '{camera_entity_id}' to {device_uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error while sending snapshot to {device_uuid}: {e}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_CAMERA_SNAPSHOT, "status": status, "params": {"camera_entity": camera_entity_id}})
    
    async def handle_send_sensor_graph(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        entity_ids = call.data[ATTR_ENTITIES]
        duration_hours = call.data[ATTR_DURATION_HOURS]
        graph_type = call.data[ATTR_GRAPH_TYPE]
        show_points = call.data[ATTR_SHOW_POINTS]
        image_zoom = call.data[ATTR_IMAGE_ZOOM]
        image_rotation = int(call.data.get(ATTR_DISPLAY_ROTATION, "0"))
        
        start_time = dt_util.now() - timedelta(hours=duration_hours)
        func_to_run = partial(history.get_significant_states, hass, start_time, entity_ids=entity_ids, significant_changes_only=False)
        history_data = await get_instance(hass).async_add_executor_job(func_to_run)

        main_menu_url = hass.data[DOMAIN].get("main_menu_url")
        back_url = call.data.get(ATTR_BACK_BUTTON_URL) or main_menu_url
        www_dir = Path(hass.config.path("www"))
        def _ensure_www():
            www_dir.mkdir(parents=True, exist_ok=True)
        await hass.async_add_executor_job(_ensure_www)

        for device_uuid in uuids:
            device_data = coordinator.data.get(device_uuid, {})
            config = device_data.get("Config", {})
            orientation = str(config.get("DisplayRotation", "0"))

            try:
                image_bytes = await hass.async_add_executor_job(_generate_graph_image, hass, history_data, entity_ids, graph_type, show_points, orientation)
            except Exception as e:
                _LOGGER.error(f"Failed to generate graph image for {device_uuid}: {e}")
                image_bytes = None

            if not image_bytes:
                lang = _get_lang(hass)
                msg = "Brak danych lub błąd generowania wykresu." if lang == "pl" else "No data or failed to generate the graph."
                content_url = f"data:text/html,{urllib.parse.quote(f'<!DOCTYPE html><html><head><meta charset=\"UTF-8\"></head><body style=\"display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;\"><div style=\"font-size:2em;text-align:center;\">{msg}</div></body></html>', safe='')}"
                final_url = _add_interactive_layer_to_url(
                    hass=hass, data_url=content_url, back_url=back_url,
                    add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
                    click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                    action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
                )
                _LOGGER.info(f"Sending no data message to {device_uuid}.")
                status = "failure"
                try:
                    if await api.async_set_device_url(device_uuid, final_url): status = "success"
                except Exception as e: _LOGGER.error(f"Error sending message to {device_uuid}: {e}")
                hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_SENSOR_GRAPH, "status": status, "params": {"entities": entity_ids}})
                continue

            image_filename = f"visionect_graph_{uuid.uuid4().hex}.png"
            image_path = www_dir / image_filename
            
            def _write_image():
                with open(image_path, "wb") as f: f.write(image_bytes)
            
            await hass.async_add_executor_job(_write_image)
            await _async_cleanup_media_files(hass)
            
            base_url = get_url(hass)
            image_url = f"{base_url}/local/{image_filename}"
            image_url = create_simple_cache_buster(image_url)
            
            content_url = create_text_message_url(message="", layout="image_only", image_url=image_url, image_zoom=image_zoom, image_rotation=image_rotation)
            final_url = _add_interactive_layer_to_url(
                hass=hass, data_url=content_url, back_url=back_url,
                add_back_button=call.data[ATTR_ADD_BACK_BUTTON],
                click_anywhere=call.data[ATTR_CLICK_ANYWHERE_TO_RETURN],
                action_webhook_id=call.data.get(ATTR_ACTION_WEBHOOK_ID),
            )
            
            _LOGGER.info(f"Sending graph with {entity_ids} to {device_uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(device_uuid, final_url): status = "success"
            except Exception as e: _LOGGER.error(f"Error sending graph to {device_uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": device_uuid, "service": SERVICE_SEND_SENSOR_GRAPH, "status": status, "params": {"entities": entity_ids}})

    # SERVICE REGISTRATION
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
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Visionect Joan config entry successfully initialized.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Visionect Joan integration.")
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DISPLAY_ROTATION)
    hass.services.async_remove(DOMAIN, SERVICE_FORCE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_DISPLAY)
    hass.services.async_remove(DOMAIN, SERVICE_SLEEP_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_SLEEP_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_WAKE_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_QR_CODE)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_CALENDAR)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_WEATHER)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_ENERGY_PANEL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TODO_LIST)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_CAMERA_SNAPSHOT)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_STATUS_PANEL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_SENSOR_GRAPH)
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Visionect Joan integration successfully unloaded.")
    else: _LOGGER.error("Error while unloading Visionect Joan integration.")
    return unload_ok
