# custom_components/visionect_joan/__init__.py
import logging
import time
import urllib.parse
import voluptuous as vol
import html
from datetime import datetime, timezone, timedelta
import io
import base64
import qrcode
import calendar
from pathlib import Path
import shutil

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, State, ServiceResponse, SupportsResponse
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID, UnitOfPower, UnitOfEnergy
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .api import VisionectAPI
from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY,
    SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE,
    NETWORK_RETRY_DELAY
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "text", "button", "select"]

VIEW_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Required("url"): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional("views", default=[]): vol.All(cv.ensure_list, [VIEW_SCHEMA]),
    })
}, extra=vol.ALLOW_EXTRA)

SERVICE_SET_URL = "set_url"
SERVICE_SEND_TEXT = "send_text"
SERVICE_SET_DISPLAY_ROTATION = "set_display_rotation"
SERVICE_SEND_CALENDAR = "send_calendar"
SERVICE_SEND_WEATHER = "send_weather"
SERVICE_SEND_ENERGY_PANEL = "send_energy_panel"
SERVICE_SEND_TODO_LIST = "send_todo_list"
EVENT_COMMAND_RESULT = f"{DOMAIN}_command_result"

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
ATTR_DAILY_VIEW_DURATION = "daily_view_duration"
ATTR_POWER_USAGE_ENTITY = "power_usage_entity"
ATTR_DAILY_CONSUMPTION_ENTITY = "daily_consumption_entity"
ATTR_DAILY_PRODUCTION_ENTITY = "daily_production_entity"
ATTR_DAILY_GRID_IMPORT_ENTITY = "daily_grid_import_entity"
ATTR_DAILY_GRID_EXPORT_ENTITY = "daily_grid_export_entity"
ATTR_TODO_ENTITY = "todo_entity"
ATTR_TITLE = "title"

EINK_COLORS = ["black", "white"]
FONT_WEIGHTS = ["normal", "bold"]
LAYOUT_OPTIONS = ["text_only", "image_top", "image_bottom", "image_left", "image_right"]

THEMED_FONTS = {
    "Nowoczesna": "'Trebuchet MS', Helvetica, sans-serif",
    "Czytelna": "Verdana, Geneva, sans-serif",
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
    vol.Optional(ATTR_FONT_FAMILY, default="Nowoczesna"): vol.In(list(THEMED_FONTS.keys())),
    vol.Optional(ATTR_FONT_WEIGHT, default="normal"): vol.In(FONT_WEIGHTS),
    vol.Optional(ATTR_LAYOUT, default="text_only"): vol.In(LAYOUT_OPTIONS),
    vol.Optional(ATTR_IMAGE_URL): cv.string,
    vol.Optional(ATTR_IMAGE_ZOOM, default=100): vol.All(vol.Coerce(int), vol.Range(min=50, max=200)),
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
})

SERVICE_SEND_CALENDAR_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_CALENDAR_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DURATION_DAYS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
    vol.Optional(ATTR_DISPLAY_STYLE, default="modern"): vol.In(["modern", "minimalist", "monthly_grid"]),
    vol.Optional(ATTR_DAILY_VIEW_DURATION, default=5): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
})

SERVICE_SEND_WEATHER_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_WEATHER_ENTITY): cv.entity_id,
    vol.Optional(ATTR_LAYOUT, default="detailed_summary"): vol.In([
        "detailed_summary", "daily_forecast_list", "current_large"
    ]),
})

SERVICE_SEND_ENERGY_PANEL_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Optional(ATTR_POWER_USAGE_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_CONSUMPTION_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_PRODUCTION_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_GRID_IMPORT_ENTITY): cv.entity_id,
    vol.Optional(ATTR_DAILY_GRID_EXPORT_ENTITY): cv.entity_id,
})

SERVICE_SEND_TODO_LIST_SCHEMA = SERVICE_DEVICE_SCHEMA.extend({
    vol.Required(ATTR_TODO_ENTITY): cv.entity_id,
    vol.Optional(ATTR_TITLE): cv.string,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Ustawia globalną konfigurację dla integracji z pliku YAML."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        hass.data[DOMAIN]["views"] = config[DOMAIN].get("views", [])
    else:
        hass.data[DOMAIN]["views"] = []
    return True

ICON_CACHE = {}

async def async_get_icon_as_base64(hass: HomeAssistant, icon_name: str) -> str:
    """Wczytuje ikonę SVG asynchronicznie i konwertuje ją do formatu data URL Base64."""
    if icon_name in ICON_CACHE:
        return ICON_CACHE[icon_name]
    
    icon_file = Path(__file__).parent / "svg" / icon_name
    
    if not icon_file.is_file():
        _LOGGER.warning(f"Nie znaleziono ikony: {icon_file}")
        return ""
    
    def _load_icon():
        """Synchronous icon loading function to be run in an executor."""
        try:
            with open(icon_file, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/svg+xml;base64,{encoded_string}"
        except Exception as e:
            _LOGGER.error(f"Błąd podczas kodowania ikony {icon_name}: {e}")
            return ""

    data_url = await hass.async_add_executor_job(_load_icon)
    if data_url:
        ICON_CACHE[icon_name] = data_url
    return data_url

async def create_todo_list_url(hass: HomeAssistant, title: str, items: list) -> str:
    """Asynchronicznie generuje URL data:text/html dla listy zadań."""

    style_css = """
        body { font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; }
        .header { text-align: center; font-size: 2.5em; font-weight: bold; border-bottom: 2px solid black; padding-bottom: 15px; margin-bottom: 20px; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { display: flex; align-items: center; font-size: 2.2em; padding: 15px 0; border-bottom: 1px solid #eee; }
        .icon { width: 1.2em; height: 1.2em; margin-right: 15px; flex-shrink: 0; }
        .summary { flex-grow: 1; }
        li.completed .summary { text-decoration: line-through; color: #888; }
        .no-tasks { text-align: center; font-size: 2em; padding-top: 50px; color: #888; }
    """

    icon_unchecked = await async_get_icon_as_base64(hass, "checkbox-blank-outline.svg")
    icon_checked = await async_get_icon_as_base64(hass, "checkbox-marked.svg")

    items_html = ""
    if not items:
        items_html = "<div class='no-tasks'>Brak zadań na liście</div>"
    else:
        # Sortowanie: niewykonane (needs_action) na górze, wykonane (completed) na dole
        sorted_items = sorted(items, key=lambda x: x.get('status', 'needs_action') == 'completed')
        
        for item in sorted_items:
            # Dla `todo` używamy 'summary', dla `shopping_list` 'name'
            summary = html.escape(item.get('summary') or item.get('name', 'Brak opisu'))
            # Dla `todo` status to 'status', dla `shopping_list` to 'complete'
            is_complete = item.get('status') == 'completed' or item.get('complete', False)
            
            if is_complete:
                icon_data = icon_checked
                css_class = "completed"
            else:
                icon_data = icon_unchecked
                css_class = ""
            
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

async def create_energy_panel_url(hass: HomeAssistant, states: dict[str, State | None]) -> str:
    """Asynchronicznie generuje URL data:text/html dla panelu energetycznego."""

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

    style_css = """
        body { font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; height: 100vh; width: 100vw; }
        .header { text-align: center; font-size: 2em; font-weight: bold; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 20px; }
        .main-stat { text-align: center; margin: 20px 0; }
        .main-stat .value { font-size: 8em; font-weight: bold; line-height: 1.1; }
        .main-stat .unit { font-size: 2em; opacity: 0.8; margin-left: 10px; }
        .main-stat .label { font-size: 1.8em; }
        .stats-grid { display: flex; flex-wrap: wrap; justify-content: space-around; width: 100%; flex-grow: 1; align-content: center; gap: 20px; }
        .stat-card { flex-basis: 45%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
        .stat-card .icon { width: 80px; height: 80px; margin-bottom: 10px; }
        .stat-card .value { font-size: 3em; font-weight: bold; }
        .stat-card .label { font-size: 1.5em; opacity: 0.8; }
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
            <div class="value">{get_state_val(power_usage_state, 0)}<span class="unit">{unit}</span></div>
            <div class="label">Aktualne zużycie</div>
        </div>
        """

    grid_html = ""
    
    if daily_production_state:
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['solar']}" class="icon" />
            <div class="value">{get_state_val(daily_production_state)} {UnitOfEnergy.KILO_WATT_HOUR}</div>
            <div class="label">Produkcja dzisiaj</div>
        </div>
        """
    
    if daily_import_state:
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['import']}" class="icon" />
            <div class="value">{get_state_val(daily_import_state)} {UnitOfEnergy.KILO_WATT_HOUR}</div>
            <div class="label">Pobrano z sieci</div>
        </div>
        """

    if daily_export_state:
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['export']}" class="icon" />
            <div class="value">{get_state_val(daily_export_state)} {UnitOfEnergy.KILO_WATT_HOUR}</div>
            <div class="label">Oddano do sieci</div>
        </div>
        """

    if daily_consumption_state:
        grid_html += f"""
        <div class="stat-card">
            <img src="{icons['home']}" class="icon" />
            <div class="value">{get_state_val(daily_consumption_state)} {UnitOfEnergy.KILO_WATT_HOUR}</div>
            <div class="label">Zużycie w domu</div>
        </div>
        """

    html_body = f"""
    <div class="header">Panel Energetyczny</div>
    {main_stat_html}
    <div class="stats-grid">{grid_html}</div>
    """

    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Panel Energetyczny</title><style>{style_css}</style></head><body>{html_body}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"


def create_qr_code_url(qr_data: str, message: str = "", qr_message_text_size: int = 24, qr_message_position: str = "below", box_size: int = 10, border: int = 4, fill_color: str = "black", back_color: str = "white") -> str:
    """Generuje kod QR i zwraca go jako URL z osadzonym obrazem i opcjonalnym tekstem."""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
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
        <body style="margin: 0; padding: 0; width: 100vw; height: 100vh; display: flex; flex-direction: {flex_direction}; align-items: center; justify-content: center; background-color: {back_color}; color: {fill_color};">
            <div><img src="{img_data_url}" /></div>
            {message_html}
        </body>
        </html>
        """
        encoded = urllib.parse.quote(html_content, safe='')
        return f"data:text/html,{encoded}"

    except Exception as e:
        _LOGGER.error(f"Błąd podczas generowania kodu QR: {e}")
        return "data:text/html,<html><body>Error generating QR code.</body></html>"

def create_calendar_list_view_html(events: list, style: str = "modern", add_back_button: bool = False) -> str:
    """Generuje fragment HTML dla widoku listy wydarzeń."""
    html_body_content = ""
    if add_back_button:
        html_body_content += '<a href="#" onclick="showView(\'monthly-view\'); return false;" class="back-button">&#x2190;</a>'

    if not events:
        html_body_content += '<div class="no-events">Brak wydarzeń tego dnia</div>'
    else:
        events_by_day = {}
        for event in events:
            if isinstance(event.get('start'), datetime):
                event_date = event['start'].date()
                if event_date not in events_by_day:
                    events_by_day[event_date] = []
                events_by_day[event_date].append(event)

        for event_date in sorted(events_by_day.keys()):
            html_body_content += f'<div class="date-header">{event_date.strftime("%A, %d %B")}</div>'
            
            for event in sorted(events_by_day[event_date], key=lambda x: x['start']):
                start_time = event['start'].strftime('%H:%M')
                summary = html.escape(event.get('summary', 'Brak tytułu'))
                location = html.escape(event.get('location', ''))
                
                html_body_content += f'''
                <div class="event">
                    <div class="time">{start_time}</div>
                    <div class="summary">{summary}</div>
                    {f'<div class="location">{location}</div>' if location else ''}
                </div>
                '''
    return html_body_content

def create_calendar_url(events: list, style: str = "modern") -> str:
    """Generuje pełny URL HTML dla widoku listy wydarzeń."""
    if style == "modern":
        style_css = """
            body { font-family: 'Trebuchet MS', sans-serif; background-color: white; color: black; margin: 0; padding: 20px; box-sizing: border-box; }
            .date-header { text-align: center; font-size: 1.5em; border-bottom: 2px solid black; padding-bottom: 10px; margin-top: 20px; margin-bottom: 15px; }
            .event { margin-bottom: 15px; padding: 10px; border-left: 5px solid black; background-color: #f9f9f9; }
            .time { font-weight: bold; font-size: 1.2em; }
            .summary { font-size: 1.1em; margin: 5px 0; }
            .location { font-style: italic; color: #555; }
            .no-events { text-align: center; font-size: 1.5em; padding-top: 50px; }
        """
    else: # minimalist
        style_css = """
            body { font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; }
            .date-header { font-size: 1.2em; font-weight: bold; margin-top: 25px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px;}
            .event { display: flex; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid #eee; }
            .time { flex: 0 0 100px; font-weight: bold; }
            .summary { flex-grow: 1; }
            .location { display: none; }
            .no-events { text-align: center; font-size: 1.2em; padding-top: 20%; }
        """
    
    html_body_content = create_calendar_list_view_html(events, style, add_back_button=False)
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Kalendarz</title><style>{style_css}</style></head><body>{html_body_content}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_monthly_calendar_url(year: int, month: int, events: list, daily_view_duration_seconds: int = 5) -> str:
    """Generuje URL data:text/html dla interaktywnego widoku miesięcznego."""
    
    style_css = """
        body { font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; }
        a { text-decoration: none; color: inherit; }
        
        #monthly-view { display: flex; flex-direction: column; height: calc(100vh - 50px); }
        .month-header { text-align: center; font-size: 2.8em; padding-bottom: 20px; }
        .calendar-grid { display: flex; flex-direction: column; flex-grow: 1; }
        .week-header, .week { display: flex; flex-grow: 1; }
        .day-name, .day-cell { flex-basis: 0; flex-grow: 1; text-align: center; display: flex; align-items: center; justify-content: center; }
        .day-name { font-weight: bold; font-size: 1.5em; }
        .day-cell { border-top: 1px solid #ccc; position: relative; font-size: 3.2em; font-weight: bold; cursor: pointer; }
        .day-cell.empty { background-color: #f8f8f8; cursor: default; }
        .day-cell a { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
        .day-cell .day-number { z-index: 1; }
        
        .day-cell.today .day-number {
            background-color: black;
            color: white;
            border-radius: 50%;
            width: 1.5em;
            height: 1.5em;
            line-height: 1.5em;
            display: inline-block;
        }

        .day-number.has-event {
            color: black;
            border: 3px solid black;
            border-radius: 50%;
            width: calc(1.5em - 6px);
            height: calc(1.5em - 6px);
            line-height: calc(1.5em - 6px);
            display: inline-block;
        }
        
        .daily-view-container { padding: 25px; }
        .back-button { font-size: 2.5em; text-decoration: none; color: black; position: absolute; top: 20px; left: 25px; cursor: pointer; }
        .date-header { text-align: center; font-size: 2.2em; border-bottom: 2px solid black; padding-bottom: 15px; margin-top: 25px; margin-bottom: 20px; }
        .event { margin-bottom: 20px; padding: 15px; border-left: 5px solid black; background-color: #f9f9f9; }
        .time { font-weight: bold; font-size: 1.8em; }
        .summary { font-size: 1.6em; margin: 8px 0; }
        .location { font-style: italic; color: #555; font-size: 1.4em;}
        .no-events { text-align: center; font-size: 2em; padding-top: 60px; }
    """
    
    timeout_ms = daily_view_duration_seconds * 1000
    js_back_timer_logic = f"backTimer = setTimeout(function() {{ showView('monthly-view'); }}, {timeout_ms});"
    if daily_view_duration_seconds == 0:
        js_back_timer_logic = "" 

    js_script = f"""
        var backTimer = null;
        function showView(viewId) {{
            if (backTimer) {{ clearTimeout(backTimer); }}
            
            document.getElementById('monthly-view').style.display = 'none';
            var dailyViews = document.getElementsByClassName('daily-view');
            for (var i = 0; i < dailyViews.length; i++) {{
                dailyViews[i].style.display = 'none';
            }}
            
            var viewToShow = document.getElementById(viewId);
            if (viewId === 'monthly-view') {{
                viewToShow.style.display = 'flex';
            }} else {{
                viewToShow.style.display = 'block';
                {js_back_timer_logic}
            }}
        }}
    """
    
    cal = calendar.Calendar()
    month_matrix = cal.monthdatescalendar(year, month)
    today = dt_util.now().date()
    
    event_dates = {e['start'].date() for e in events if isinstance(e.get('start'), datetime)}
    
    month_name = datetime(year, month, 1).strftime("%B %Y")
    monthly_view_html = f'<div id="monthly-view" style="display: flex; flex-direction: column; height: calc(100vh - 50px);">'
    monthly_view_html += f'<div class="month-header">{month_name}</div><div class="calendar-grid">'
    
    day_names = ["M", "T", "W", "T", "F", "S", "S"]
    monthly_view_html += '<div class="week-header">'
    for name in day_names:
        monthly_view_html += f'<div class="day-name">{name}</div>'
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

            if day_date == today:
                class_list.append("today")
            
            day_number_classes = ["day-number"]
            if day_date in event_dates and day_date != today:
                day_number_classes.append("has-event")
            
            day_number_html = f'<span class="{" ".join(day_number_classes)}">{day_date.day}</span>'
            
            view_id = f'view-{day_date.isoformat()}'
            events_for_day = [e for e in events if isinstance(e.get('start'), datetime) and e['start'].date() == day_date]
            daily_list_html = create_calendar_list_view_html(events_for_day, style="modern", add_back_button=True)
            daily_views_html += f'<div id="{view_id}" class="daily-view" style="display: none;"><div class="daily-view-container">{daily_list_html}</div></div>'
            
            monthly_view_html += f'<a href="#" onclick="showView(\'{view_id}\'); return false;" class="{" ".join(class_list)}">{day_number_html}</a>'

        monthly_view_html += '</div>'

    monthly_view_html += '</div></div>'
    
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Kalendarz Miesięczny</title><style>{style_css}</style><script>{js_script}</script></head><body>{monthly_view_html}{daily_views_html}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def wind_deg_to_direction(deg):
    """Konwertuje stopnie na kardynalny kierunek wiatru."""
    if deg is None:
        return ""
    try:
        deg = float(deg)
        dirs = ["Pn", "Pn-Wsch", "Wsch", "Pd-Wsch", "Pd", "Pd-Zach", "Zach", "Pn-Zach"]
        ix = round(deg / (360. / len(dirs)))
        return dirs[ix % len(dirs)]
    except (ValueError, TypeError):
        return ""

async def create_weather_url(
    hass: HomeAssistant, 
    weather_state: State, 
    daily_forecast: list | None,
    hourly_forecast: list | None,
    layout: str
) -> str:
    """Asynchronicznie generuje URL data:text/html dla widoku pogody."""
    
    state = weather_state.state
    attrs = weather_state.attributes
    
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
    
    style_css = """
        body { font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; display: flex; flex-direction: column; height: 100vh; width: 100vw; }
        .flex { display: flex; }
        .col { flex-direction: column; }
        .center { align-items: center; justify-content: center; }
        .space-around { justify-content: space-around; }
        .space-between { justify-content: space-between; }
        .icon { width: 1em; height: 1em; vertical-align: middle; }
        
        .current-large-temp { font-size: 12em; font-weight: bold; }
        .current-large-icon { width: 350px; height: 350px; }

        /* Detailed Summary Layout */
        .summary-header { width: 100%; padding-bottom: 15px; text-align: center; }
        .summary-main { display: flex; align-items: center; justify-content: center; margin-top: 10px; }
        .summary-main .temp { font-size: 10em; font-weight: bold; line-height: 1; }
        .summary-main .icon { width: 200px; height: 200px; margin-left: 25px; }
        .feels-like { font-size: 2.5em; opacity: 0.8; margin-top: -15px; }
        
        .summary-details { font-size: 2.2em; width: 100%; border-top: 2px solid black; border-bottom: 2px solid black; padding: 15px 0; margin: 20px 0; }
        .detail-item { flex-basis: 50%; text-align: center; padding: 8px 0; }
        .detail-item .icon { font-size: 1.2em; margin-right: 10px; }

        .hourly-forecast { width: 100%; margin-bottom: 20px; }
        .hourly-item { text-align: center; font-size: 2.2em; }
        .hourly-item .icon { width: 100px; height: 100px; }
        .hourly-item .temp { font-weight: bold; }

        .daily-list { width: 100%; flex-grow: 1; overflow: hidden; }
        .daily-item { display: flex; align-items: center; font-size: 2.5em; padding: 12px 0; border-bottom: 1px solid #ccc; }
        .daily-item:last-child { border-bottom: none; }
        .daily-item .day { flex: 0 0 140px; font-weight: bold; }
        .daily-item .icon { width: 80px; height: 80px; margin: 0 20px; }
        .daily-item .temps { flex-grow: 1; text-align: center; }
        .daily-item .precip { display: flex; align-items: center; justify-content: flex-end; flex: 0 0 140px; }
        .daily-item .precip .icon { width: 32px; height: 32px; margin-right: 10px; }

        /* Daily Forecast List Layout (kiedy jest samodzielnym widokiem) */
        .daily-list-standalone .daily-item { font-size: 2.8em; }
    """
    
    html_body = ""

    if layout == "current_large":
        temp = f"{round(attrs.get('temperature', 0))}&deg;"
        main_icon_url = await get_weather_icon(state)
        html_body = f'<div class="flex center" style="flex-grow: 1;"><img src="{main_icon_url}" class="current-large-icon" /><div class="current-large-temp">{temp}</div></div>'
    
    elif layout == "daily_forecast_list":
        html_body += '<div class="daily-list daily-list-standalone">'
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
            html_body += '<div style="font-size: 2em; text-align: center;">Brak danych prognozy dziennej.</div>'
        html_body += '</div>'

    else:
        temp = f"{round(attrs.get('temperature', 0))}&deg;"
        feels_like = f"{round(attrs.get('apparent_temperature', attrs.get('temperature', 0)))}&deg;"
        main_icon_url = await get_weather_icon(state)
        html_body += f"""
        <div class="summary-header">
            <div class="summary-main">
                <div class="temp">{temp}</div>
                <img src="{main_icon_url}" class="icon" />
            </div>
            <div class="feels-like">Odczuwalna: {feels_like}</div>
        </div>"""

        humidity = f"{attrs.get('humidity', 0)}%"
        wind_speed = f"{attrs.get('wind_speed', 0)} {attrs.get('wind_speed_unit', 'km/h')}"
        wind_dir = wind_deg_to_direction(attrs.get('wind_bearing'))
        pressure = f"{attrs.get('pressure', 0)} {attrs.get('pressure_unit', 'hPa')}"
        sunrise, sunset = "", ""
        if sun_state and sun_state.attributes.get('next_rising') and sun_state.attributes.get('next_setting'):
            sunrise_dt = dt_util.parse_datetime(sun_state.attributes['next_rising'])
            sunset_dt = dt_util.parse_datetime(sun_state.attributes['next_setting'])
            sunrise = f'<img src="{await async_get_icon_as_base64(hass, "wi-sunrise.svg")}" class="icon" /> {sunrise_dt.strftime("%H:%M")}'
            sunset = f'<img src="{await async_get_icon_as_base64(hass, "wi-sunset.svg")}" class="icon" /> {sunset_dt.strftime("%H:%M")}'

        html_body += f"""
        <div class="summary-details flex" style="flex-wrap: wrap;">
            <div class="detail-item">Wiatr: {wind_dir} {wind_speed}</div>
            <div class="detail-item">Ciśnienie: {pressure}</div>
            <div class="detail-item">Wilgotność: {humidity}</div>
            <div class="detail-item">{sunrise} / {sunset}</div>
        </div>"""

        html_body += '<div class="hourly-forecast flex space-around">'
        if hourly_forecast:
            for hour in hourly_forecast[:4]: 
                if not isinstance(hour, dict): continue
                hour_str = dt_util.parse_datetime(hour.get('datetime')).strftime("%H:00")
                hour_temp = f"{round(hour.get('temperature', 0))}&deg;"
                hour_icon = await get_weather_icon(hour.get('condition'))
                html_body += f"""
                <div class="hourly-item">
                    <div>{hour_str}</div><img src="{hour_icon}" class="icon" /><div class="temp">{hour_temp}</div>
                </div>"""
        else:
             html_body += '<div style="font-size: 1.5em;">Brak prognozy godzinowej</div>'
        html_body += '</div>'

        html_body += '<div class="daily-list">'
        if daily_forecast:
            for day in daily_forecast[:3]:
                if not isinstance(day, dict): continue
                day_name = dt_util.parse_datetime(day.get('datetime')).strftime("%a")
                temp_high = f"{round(day.get('temperature', 0))}&deg;"
                temp_low = f"{round(day.get('templow', 0))}&deg;"
                icon_url = await get_weather_icon(day.get('condition'))
                html_body += f"""
                <div class="daily-item">
                    <div class="day">{day_name}</div><img src="{icon_url}" class="icon" /><div class="temps">{temp_high} / {temp_low}</div>
                </div>"""
        html_body += '</div>'

    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Pogoda</title><style>{style_css}</style></head><body>{html_body}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_simple_cache_buster(url: str) -> str:
    """Tworzy cache buster zgodnie z najlepszymi praktykami Visionect."""
    timestamp = int(time.time())
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}&reload_timeout=300"

def create_text_message_url(message: str, text_color: str = "black", background_color: str = "white", text_size: str = "28px", text_align: str = "center", font_family_key: str = "Nowoczesna", font_weight: str = "normal", layout: str = "text_only", image_url: str = None, image_zoom: int = 100) -> str:
    """Tworzy URL z wiadomością tekstową zoptymalizowaną dla e-ink z ulepszonym error handling."""
    font_family_css = THEMED_FONTS.get(font_family_key, "'Trebuchet MS', sans-serif")
    font_import_rule = f"@import url('{GOOGLE_FONTS_IMPORT_URL}');"
    escaped_message = html.escape(message).replace('\n', '<br>')
    image_html = ""
    
    if layout != "text_only" and image_url:
        scale_factor = image_zoom / 100.0
        zoom_style = f"transform: scale({scale_factor}); image-rendering: pixelated;"
        image_html = f'<div class="image-container"><img src="{image_url}" style="{zoom_style}" onerror="console.log(\'Visionect: Failed to load image: {image_url}\'); this.style.display=\'none\';" /></div>'
    
    flex_direction = "column"
    if layout == "image_bottom": 
        flex_direction = "column-reverse"
    elif layout == "image_left": 
        flex_direction = "row"
    elif layout == "image_right": 
        flex_direction = "row-reverse"
    
    auto_retry_script = ""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Wiadomość E-ink</title>
    {auto_retry_script}
    <style>
        {font_import_rule}
        body {{ 
            font-family: {font_family_css}; 
            color: {text_color}; 
            background-color: {background_color}; 
            margin: 0; 
            padding: 0; 
            width: 100vw; 
            height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            text-align: {text_align}; 
            box-sizing: border-box; 
            -webkit-font-smoothing: none; 
            font-smooth: never; 
        }}
        .container {{ 
            display: flex; 
            flex-direction: {flex_direction}; 
            align-items: center; 
            justify-content: center; 
            width: 90%; 
            height: 90%; 
            gap: 20px; 
        }}
        .text-container {{ 
            font-size: {text_size}; 
            font-weight: {font_weight}; 
            line-height: 1.5; 
            word-wrap: break-word; 
            flex-shrink: 1; 
        }}
        .image-container {{ 
            flex-shrink: 0; 
            max-width: {'40%' if layout in ['image_left', 'image_right'] else '90%'}; 
            max-height: {'90%' if layout in ['image_left', 'image_right'] else '40%'}; 
            display: flex; 
            align-items: center; 
            justify-content: center;
        }}
        img {{ 
            max-width: 100%; 
            max-height: 100%; 
            object-fit: contain; 
        }}
        .timestamp {{ 
            position: absolute; 
            bottom: 10px; 
            right: 10px; 
            font-size: 16px; 
            opacity: 0.8; 
            font-family: 'Courier New', Courier, monospace; 
            font-weight: 700; 
        }}
    </style>
</head>
<body>
    <div class="container">
        {image_html if layout != 'text_only' else ''}
        <div class="text-container">{escaped_message}</div>
    </div>
    <div class="timestamp">{time.strftime("%Y-%m-%d %H:%M")}</div>
</body>
</html>"""
    
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja wpisu dla integracji Visionect Joan z ulepszonym error handling."""
    _LOGGER.info("Rozpoczynanie konfiguracji wpisu dla Visionect Joan.")
    
    api = VisionectAPI(
        hass, 
        entry.data[CONF_HOST], 
        entry.data.get(CONF_USERNAME), 
        entry.data.get(CONF_PASSWORD), 
        entry.data.get(CONF_API_KEY), 
        entry.data.get(CONF_API_SECRET)
    )
    
    if not await api.async_test_authentication():
        _LOGGER.error("Autentykacja nie powiodła się. Nie można załadować integracji.")
        return False

    async def async_update_data():
        """Aktualizuje dane urządzeń z ulepszoną obsługą błędów."""
        try:
            devices_summary = await api.async_get_all_devices()
            if not devices_summary: 
                _LOGGER.warning("Brak danych urządzeń z API")
                return {}
            
            data = {}
            for device_summary in devices_summary:
                uuid = device_summary.get("Uuid")
                if not uuid: 
                    _LOGGER.warning("Urządzenie bez UUID zostało pominięte")
                    continue
                    
                device_details = await api.async_get_device_data(uuid)
                if not device_details: 
                    _LOGGER.warning(f"Nie można pobrać szczegółów urządzenia {uuid}")
                    continue
                    
                final_data = device_details
                if "Config" not in final_data: 
                    final_data["Config"] = {}
                    
                device_name = device_summary.get("Options", {}).get("Name")
                if device_name and device_name.lower() not in UNKNOWN_STRINGS:
                    final_data["Config"]["Name"] = device_name
                    
                final_data["LastUpdated"] = datetime.now(timezone.utc)
                data[uuid] = final_data
                
            _LOGGER.debug(f"Zaktualizowano dane dla {len(data)} urządzeń")
            return data
            
        except Exception as e:
            _LOGGER.error(f"Błąd podczas aktualizacji danych: {e}")
            return {}

    coordinator = DataUpdateCoordinator(
        hass, 
        _LOGGER, 
        name=f"visionect_{entry.entry_id}", 
        update_method=async_update_data, 
        update_interval=SCAN_INTERVAL
    )
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {"api": api, "coordinator": coordinator}
    
    device_reg = dr.async_get(hass)

    async def get_uuids_from_call(call: ServiceCall) -> list[str]:
        """Pobiera UUID urządzeń z wywołania serwisu."""
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if isinstance(device_ids, str): 
            device_ids = [device_ids]
        
        uuids = []
        for device_id in device_ids:
            device_entry = device_reg.async_get(device_id)
            if device_entry and (uuid := next((i[1] for i in device_entry.identifiers if i[0] == DOMAIN), None)):
                uuids.append(uuid)
            else:
                _LOGGER.warning(f"Nie znaleziono UUID dla device_id: {device_id}")
        
        return uuids

    async def handle_set_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        original_url = call.data[ATTR_URL]
        
        if not original_url.strip():
            _LOGGER.error("Pusty URL został odrzucony")
            return
            
        url_with_buster = create_simple_cache_buster(original_url)
        
        for uuid in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, url_with_buster) and await api.async_restart_session(uuid): 
                    status = "success"
                    _LOGGER.info(f"URL dla {uuid} pomyślnie zmieniony na: {original_url}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas zmiany URL dla {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SET_URL, "status": status, "params": {"url": original_url}
            })
        
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        
        if isinstance(message_template, Template): 
            message_template.hass = hass
            
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        
        image_url = call.data.get(ATTR_IMAGE_URL)
        if image_url and call.data[ATTR_LAYOUT] != "text_only":
            if not api.validate_image_url(image_url):
                _LOGGER.warning(f"URL obrazka może nie być obsługiwany: {image_url}")
        
        data_url = create_text_message_url(
            message,
            call.data[ATTR_TEXT_COLOR],
            call.data[ATTR_BACKGROUND_COLOR],
            f"{call.data[ATTR_TEXT_SIZE]}px",
            call.data[ATTR_TEXT_ALIGN],
            call.data[ATTR_FONT_FAMILY],
            call.data[ATTR_FONT_WEIGHT],
            call.data[ATTR_LAYOUT],
            image_url,
            call.data.get(ATTR_IMAGE_ZOOM)
        )
        
        for uuid in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, data_url): 
                    status = "success"
                    _LOGGER.info(f"Tekst pomyślnie wysłany do {uuid}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wysyłania tekstu do {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SEND_TEXT, "status": status, "params": {"message": message}
            })
        
        await coordinator.async_request_refresh()

    async def handle_set_display_rotation(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        rotation = call.data[ATTR_DISPLAY_ROTATION]
        
        for uuid in uuids:
            status = "failure"
            try:
                if await api.async_set_display_rotation(uuid, rotation) and await api.async_reboot_device(uuid): 
                    status = "success"
                    _LOGGER.info(f"Orientacja ekranu dla {uuid} zmieniona na: {rotation}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas zmiany orientacji dla {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status, "params": {"display_rotation": rotation}
            })
        
        await coordinator.async_request_refresh()

    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        
        for uuid in uuids:
            status = "failure"
            try:
                if await api.async_restart_session(uuid): 
                    status = "success"
                    _LOGGER.info(f"Sesja dla {uuid} została zrestartowana")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas restartowania sesji dla {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_FORCE_REFRESH, "status": status})

    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        
        for uuid in uuids:
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, blank_url): 
                    status = "success"
                    _LOGGER.info(f"Ekran {uuid} został wyczyszczony")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas czyszczenia ekranu dla {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_CLEAR_DISPLAY, "status": status})

    async def handle_sleep_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        duration = call.data[ATTR_DURATION]
        
        sleep_url = f"data:text/html,<html><script>window.VECT = window.VECT || {{}}; window.VECT.setSleep({duration});</script></html>"
        
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie komendy uśpienia do {uuid} na {duration} sekund.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, sleep_url):
                    status = "success"
                    _LOGGER.info(f"Urządzenie {uuid} zostało uśpione na {duration} sekund")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas usypiania {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SLEEP_DEVICE, "status": status, "params": {"duration": duration}
            })

    async def handle_wake_device(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        
        wake_url = "data:text/html,<html><script>window.VECT = window.VECT || {}; window.VECT.setSleep(0);</script></html>"
        
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie komendy wybudzenia do {uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, wake_url):
                    status = "success"
                    _LOGGER.info(f"Urządzenie {uuid} zostało wybudzone")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wybudzania {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_WAKE_DEVICE, "status": status})

    async def handle_send_qr_code(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        
        try:
            qr_url = create_qr_code_url(
                qr_data=call.data[ATTR_DATA],
                message=call.data[ATTR_MESSAGE],
                qr_message_text_size=call.data[ATTR_QR_MESSAGE_TEXT_SIZE],
                qr_message_position=call.data[ATTR_QR_MESSAGE_POSITION],
                box_size=call.data[ATTR_BOX_SIZE],
                border=call.data[ATTR_BORDER],
                fill_color=call.data[ATTR_FILL_COLOR],
                back_color=call.data[ATTR_BACK_COLOR]
            )
        except Exception as e:
            _LOGGER.error(f"Błąd podczas generowania kodu QR: {e}")
            return
        
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie kodu QR do {uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, qr_url):
                    status = "success"
                    _LOGGER.info(f"Kod QR pomyślnie wysłany do {uuid}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wysyłania kodu QR do {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_SEND_QR_CODE, "status": status})

    async def handle_send_calendar(call: ServiceCall):
        """Obsługuje wysyłanie widoku kalendarza."""
        uuids = await get_uuids_from_call(call)
        calendar_entity_id = call.data[ATTR_CALENDAR_ENTITY]
        duration_days = call.data[ATTR_DURATION_DAYS]
        style = call.data[ATTR_DISPLAY_STYLE]
        daily_view_duration = call.data[ATTR_DAILY_VIEW_DURATION]
        
        now = dt_util.now()
        
        if style == "monthly_grid":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = (start_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            end_date = end_of_month
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=duration_days)
        
        try:
            response_data = await hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "entity_id": calendar_entity_id,
                    "start_date_time": start_date.isoformat(),
                    "end_date_time": end_date.isoformat(),
                },
                blocking=True,
                return_response=True,
            )
            
            raw_events = response_data.get(calendar_entity_id, {}).get("events", [])
            
            events = []
            for event in raw_events:
                if not isinstance(event, dict):
                    _LOGGER.debug(f"Pominięto nieprawidłowy element w danych kalendarza: {event}")
                    continue

                start_info = event.get('start')
                end_info = event.get('end')
                
                start_str = None
                if isinstance(start_info, dict):
                    start_str = start_info.get('dateTime') or start_info.get('date')
                elif isinstance(start_info, str):
                    start_str = start_info

                end_str = None
                if isinstance(end_info, dict):
                    end_str = end_info.get('dateTime') or end_info.get('date')
                elif isinstance(end_info, str):
                    end_str = end_info

                if start_str:
                    event['start'] = dt_util.parse_datetime(start_str)
                if end_str:
                    event['end'] = dt_util.parse_datetime(end_str)
                
                if 'start' in event:
                    events.append(event)

        except Exception as e:
            _LOGGER.error(f"Błąd podczas pobierania wydarzeń z kalendarza {calendar_entity_id}: {e}")
            return
            
        if style == "monthly_grid":
            calendar_url = create_monthly_calendar_url(now.year, now.month, events, daily_view_duration)
        else:
            calendar_url = create_calendar_url(events, style)
        
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie kalendarza '{calendar_entity_id}' do {uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, calendar_url):
                    status = "success"
                    _LOGGER.info(f"Kalendarz pomyślnie wysłany do {uuid}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wysyłania kalendarza do {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, 
                "service": SERVICE_SEND_CALENDAR, 
                "status": status,
                "params": {"calendar": calendar_entity_id}
            })

    async def handle_send_weather(call: ServiceCall):
        """Obsługuje wysyłanie widoku pogody."""
        uuids = await get_uuids_from_call(call)
        weather_entity_id = call.data[ATTR_WEATHER_ENTITY]
        layout = call.data[ATTR_LAYOUT]

        weather_state = hass.states.get(weather_entity_id)
        if not weather_state:
            _LOGGER.error(f"Nie można znaleźć encji pogody: {weather_entity_id}")
            return
            
        daily_forecast, hourly_forecast = None, None
        
        try:
            daily_response: ServiceResponse = await hass.services.async_call(
                "weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "daily"},
                blocking=True, return_response=True
            )
            if daily_response:
                daily_forecast = daily_response.get(weather_entity_id, {}).get("forecast", [])
        except Exception as e:
            _LOGGER.warning(f"Nie udało się pobrać prognozy dziennej dla {weather_entity_id}: {e}")

        try:
            hourly_response: ServiceResponse = await hass.services.async_call(
                "weather", "get_forecasts", {"entity_id": weather_entity_id, "type": "hourly"},
                blocking=True, return_response=True
            )
            if hourly_response:
                hourly_forecast = hourly_response.get(weather_entity_id, {}).get("forecast", [])
        except Exception as e:
             _LOGGER.warning(f"Nie udało się pobrać prognozy godzinowej dla {weather_entity_id}: {e}")

        weather_url = await create_weather_url(hass, weather_state, daily_forecast, hourly_forecast, layout)

        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie pogody '{weather_entity_id}' do {uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, weather_url):
                    status = "success"
                    _LOGGER.info(f"Pogoda pomyślnie wysłana do {uuid}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wysyłania pogody do {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid,
                "service": SERVICE_SEND_WEATHER,
                "status": status,
                "params": {"weather_entity": weather_entity_id}
            })

    async def handle_send_energy_panel(call: ServiceCall):
        """Obsługuje wysyłanie widoku panelu energetycznego."""
        uuids = await get_uuids_from_call(call)
        
        entity_states = {
            key: hass.states.get(entity_id)
            for key, entity_id in call.data.items()
            if key.endswith("_entity") and entity_id
        }

        if not any(entity_states.values()):
            _LOGGER.error("Nie podano żadnych prawidłowych encji dla panelu energetycznego.")
            return

        energy_url = await create_energy_panel_url(hass, entity_states)

        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie panelu energetycznego do {uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, energy_url):
                    status = "success"
                    _LOGGER.info(f"Panel energetyczny pomyślnie wysłany do {uuid}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wysyłania panelu energetycznego do {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid,
                "service": SERVICE_SEND_ENERGY_PANEL,
                "status": status
            })

    async def handle_send_todo_list(call: ServiceCall):
        """Obsługuje wysyłanie widoku listy zadań."""
        uuids = await get_uuids_from_call(call)
        todo_entity_id = call.data[ATTR_TODO_ENTITY]
        title = call.data.get(ATTR_TITLE)

        if not title:
            todo_state = hass.states.get(todo_entity_id)
            title = todo_state.name if todo_state else "Lista Zadań"

        items = []
        try:
            # `todo.get_items` działa zarówno dla `todo`, jak i dla `shopping_list`
            response: ServiceResponse = await hass.services.async_call(
                "todo", "get_items", {"entity_id": todo_entity_id},
                blocking=True, return_response=True
            )
            if response:
                items = response.get(todo_entity_id, {}).get("items", [])
        except Exception as e:
            _LOGGER.error(f"Nie udało się pobrać zadań z listy {todo_entity_id}: {e}")
            return
        
        todo_list_url = await create_todo_list_url(hass, title, items)

        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie listy zadań '{todo_entity_id}' do {uuid}.")
            status = "failure"
            try:
                if await api.async_set_device_url(uuid, todo_list_url):
                    status = "success"
                    _LOGGER.info(f"Lista zadań pomyślnie wysłana do {uuid}")
            except Exception as e:
                _LOGGER.error(f"Błąd podczas wysyłania listy zadań do {uuid}: {e}")
            
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid,
                "service": SERVICE_SEND_TODO_LIST,
                "status": status,
                "params": {"todo_entity": todo_entity_id}
            })

    # Rejestracja serwisów
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
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Wpis konfiguracyjny dla Visionect Joan został pomyślnie zainicjalizowany.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Wyładowuje wpis konfiguracyjny."""
    _LOGGER.info("Wyładowywanie integracji Visionect Joan.")
    
    # Usunięcie serwisów
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DISPLAY_ROTATION)
    hass.services.async_remove(DOMAIN, SERVICE_FORCE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_DISPLAY)
    hass.services.async_remove(DOMAIN, SERVICE_SLEEP_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_WAKE_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_QR_CODE)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_CALENDAR)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_WEATHER)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_ENERGY_PANEL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TODO_LIST)
    
    # Wyładowanie platform
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Integracja Visionect Joan została pomyślnie wyładowana.")
    else:
        _LOGGER.error("Błąd podczas wyładowywania integracji Visionect Joan.")
    
    return unload_ok