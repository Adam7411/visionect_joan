import logging
import time
import urllib.parse
import html
import re
from datetime import datetime, timezone, timedelta, date
import io
import base64
import qrcode
import calendar
import json
from pathlib import Path

# matplotlib for graphs (headless)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cycler import cycler

# Network URLs
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url
try:
    # Newer Home Assistant
    from homeassistant.helpers.network import get_internal_url
except ImportError:
    # Older Home Assistant, where get_internal_url doesn't exist
    get_internal_url = None

from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfPower, UnitOfEnergy

from .const import UNKNOWN_STRINGS, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Local constants
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

_PL_DAY_NAMES = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
_EN_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_PL_DAY_ABBR = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
_EN_DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_PL_MONTH_NAMES = ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"]
_EN_MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

ICON_CACHE = {}

def _get_attr_as_float(attributes, key, default=0.0):
    val = attributes.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
        
def _get_lang(hass) -> str:
    try:
        # Check for manual override in integration options
        if DOMAIN in hass.data and "tablet_language" in hass.data[DOMAIN]:
            override = hass.data[DOMAIN]["tablet_language"]
            if override == "pl":
                return "pl"
            if override == "en":
                return "en"
        
        # Fallback to HA system language
        lang = (hass.config.language or "en").lower()
        return "pl" if lang.startswith("pl") else "en"
    except Exception:
        return "en"

async def async_get_icon_as_base64(hass, icon_name: str) -> str:
    if not icon_name:
        return ""
    
    cache_key = f"icon::{icon_name}"
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]
        
    base_dir = Path(__file__).parent
    
    # Check svg_button first (for button panel), then svg (general)
    possible_paths = [
        base_dir / "svg_button" / icon_name,
        base_dir / "svg" / icon_name
    ]
    
    icon_file = None
    for path in possible_paths:
        if path.is_file():
            icon_file = path
            break
            
    if not icon_file:
        _LOGGER.warning(f"Icon file not found: {icon_name}, using default.")
        default_icon_file = base_dir / "svg" / "default.svg"
        if not default_icon_file.is_file():
            _LOGGER.error("Even the default icon (default.svg) is missing!")
            return ""
        icon_file = default_icon_file

    def _load_icon():
        try:
            with open(icon_file, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/svg+xml;base64,{encoded_string}"
        except Exception as e:
            _LOGGER.error(f"Error encoding icon {icon_name}: {e}")
            return ""
            
    data_url = await hass.async_add_executor_job(_load_icon)
    if data_url:
        ICON_CACHE[cache_key] = data_url
    return data_url

async def _get_icon_filename_for_entity(state) -> str:
    device_class = state.attributes.get("device_class")
    domain = state.domain
    entity_id = state.entity_id.lower()
    is_on_state = state.state in ["on", "open", "unlocked", "armed", "armed_away", "armed_home", "playing"]
    if device_class == "door":
        return "door-open.svg" if is_on_state else "door-closed.svg"
    if device_class == "window":
        return "window-open.svg" if is_on_state else "window-closed.svg"
    if device_class == "lock":
        return "lock-open.svg" if is_on_state else "lock.svg"
    if domain == "cover" or "roleta" in entity_id or "blinds" in entity_id:
        return "blinds-open.svg" if is_on_state else "blinds-closed.svg"
    if domain == "light":
        return "light-on.svg" if is_on_state else "light-off.svg"
    if device_class in ["power", "switch", "plug"]:
        return "power-plug.svg"
    if device_class == "timestamp":
        return "clock.svg"
    if domain == "person" or domain == "device_tracker":
        return "account.svg"
    if domain == "camera":
        return "camera.svg"
    if domain == "weather":
        return "weather.svg"
    if domain == "media_player":
        return "speaker.svg"
    if domain == "update":
        return "update.svg"
    # POPRAWKA: Dodanie obsługi czujników bezpieczeństwa
    if device_class == "gas":
        return "fire-circle.svg"
    if device_class == "smoke":
        return "smoke-detector.svg"
    if device_class in ["moisture", "water", "leak"]:
        return "water-alert.svg"
    if device_class == "safety":
        return "shield-check.svg" if is_on_state else "shield-off.svg"
    # Dodatkowe mapowania po ID encji
    if "drzwi" in entity_id:
        return "door-open.svg" if is_on_state else "door-closed.svg"
    if "okno" in entity_id:
        return "window-open.svg" if is_on_state else "window-closed.svg"
    if "brama" in entity_id:
        return "gate.svg"
    if "ruch" in entity_id:
        return "motion-sensor.svg"
    if "swiatlo" in entity_id or "lampa" in entity_id or "led" in entity_id:
        return "light-on.svg" if is_on_state else "light-off.svg"
    if "zamek" in entity_id:
        return "lock-open.svg" if is_on_state else "lock.svg"
    if "wilgotnosc" in entity_id:
        return "humidity.svg"
    if "temperatury" in entity_id:
        return "temperature.svg"
    if "energia" in entity_id or "energy" in entity_id or "fazy" in entity_id:
        return "energy.svg"
    if "licznik" in entity_id:
        return "counter.svg"
    if "gniazdko" in entity_id:
        return "power-plug.svg"
    if "alarm" in entity_id:
        return "shield-check.svg" if is_on_state else "shield-off.svg"
    if "czas" in entity_id or "time" in entity_id:
        return "clock.svg"
    if "kamera" in entity_id:
        return "camera.svg"
    if "glosnik" in entity_id or "speaker" in entity_id or "radio" in entity_id:
        return "speaker.svg"
    if "tv" in entity_id or "telewizor" in entity_id:
        return "television.svg"
    if "pralka" in entity_id or "washing" in entity_id:
        return "washing-machine.svg"
    if "suszarka" in entity_id or "dryer" in entity_id:
        return "tumble-dryer.svg"
    if "zmywarka" in entity_id or "dishwasher" in entity_id:
        return "dishwasher.svg"
    if "piec" in entity_id or "kociol" in entity_id or "boiler" in entity_id:
        return "fire-circle.svg"
    if "zawor" in entity_id or "valve" in entity_id:
        return "valve.svg"
    if "pompa" in entity_id or "pump" in entity_id:
        return "pump.svg"
    if "hydrofor" in entity_id or "woda" in entity_id:
        return "water-pump.svg"
    if "gaz" in entity_id:
        return "fire-circle.svg"
    if "klima" in entity_id or "ac" in entity_id:
        return "air-conditioner.svg"
    if "wentylator" in entity_id or "fan" in entity_id:
        return "fan.svg"
    if "rekuperator" in entity_id or "reku" in entity_id:
        return "air-filter.svg"
    if "grzejnik" in entity_id or "radiator" in entity_id:
        return "radiator.svg"
    if "wifi" in entity_id:
        return "wifi.svg"
    if "zigbee" in entity_id:
        return "zigbee.svg"
    if "ip" in entity_id and "adres" in entity_id:
        return "ip-network-outline.svg"
    if device_class == "smoke":
        return "smoke-detector.svg"
    if device_class == "moisture":
        return "water-alert.svg"
    # POPRAWKA: Dodanie mapowań po entity_id dla czujników bezpieczeństwa
    if "dym" in entity_id or "smoke" in entity_id:
        return "smoke-detector.svg"
    if "zalanie" in entity_id or "wyciek" in entity_id or "leak" in entity_id:
        return "water-alert.svg"
    if "gaz" in entity_id:
        return "fire-circle.svg"
    if domain == "sensor":
        return "gauge.svg"
    return "default.svg"

def _format_long_date(d: date, lang: str) -> str:
    if lang == "pl":
        return f"{_PL_DAY_NAMES[d.weekday()]}, {d.day} {_PL_MONTH_NAMES[d.month-1]}"
    return f"{_EN_DAY_NAMES[d.weekday()]}, {d.day} {_EN_MONTH_NAMES[d.month-1]}"

async def _add_interactive_layer_to_url(
    hass, data_url: str, back_url: str | None, add_back_button: bool,
    click_anywhere: bool, click_anywhere_to_action: bool, 
    action_webhook_id: str | None, action_webhook_2_id: str | None,
    auto_return_seconds: int = 0
) -> str:
    """
    Adds an interactive layer with buttons and overlays.
    """
    # First, determine if any interactive elements are requested AT ALL.
    has_back_button = add_back_button and back_url
    has_webhook_1 = bool(action_webhook_id)
    has_webhook_2 = bool(action_webhook_2_id)
    has_click_anywhere = click_anywhere or click_anywhere_to_action
    
    # If no interactive elements are needed, but mamy auto-return -> też potrzebujemy skrypt
    if not (has_back_button or has_webhook_1 or has_webhook_2 or has_click_anywhere or auto_return_seconds > 0):
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

        any_button_defined = has_back_button or has_webhook_1 or has_webhook_2
        show_bar_and_padding = not (click_anywhere_to_action or click_anywhere) and any_button_defined
        
        padding_css = "padding-bottom: 120px !important;" if show_bar_and_padding else ""
        
        icon_back_svg = await async_get_icon_as_base64(hass, "arrow-left.svg")
        icon_action1_svg = await async_get_icon_as_base64(hass, "arrow-right.svg")
        icon_action2_svg = await async_get_icon_as_base64(hass, "check-circle.svg")
        
        # --- LOGIKA UKRYWANIA DATY ---
        timestamp_css = ""
        if has_webhook_1: # Jeśli jest prawy przycisk, ukrywamy datę
            timestamp_css = ".timestamp { display: none !important; }"
        # -----------------------------

        common_css = f"""
        html {{ box-sizing: border-box; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin: 0; width: 100vw; height: 100vh; {padding_css} }}

        .visionect-button-bar {{
            position: absolute; bottom: 0; left: 0; right: 0;
            height: 100px;
            display: flex;
            align-items: stretch;
            justify-content: space-around;
            padding: 0;
            background-color: rgba(255, 255, 255, 0.8);
            border-top: 2px solid #000;
        }}
        
        .button-area {{
            flex: 1;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
        }}
        .button-area:active {{
            background-color: rgba(0, 0, 0, 0.1);
        }}

        .icon-display {{
            width: 70px; height: 70px;
            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;
            pointer-events: none;
        }}
        
        .icon-back {{ background-image: url('{icon_back_svg}'); }}
        .icon-action1 {{ background-image: url('{icon_action1_svg}'); }}
        .icon-action2 {{ background-image: url('{icon_action2_svg}'); }}

        #visionect-click-overlay {{
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw; height: 100vh; z-index: 999; background: transparent; cursor: pointer;
        }}
        
        {timestamp_css}
        """

        if re.search(r"</style>", decoded_html, re.IGNORECASE):
            decoded_html = re.sub(r"</style>", common_css + "</style>", decoded_html, count=1, flags=re.IGNORECASE)
        else:
            decoded_html = re.sub(r"</head>", f"<style>{common_css}</style></head>", decoded_html, count=1, flags=re.IGNORECASE)

        def get_webhook_url(webhook_id):
            if not webhook_id:
                return None
            base_url = None
            try:
                base_url = get_internal_url(hass) if get_internal_url else get_url(hass)
            except Exception:
                base_url = None
            
            if not base_url:
                base_url = "http://homeassistant.local:8123"  # Fallback
            
            return f"{base_url.rstrip('/')}/api/webhook/{webhook_id}"

        webhook_url_1 = get_webhook_url(action_webhook_id)
        webhook_url_2 = get_webhook_url(action_webhook_2_id)

        buttons_html = ""
        if show_bar_and_padding:
            back_slot = '<div class="button-area"></div>'
            action2_slot = '<div class="button-area"></div>'
            action1_slot = '<div class="button-area"></div>'

            if has_back_button:
                back_slot = f'<div class="button-area" onclick="navigate(event, \'{back_url}\')"><div class="icon-display icon-back"></div></div>'
            
            if webhook_url_2:
                action2_slot = f'<div class="button-area" onclick="triggerWebhook(event, \'{webhook_url_2}\')"><div class="icon-display icon-action2"></div></div>'

            if webhook_url_1:
                action1_slot = f'<div class="button-area" onclick="triggerWebhook(event, \'{webhook_url_1}\')"><div class="icon-display icon-action1"></div></div>'
            
            buttons_html = f'<div class="visionect-button-bar">{back_slot}{action2_slot}{action1_slot}</div>'

        if buttons_html:
            decoded_html = re.sub(r"(<body\b[^>]*>)", r"\1" + buttons_html, decoded_html, count=1, flags=re.IGNORECASE)
        
        interactive_scripts = ""
        js_needs_navigate = (has_back_button) or (click_anywhere and back_url) or (auto_return_seconds and back_url)
        js_needs_webhook = (has_webhook_1 or has_webhook_2) or (click_anywhere_to_action and webhook_url_1) or (auto_return_seconds and click_anywhere_to_action and webhook_url_1)

        if js_needs_navigate:
             interactive_scripts += "function navigate(e,u){try{if(e)e.stopPropagation();window.location.href=u;}catch(err){}}"
        
        if js_needs_webhook:
            interactive_scripts += """
            var __vectLock = false;
            function triggerWebhook(e,u){
              try{
                if(e) e.stopPropagation();
                if(__vectLock) return;
                __vectLock = true;
                fetch(u,{
                  method:'POST',
                  headers:{'Content-Type':'application/json'},
                  body:'{}'
                }).catch(function(){}).finally(function(){
                  setTimeout(function(){ __vectLock = false; }, 800);
                });
              }catch(err){}
            }"""

        overlay_html = ""
        if click_anywhere_to_action and webhook_url_1:
            overlay_html = f'<div id="visionect-click-overlay" onclick="triggerWebhook(event, \'{webhook_url_1}\')"></div>'
        elif click_anywhere and back_url:
            overlay_html = f'<div id="visionect-click-overlay" onclick="navigate(event, \'{back_url}\')"></div>'

        if overlay_html:
            decoded_html = re.sub(r"(<body\b[^>]*>)", r"\1" + overlay_html, decoded_html, count=1, flags=re.IGNORECASE)

        # Auto return
        if auto_return_seconds and auto_return_seconds > 0:
            if click_anywhere_to_action and webhook_url_1:
                interactive_scripts += f"setTimeout(function(){{ try{{ triggerWebhook(null, '{webhook_url_1}'); }}catch(e){{}} }}, {int(auto_return_seconds)*1000});"
            elif back_url:
                interactive_scripts += f"setTimeout(function(){{ try{{ navigate(null, '{back_url}'); }}catch(e){{}} }}, {int(auto_return_seconds)*1000});"

        if interactive_scripts:
            script_html = f"<script>{interactive_scripts}</script>"
            decoded_html = re.sub(r"</body>", script_html + "</body>", decoded_html, count=1, flags=re.IGNORECASE)

        return f"{header},{urllib.parse.quote(decoded_html, safe='')}"
    except Exception as e:
        _LOGGER.error(f"Failed to add interactive layer to URL: {e}")
        return data_url

async def create_status_panel_url(hass, title: str, entity_ids: list[str], lang: str, orientation: str, small_screen: bool) -> str:
    STATE_TRANSLATIONS_PL = { "on": "Włączone", "off": "Wyłączone", "open": "Otwarte", "closed": "Zamknięte", "home": "w Domu", "not_home": "Poza domem", "locked": "Zamknięte", "unlocked": "Otwarte", "unavailable": "Niedostępny", "unknown": "Nieznany", }
    STATE_TRANSLATIONS_EN = { "on": "On", "off": "Off", "open": "Open", "closed": "Closed", "home": "Home", "not_home": "Away", "locked": "Locked", "unlocked": "Unlocked", "unavailable": "Unavailable", "unknown": "Unknown", }
    translations = STATE_TRANSLATIONS_PL if lang == "pl" else STATE_TRANSLATIONS_EN
    
    header_fs = "2.4em" if small_screen else "2.8em"
    grid_fs = "1.6em" if small_screen else "1.8em"
    
    style_css = f""" body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: white; color: black; margin: 0; padding: 30px; box-sizing: border-box; }} .header {{ text-align: center; font-size: {header_fs}; font-weight: bold; border-bottom: 3px solid black; padding-bottom: 20px; margin-bottom: 25px; }} .grid {{ display: grid; grid-template-columns: auto 1fr auto; gap: 20px 15px; align-items: center; font-size: {grid_fs}; }} .icon {{ width: 1.5em; height: 1.5em; }} .name {{ text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }} .state {{ text-align: right; font-weight: bold; }} .state-active {{ color: #d32f2f; }} """
    items_html = ""
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if not state:
            continue

        name = state.attributes.get('friendly_name', entity_id)
        icon_filename = await _get_icon_filename_for_entity(state)
        icon_data_url = await async_get_icon_as_base64(hass, icon_filename)

        unit = state.attributes.get('unit_of_measurement', '')
        raw = state.state

        display_state_val = None
        try:
            val = float(raw)
            if float(val).is_integer():
                fmt_val = f"{int(val)}"
            else:
                fmt_val = f"{val:.1f}"
            display_state_val = f"{fmt_val} {unit}" if unit else fmt_val
        except (ValueError, TypeError):
            low = str(raw).lower() if isinstance(raw, str) else raw
            display_state_val = translations.get(low, raw)
            if unit:
                display_state_val = f"{display_state_val} {unit}"

        state_class = "state-active" if state.state in ["on", "open", "unlocked", "problem", "detected", "arming", "armed", "armed_away", "armed_home"] else ""
        items_html += f""" <img src="{icon_data_url}" class="icon" /> <div class="name">{html.escape(name)}</div> <div class="state {state_class}">{html.escape(str(display_state_val))}</div> """

    html_body = f""" <div class="header">{html.escape(title)}</div> <div class="grid">{items_html}</div> """
    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style_css}</style></head><body>{html_body}{cache_buster_comment}</body></html>'
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
        # ZMIANA: Usunięto wszelkie paddingi, ustawiono viewport na 100vw/100vh
        # display: block usuwa dolny margines dla obrazków inline
        style_css = f"""
            body {{ 
                margin: 0; 
                padding: 0; 
                width: 100vw; 
                height: 100vh; 
                background-color: {background_color}; 
                overflow: hidden; 
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            img {{ 
                width: 100%; 
                height: 100%; 
                object-fit: fill; /* ZMIANA: fill wymusi rozciągnięcie, contain zachowa proporcje ale może zostawić paski */
                display: block;
                {transform_style} 
            }}
        """
        body_html = f'<img src="{image_url}" />'
    else:
        # Prepare image style based on layout and zoom
        img_style = f"transform: rotate({image_rotation}deg);"
        # For vertical layouts, width percentage works best for zoom
        # For horizontal layouts, we might need more care, but let's prioritize vertical as requested
        if layout in ["image_top", "image_bottom"]:
            img_style += f" width: {image_zoom}%; height: auto;"
        else:
            img_style += f" max-width: {'45%' if layout in ['image_left', 'image_right'] else '100%'}; max-height: 100%;"
            if image_zoom != 100: # Scale still useful for horizontal or as fallback
                img_style += f" transform: scale({image_zoom/100.0}) rotate({image_rotation}deg);"

        image_html = f'<img src="{image_url}" class="main-image" style="{img_style}" />' if layout != "text_only" and image_url else ""
        flex_direction = "column"
        if layout == "image_bottom": flex_direction = "column-reverse"
        elif layout == "image_left": flex_direction = "row"
        elif layout == "image_right": flex_direction = "row-reverse"
        
        style_css = f"""
            {font_import_rule}
            body {{ font-family: {font_family_css}; color: {text_color}; background-color: {background_color}; margin: 0; padding: 0; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; text-align: {text_align}; box-sizing: border-box; -webkit-font-smoothing: none; font-smooth: never; overflow: hidden; }}
            
            .container {{ display: flex; flex-direction: {flex_direction}; align-items: center; justify-content: center; max-width: 100%; max-height: 100%; gap: 0px; }}
            
            .text-container {{ font-size: {text_size}; font-weight: {font_weight}; line-height: 1.2; word-wrap: break-word; padding: 5px; }}
            
            .main-image {{ 
                flex-shrink: 0;
                object-fit: contain;
                display: block;
            }}
        """
        body_html = f"""
            <div class="container">
                {image_html}
                <div class="text-container">{escaped_message}</div>
            </div>
        """

    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style_css}</style></head><body>{body_html}{cache_buster_comment}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_todo_list_url(
    hass,
    title: str,
    items: list,
    lang: str,
    orientation: str,
    small_screen: bool,
    todo_entity_id: str | None = None,
    toggle_action_webhook_id: str | None = None,
) -> str:
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
        li {{ display: flex; align-items: center; font-size: {item_size}; padding: {li_padding}; border-bottom: 2px solid #eee; cursor: pointer; }}
        .icon {{ width: 1.2em; height: 1.2em; margin-right: {icon_margin}; flex-shrink: 0; }}
        .summary {{ flex-grow: 1; }}
        li.completed .summary {{ text-decoration: line-through; color: #888; }}
        .no-tasks {{ text-align: center; font-size: 3.0em; padding-top: 50px; color: #888; }}
        * {{ -webkit-user-select: none; -moz-user-select: none; user-select: none; }}
    """

    icon_unchecked = await async_get_icon_as_base64(hass, "checkbox-blank-outline.svg")
    icon_checked = await async_get_icon_as_base64(hass, "checkbox-marked.svg")

    def _get_webhook_url(hass, webhook_id: str | None) -> str | None:
        if not webhook_id:
            return None
        try:
            base = get_internal_url(hass) if get_internal_url else get_url(hass)
        except Exception:
            base = None
        if not base:
            base = "http://homeassistant.local:8123"
        return f"{base.rstrip('/')}/api/webhook/{webhook_id}"

    webhook_url = _get_webhook_url(hass, toggle_action_webhook_id) if toggle_action_webhook_id else None

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
            uid = item.get('uid') or ""

            icon_data = icon_checked if is_complete else icon_unchecked
            css_class = "completed" if is_complete else ""

            onclick = "toggleItem(this)" if webhook_url and todo_entity_id else "toggleLocal(this)"
            items_html += f"""
            <li class="{css_class}" data-uid="{html.escape(uid)}" data-status="{ 'completed' if is_complete else 'needs_action' }" onclick="{onclick}">
                <img src="{icon_data}" class="icon" />
                <span class="summary">{summary}</span>
            </li>
            """

    script_js = f"""
        <script>
        const ICON_UNCHECKED = "{icon_unchecked}";
        const ICON_CHECKED = "{icon_checked}";
        const WEBHOOK = {json.dumps(webhook_url) if webhook_url else 'null'};
        const TODO_ENTITY = {json.dumps(todo_entity_id) if todo_entity_id else 'null'};

        function _setVisual(li, completed) {{
            try {{
                if (completed) {{
                    li.classList.add('completed');
                }} else {{
                    li.classList.remove('completed');
                }}
                const img = li.querySelector('.icon');
                if (img) img.src = completed ? ICON_CHECKED : ICON_UNCHECKED;
                li.dataset.status = completed ? 'completed' : 'needs_action';
            }} catch (e) {{
            }}
        }}

        function toggleLocal(el) {{
            const li = el.closest('li');
            if (!li) return;
            const completed = li.dataset.status !== 'completed';
            _setVisual(li, completed);
        }}

        function postJSON(url, data) {{
            try {{
                fetch(url, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }}).catch(function(){{}}).finally(function(){{
                    setTimeout(function(){{ __vectLock = false; }}, 800);
                }});
            }} catch (e) {{
            }}
        }}

        function toggleItem(el) {{
            const li = el.closest('li');
            if (!li) return;

            const completed = li.dataset.status !== 'completed';
            _setVisual(li, completed);

            if (WEBHOOK && TODO_ENTITY) {{
                const payload = {{
                    entity_id: TODO_ENTITY,
                    uid: li.dataset.uid || null,
                    action: 'set_status',
                    status: completed ? 'completed' : 'needs_action'
                }};
                postJSON(WEBHOOK, payload);
            }}
        }}
        </script>
    """

    html_body = f"""
    <div class="header">{html.escape(title)}</div>
    <ul>{items_html}</ul>
    {script_js}
    """

    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{html.escape(title)}</title><style>{style_css}</style></head><body>{html_body}{cache_buster_comment}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_rss_feed_url(hass, title: str, items: list, lang: str, small_screen: bool) -> str:
    header_fs = "2.8em" if small_screen else "3.5em"
    item_fs = "1.8em" if small_screen else "2.2em"
    per_page = 7 if small_screen else 10

    style_css = f"""
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: white; color: black; margin: 0; padding: 0; box-sizing: border-box;
            display: flex; flex-direction: column; height: 100vh; width: 100vw;
            -webkit-text-size-adjust: 100%;
        }}
        .header {{
            flex: 0 0 auto; text-align: center; font-size: {header_fs};
            font-weight: bold; border-bottom: 3px solid black; padding: 20px 30px; margin: 0;
        }}
        .content {{
            flex: 1 1 auto; padding: 20px 30px 10px 30px;
            overflow: hidden;
            position: relative;
        }}
        .rss-page {{ display: none; }}
        .rss-page.active {{ display: block; }}

        ul {{ list-style: none; padding: 0; margin: 0; }}
        li {{
            font-size: {item_fs}; padding: 15px 5px; border-bottom: 2px solid #eee; line-height: 1.3;
        }}
        li:last-child {{ border-bottom: none; }}
        .icon {{ display: inline-block; margin-right: 15px; }}

        .pager {{
            flex: 0 0 auto;
            display: flex; align-items: center; justify-content: center;
            gap: 18px; padding: 14px 20px 18px 20px; border-top: 3px solid black;
        }}
        .pager-btn {{
            border: 3px solid #000; padding: 10px 18px; border-radius: 8px;
            background: #fff; cursor: pointer; font-weight: 700; user-select: none;
        }}
        .pager-btn:active {{ opacity: 0.7; }}
        .pager-btn.disabled {{ opacity: 0.35; cursor: default; pointer-events: none; }}
        .pager-info {{ min-width: 180px; text-align: center; font-weight: bold; }}

        * {{ -webkit-user-select: none; user-select: none; }}
    """

    icon_bullet = await async_get_icon_as_base64(hass, "circle-medium.svg")

    error_text = "Nie udało się wczytać kanału RSS" if lang == "pl" else "Failed to load RSS feed"
    btn_prev = "Wstecz" if lang == "pl" else "Previous"
    btn_next = "Dalej" if lang == "pl" else "Next"
    page_word = "Strona" if lang == "pl" else "Page"

    li_html_list: list[str] = []
    if not items:
        li_html_list.append(f"<li style='text-align:center;color:#888;'>{error_text}</li>")
    else:
        for item in items:
            summary = html.escape(item.get('title', 'Brak tytułu' if lang == 'pl' else 'No title'))
            li_html_list.append(
                f'<li><img src="{icon_bullet}" class="icon" style="width:0.8em;height:0.8em;" />{summary}</li>'
            )

    pages: list[list[str]] = []
    for i in range(0, len(li_html_list), per_page):
        pages.append(li_html_list[i:i+per_page])
    if not pages:
        pages = [[f"<li style='text-align:center;color:#888;'>{error_text}</li>"]]

    total_pages = len(pages)

    pages_html = []
    for idx, page_items in enumerate(pages, start=1):
        active_cls = " active" if idx == 1 else ""
        pages_html.append(
            f'<div class="rss-page{active_cls}" id="rss-page-{idx}"><ul>{"".join(page_items)}</ul></div>'
        )

    html_body = f"""
    <div class="header">{html.escape(title)}</div>

    <div class="content">
        {''.join(pages_html)}
    </div>

    <div class="pager">
        <div id="btn-prev" class="pager-btn{' disabled' if total_pages <= 1 else ''}" onclick="goPrev()">&larr; {btn_prev}</div>
        <div class="pager-info">{page_word} <span id="page-cur">1</span>/<span id="page-max">{total_pages}</span></div>
        <div id="btn-next" class="pager-btn{' disabled' if total_pages <= 1 else ''}" onclick="goNext()">{btn_next} &rarr;</div>
    </div>

    <script>
    (function(){{
        var cur = 1;
        var max = {total_pages};

        function show(n){{
            if (n < 1 || n > max) return;
            var old = document.getElementById('rss-page-' + cur);
            var neu = document.getElementById('rss-page-' + n);
            if (old) old.className = old.className.replace(' active','');
            if (neu && neu.className.indexOf('active') === -1) neu.className += ' active';
            cur = n;
            var pc = document.getElementById('page-cur');
            if (pc) pc.textContent = String(cur);

            var prev = document.getElementById('btn-prev');
            var next = document.getElementById('btn-next');
            if (prev) prev.className = 'pager-btn' + (cur <= 1 ? ' disabled' : '');
            if (next) next.className = 'pager-btn' + (cur >= max ? ' disabled' : '');
        }}

        window.goPrev = function(){{
            if (cur > 1) show(cur - 1);
        }};
        window.goNext = function(){{
            if (cur < max) show(cur + 1);
        }};

        show(1);
    }})();
    </script>
    """

    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{style_css}</style></head><body>{html_body}{cache_buster_comment}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_energy_panel_url(hass, states: dict[str], orientation: str, lang: str, small_screen: bool) -> str:
    panel_title = "Panel Energetyczny" if lang == "pl" else "Energy Panel"
    current_usage_label = "Aktualne zużycie" if lang == "pl" else "Current Usage"
    production_label = "Produkcja" if lang == "pl" else "Production"
    import_label = "Pobór" if lang == "pl" else "Import"
    export_label = "Eksport" if lang == "pl" else "Export"
    consumption_label = "Zużycie" if lang == "pl" else "Consumption"

    async def get_icon(name):
        return await async_get_icon_as_base64(hass, name)

    def get_state_val(state, precision: int = 2) -> str:
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
    
    is_portrait = orientation in ["0", "2"]
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
        .main-stats {{ flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }}
        .daily-stats {{ flex: 1; display: flex; flex-wrap: wrap; justify-content: space-around; align-content: center; gap: 15px; }}
        .main-stat-value {{ font-size: {main_val_fs}; font-weight: bold; line-height: 1.1; }}
        .main-stat-label {{ font-size: {main_lbl_fs}; opacity: 0.8; margin-top: 5px; }}
        .stat-card {{ flex-basis: {stat_card_basis}; padding: 15px; display: flex; flex-direction: column; align-items: center; text-align: center; }}
        .stat-card .icon {{ width: {icon_size}; height: {icon_size}; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: {card_val_fs}; font-weight: bold; }}
        .stat-card .label {{ font-size: {card_lbl_fs}; opacity: 0.8; }}
        .divider {{ border-left: 2px solid #000; margin: 20px; }}
    """
    
    main_stats_html, daily_stats_html = "", ""

    if states.get("power_usage_entity"):
        state = states["power_usage_entity"]
        unit = state.attributes.get("unit_of_measurement", "W")
        value = get_state_val(state, 1 if unit == UnitOfPower.KILO_WATT else 0)
        main_stats_html = f"""
        <div class="main-stats" style="margin: {main_stat_margin};">
            <div class="main-stat-value">{value} <span style="font-size: 0.5em;">{unit}</span></div>
            <div class="main-stat-label">{current_usage_label}</div>
        </div>"""

    daily_cards = []
    if states.get("daily_production_entity"):
        state = states["daily_production_entity"]
        daily_cards.append(f'<div class="stat-card"><img src="{icons["solar"]}" class="icon" /><div class="value">{get_state_val(state)} kWh</div><div class="label">{production_label}</div></div>')
    if states.get("daily_grid_import_entity"):
        state = states["daily_grid_import_entity"]
        daily_cards.append(f'<div class="stat-card"><img src="{icons["import"]}" class="icon" /><div class="value">{get_state_val(state)} kWh</div><div class="label">{import_label}</div></div>')
    if states.get("daily_grid_export_entity"):
        state = states["daily_grid_export_entity"]
        daily_cards.append(f'<div class="stat-card"><img src="{icons["export"]}" class="icon" /><div class="value">{get_state_val(state)} kWh</div><div class="label">{export_label}</div></div>')
    if states.get("daily_consumption_entity"):
        state = states["daily_consumption_entity"]
        daily_cards.append(f'<div class="stat-card"><img src="{icons["home"]}" class="icon" /><div class="value">{get_state_val(state)} kWh</div><div class="label">{consumption_label}</div></div>')

    if daily_cards:
        daily_stats_html = f'<div class="daily-stats">{"".join(daily_cards)}</div>'
    
    html_body = f"{main_stats_html}{'' if is_portrait else '<div class=divider></div>'}{daily_stats_html}"

    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{panel_title}</title><style>{style_css}</style></head><body>{html_body}{cache_buster_comment}</body></html>'
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
        cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>QR Code</title></head>
        <body style="margin: 0; padding: 20px; width: 100vw; height: 100vh; display: flex; flex-direction: {flex_direction}; align-items: center; justify-content: center; background-color: {back_color}; color: {fill_color}; box-sizing: border-box;">
            <div><img src="{img_data_url}" /></div>
            {message_html}
            {cache_buster_comment}
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
        # ZWIĘKSZONO OBSZAR KLIKNIĘCIA PRZYCISKU WSTECZ W WIDOKU DZIENNYM KALENDARZA
        html_body_content += '<a href="#" onclick="showView(\'monthly-view\'); return false;" class="back-button">&#x2190;</a>'
    
    if day_date:
        html_body_content += f'<div class="date-header">{_format_long_date(day_date, lang)}</div>'
        if not events:
            html_body_content += f'<div class="no-events">{no_events_text}</div>'
        else:
            for event in sorted(events, key=lambda x: x['start']):
                html_body_content += _generate_event_html(event, no_title_text)
        return html_body_content

    if not events:
        return f'<div class="no-events">{no_events_text}</div>'

    sorted_events = sorted(events, key=lambda x: x['start'])
    
    events_by_day = {}
    for event in sorted_events:
        event_date = event['start'].date()
        events_by_day.setdefault(event_date, []).append(event)
    
    day_html_blocks = []
    # Iterate in chronological order
    for event_date in sorted(events_by_day.keys()):
        day_events = events_by_day[event_date]
        day_html = f'<div class="date-header"><b>{_format_long_date(event_date, lang)}</b></div>'
        for event in day_events:
            day_html += _generate_event_html(event, no_title_text)
        day_html_blocks.append(day_html)

    if style == "minimalist":
        html_body_content += '<div class="calendar-columns">'
        left_col_html = "".join(f'<div class="day-column">{block}</div>' for block in day_html_blocks[::2])
        right_col_html = "".join(f'<div class="day-column">{block}</div>' for block in day_html_blocks[1::2])
        html_body_content += f'<div>{left_col_html}</div><div>{right_col_html}</div>'
        html_body_content += '</div>'
    else:
        html_body_content += "".join(day_html_blocks)
        
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
            body { font-family: 'Trebuchet MS', sans-serif; background-color: white; color: black; margin: 0; padding: 15px; box-sizing: border-box; overflow: hidden; height: 100vh; }
            .date-header { text-align: center; font-size: 2.2em; font-weight: bold; border-bottom: 3px solid black; padding-bottom: 8px; margin-top: 15px; margin-bottom: 15px; }
            .event { display: flex; margin-bottom: 12px; padding: 10px; border-left: 5px solid black; background-color: #f9f9f9; }
            .time { font-weight: bold; font-size: 1.5em; flex: 0 0 150px; }
            .details { display: flex; flex-direction: column; flex-grow: 1; min-width: 0; }
            .summary { font-size: 1.6em; font-weight: bold; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .location { font-style: italic; color: #444; font-size: 1.3em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .description { margin-top: 5px; font-size: 1.2em; color: #222; white-space: pre-wrap; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
            .no-events { text-align: center; font-size: 2.2em; padding-top: 60px; }
        """
    else: # minimalist
        # DYNAMICZNY ROZMIAR CZCIONKI: dopasuj do liczby wydarzeń
        num_events = len(events)
        if num_events <= 6:
            base_fs = "1.8em"
            date_fs = "2.0em"
            time_width = "160px"
        elif num_events <= 12:
            base_fs = "1.4em"
            date_fs = "1.6em"
            time_width = "140px"
        elif num_events <= 24:
            base_fs = "1.1em"
            date_fs = "1.3em"
            time_width = "120px"
        else: # Bardzo dużo wydarzeń
            base_fs = "0.9em"
            date_fs = "1.1em"
            time_width = "100px"

        style_css = f"""
            body {{ font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 10px; box-sizing: border-box; }}
            .calendar-columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 30px; align-items: start; }}
            .day-column {{ min-width: 0; }}
            .date-header {{ font-size: {date_fs}; font-weight: bold; margin-top: 15px; margin-bottom: 8px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
            .event {{ display: flex; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #eee; }}
            .time {{ flex: 0 0 {time_width}; font-weight: bold; font-size: {base_fs}; }}
            .details {{ display: flex; flex-direction: column; flex-grow: 1; min-width: 0; }}
            .summary {{ font-size: {base_fs}; }}
            .location, .description {{ display: none; }}
            .no-events {{ text-align: center; font-size: 1.4em; padding-top: 20%; grid-column: 1 / -1; }}
        """
    html_body_content = create_calendar_list_view_html(events, style, add_back_button=False, lang=lang)
    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{calendar_title}</title><style>{style_css}</style></head><body>{html_body_content}{cache_buster_comment}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_weather_calendar_url(
    hass,
    events: list,
    weather_entity_id: str,
    lang: str = "en",
    small_screen: bool = False,
    daily_forecast: list = None,
    add_back_button: bool = False,
    max_events: int = 5  # Domyślny limit liczby wydarzeń
) -> str:
    """
    Generates a calendar view with weather forecast.
    """
    calendar_title = "Kalendarz z Pogodą" if lang == "pl" else "Calendar with Weather"
    
    # Fetch weather state for current conditions
    weather_state = hass.states.get(weather_entity_id)
    if not weather_state:
        # Fallback to regular calendar if no weather
        _LOGGER.warning(f"Weather entity {weather_entity_id} not found, falling back to regular calendar")
        return create_calendar_url(events, style="modern", lang=lang)
    
        _LOGGER.warning(f"No daily forecast provided for weather calendar")
    
async def create_weather_calendar_url(hass: HomeAssistant, events: list[dict], 
                                      weather_entity_id: str, lang: str = "en", 
                                      small_screen: bool = False, daily_forecast: list = None,
                                      add_back_button: bool = False, max_events: int = 5) -> str:
    """
    Creates a combined Weather + Calendar HTML view.
    If events <= 3, shows a 'Hero' weather view (big icon today).
    Otherwise shows a 5-day forecast strip.
    """
    
    # Determine which layout to use based on EVENT COUNT (not max_events limit)
    # We use the actual number of events available to decide.
    events_count = len(events)
    use_hero_layout = events_count <= 3
    
    # Weather icons - using existing mapping
    sun_state = hass.states.get("sun.sun")
    is_day = sun_state and sun_state.state == "above_horizon"
    
    icon_map = {
        "sunny": "wi-day-sunny.svg" if is_day else "wi-night-clear.svg",
        "clear-night": "wi-night-clear.svg",
        "cloudy": "wi-cloudy.svg",
        "fog": "wi-fog.svg",
        "hail": "wi-day-hail.svg",
        "lightning": "wi-lightning.svg",
        "lightning-rainy": "wi-storm-showers.svg",
        "partlycloudy": "wi-day-cloudy.svg" if is_day else "wi-night-alt-cloudy.svg",
        "pouring": "wi-showers.svg",
        "rainy": "wi-rain.svg",
        "snowy": "wi-snow.svg",
        "snowy-rainy": "wi-rain-mix.svg",
        "windy": "wi-strong-wind.svg",
        "windy-variant": "wi-cloudy-gusts.svg",
        "exceptional": "wi-tornado.svg",
    }
    
    # Responsive sizing
    if small_screen:
        weather_section_height = "45%" if use_hero_layout else "28%"
        calendar_section_height = "55%" if use_hero_layout else "72%"
        
        # Standard layout sizes
        weather_day_fs = "1.5em"
        weather_temp_fs = "1.4em"
        weather_icon_size = "70px"
        
        # Hero layout sizes
        hero_icon_size = "180px"  # Zwiększono z 130px
        hero_temp_fs = "5.5em"
        hero_desc_fs = "1.8em"
        
        date_header_fs = "1.3em"
    else:
        weather_section_height = "50%" if use_hero_layout else "32%"
        calendar_section_height = "50%" if use_hero_layout else "68%"
        
        # Standard layout sizes
        weather_day_fs = "1.8em"
        weather_temp_fs = "1.7em"
        weather_icon_size = "95px"
        
        # Hero layout sizes
        hero_icon_size = "260px"  # Zwiększono z 180px
        hero_temp_fs = "7.5em"    # Zwiększono z 6.0em
        hero_desc_fs = "2.5em"

        date_header_fs = "2.0em"
        event_time_fs = "1.4em"
        event_summary_fs = "1.6em"
        padding = "15px"
    
    # Determine padding-bottom based on buttons
    padding_bottom = "70px" if add_back_button else "20px"
    
    style_css = f"""
        body {{
            font-family: 'Trebuchet MS', sans-serif;
            background-color: white;
            color: black;
            margin: 0;
            padding: {padding};
            box-sizing: border-box;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .weather-section {{
            height: {weather_section_height};
            border-bottom: 3px solid black;
            padding-bottom: {padding};
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            justify-content: center;
        }}
        /* weather-header usunięte */
        .weather-days {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            flex-grow: 1;
        }}
        .weather-day {{
            text-align: center;
            flex: 1;
        }}
        .weather-day-name {{
            font-size: {weather_day_fs};
            font-weight: bold;
            margin-bottom: 6px;
        }}
        .weather-icon {{
            width: {weather_icon_size};
            height: {weather_icon_size};
            margin: 4px auto;
            display: block;
        }}
        .weather-temp {{
            font-size: {weather_temp_fs};
            margin-top: 4px;
        }}
        .temp-high {{
            font-weight: bold;
        }}
        .temp-low {{
            color: #555;
        }}
        
        /* Hero Layout Styles */
        .hero-container {{
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}
        .hero-icon-img {{
            width: {hero_icon_size};
            height: {hero_icon_size};
            margin-right: 20px;
        }}
        .hero-details {{
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .hero-temp {{
            font-size: {hero_temp_fs};
            font-weight: bold;
            line-height: 1;
        }}
        .hero-desc {{
            font-size: {hero_desc_fs};
            margin-top: 5px;
            color: #444;
        }}
        .mini-forecast {{
            display: flex;
            justify-content: space-around;
            margin-top: 10px;
            border-top: 1px solid #ccc;
            padding-top: 10px;
        }}
        .mini-day {{
            text-align: center;
        }}
        .mini-day-name {{
            font-size: {weather_day_fs};
            font-weight: bold;
        }}
        .mini-icon {{
            width: {weather_icon_size}; /* Same as standard */
            height: {weather_icon_size};
        }}
        .mini-temp {{
            font-size: {weather_temp_fs};
        }}

        .calendar-section {{
            flex: 1;
            overflow: hidden;
            padding-top: {padding};
            padding-bottom: {padding_bottom};
        }}
        .date-header {{
            text-align: center;
            font-size: {date_header_fs};
            font-weight: bold;
            border-bottom: 3px solid black;
            padding-bottom: 4px;
            margin-top: 6px;
            margin-bottom: 6px;
        }}
        .event {{
            display: flex;
            margin-bottom: 4px;
            padding: 4px;
            border-left: 5px solid black;
            background-color: #f9f9f9;
        }}
        .time {{
            font-weight: bold;
            font-size: {event_time_fs};
            flex: 0 0 130px;
        }}
        .details {{
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            min-width: 0;
            overflow: hidden;
        }}
        .summary {{
            font-size: {event_summary_fs};
            font-weight: bold;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .location {{
            font-style: italic;
            color: #444;
            font-size: 0.9em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .description {{
             display: -webkit-box;
             -webkit-line-clamp: 2;
             -webkit-box-orient: vertical;
             overflow: hidden;
             font-size: 0.8em;
             margin-top: 2px;
             color: #333;
        }}
        .no-events {{
            text-align: center;
            font-size: {date_header_fs};
            padding-top: 40px;
            color: #999;
        }}
    """
    
    # Generate HTML for weather section
    weather_html = ""
    
    no_forecast_text = "Brak prognozy" if lang == "pl" else "No forecast"
    
    if not daily_forecast:
         weather_html = f'<div style="text-align:center;width:100%;font-size:{weather_day_fs};color:#999;">{html.escape(no_forecast_text)}</div>'
    else:
        day_names_pl = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_names = day_names_pl if lang == "pl" else day_names_en
        
        # Helper to process day data
        async def process_day(day_data):
            try:
                day_dt = dt_util.parse_datetime(day_data.get('datetime'))
                d_name = day_names[day_dt.weekday()] if day_dt else "?"
            except: d_name = "?"
            
            cond = day_data.get('condition', 'cloudy')
            i_name = icon_map.get(cond, "wi-cloud.svg")
            i_url = await async_get_icon_as_base64(hass, i_name)
            
            t_high = round(day_data.get('temperature', 0))
            t_low_val = day_data.get('templow')
            if t_low_val is not None:
                t_low = round(t_low_val)
                t_disp = f'<span class="temp-high">{t_high}°</span> / <span class="temp-low">{t_low}°</span>'
            else:
                t_disp = f'<span class="temp-high">{t_high}°</span>'
            
            return d_name, cond, i_url, t_high, t_disp

        if use_hero_layout:
            # --- HERO LAYOUT (Today + 3 Days) ---
            # Today (index 0)
            today = daily_forecast[0]
            d_name, cond, i_url, t_high, t_disp = await process_day(today)
            
            weather_html += f"""
            <div class="hero-container">
                <img src="{i_url}" class="hero-icon-img" alt="{cond}" />
                <div class="hero-details">
                    <div class="hero-temp">{t_high}°</div>
                    <div class="hero-desc">{cond.replace('-',' ').capitalize()}</div>
                </div>
            </div>
            """
            
            # Mini forecast (Next 3 days)
            weather_html += '<div class="mini-forecast">'
            for day in daily_forecast[1:4]: # Take next 3 days
                d_name, cond, i_url, t_high, t_disp = await process_day(day)
                weather_html += f"""
                <div class="mini-day">
                    <div class="mini-day-name">{d_name}</div>
                    <img src="{i_url}" class="mini-icon" alt="{cond}" />
                    <div class="mini-temp">{t_disp}</div>
                </div>
                """
            weather_html += '</div>'
            
        else:
            # --- STANDARD LAYOUT (5 Days Horizontal) ---
            weather_html += '<div class="weather-days">'
            for day in daily_forecast[:5]:
                d_name, cond, i_url, t_high, t_disp = await process_day(day)
                weather_html += f"""
                <div class="weather-day">
                    <div class="weather-day-name">{d_name}</div>
                    <img src="{i_url}" class="weather-icon" alt="{cond}" />
                    <div class="weather-temp">{t_disp}</div>
                </div>
                """
            weather_html += '</div>'
    
    # Filter events based on max_events
    filtered_events = events[:max_events] if events else []
    
    # Generate HTML for events
    calendar_html = create_calendar_list_view_html(
        filtered_events, lang=lang, style="modern", add_back_button=False # Using CSS classes for sizing
    )
    
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{style_css}</style>
    </head>
    <body>
        <div class="weather-section">
            {weather_html}
        </div>
        <div class="calendar-section">
            {calendar_html}
        </div>
    </body>
    </html>
    """
    
    return create_simple_cache_buster(f"data:text/html,{urllib.parse.quote(final_html)}")

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

    # ZMIANA: Zwiększono obszar kliknięcia (padding) i odsunięto przycisk wstecz od krawędzi (left/top)
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
        .day-number {{ z-index: 1; }}
        .day-cell.today .day-number {{ background-color: black; color: white; border-radius: 50%; width: 2.2em; height: 2.2em; line-height: 2.2em; display: inline-block; }}
        .day-number.has-event {{ color: black; border: 3px solid black; border-radius: 50%; width: calc(1.9em - 6px); height: calc(1.9em - 6px); line-height: calc(1.9em - 6px); display: inline-block; }}
        .daily-view-container {{ padding: 25px; }}
        .back-button {{ font-size: 3.5em; text-decoration: none; color: black; position: absolute; top: 15px; left: 15px; cursor: pointer; z-index: 1001; padding: 15px 30px; }}
        .date-header {{ text-align: center; font-size: 2.4em; font-weight: bold; border-bottom: 3px solid black; padding-bottom: 15px; margin-bottom: 20px; }}
        .event {{ display: flex; margin-bottom: 18px; padding: 12px; border-left: 5px solid black; background-color: #f9f9f9; }}
        .time {{ font-weight: bold; font-size: 1.8em; flex: 0 0 220px; }}
        .details {{ display: flex; flex-direction: column; flex-grow: 1; }}
        .summary {{ font-size: 2.0em; font-weight: bold; margin-bottom: 8px; }}
        .location {{ font-style: italic; color: #444; font-size: 1.4em; }}
        .description {{ margin-top: 10px; font-size: 1.3em; color: #222; white-space: pre-wrap; }}
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
    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{calendar_title}</title><style>{style_css}</style><script>{js_script}</script></head><body>{monthly_view_html}{daily_views_html}{cache_buster_comment}</body></html>'
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

        # --- DODAJ TE DWIE LINIE PONIŻEJ JEŚLI ICH BRAKUJE ---
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        # -----------------------------------------------------

        # Definiujemy parametry lokalnie
        my_params = {
            'font.size': 16,
            'axes.titlesize': 22,
            'axes.labelsize': 16,
            'xtick.labelsize': 14,
            'ytick.labelsize': 14,
            'lines.linewidth': 4,
            'lines.markersize': 10,
            'figure.facecolor': 'white', 'axes.facecolor': 'white',
            'savefig.facecolor': 'white', 'text.color': 'black', 'axes.labelcolor': 'black',
            'xtick.color': 'black', 'ytick.color': 'black', 'axes.edgecolor': 'black',
        }

        if is_portrait:
            figsize = (6.0, 6.0) 
        else:
            figsize = (8.0, 5.0)

        # Używamy kontekstu - ustawienia działają TYLKO wewnątrz tego wcięcia (bloku with)
        with plt.style.context(('grayscale', my_params)):
            fig = Figure(figsize=figsize, dpi=100, constrained_layout=False)
            canvas = FigureCanvasAgg(fig)
            ax = fig.add_subplot(111)
            
            ax.plot(timestamps, temperatures, marker='o', linestyle='-', color='black')

            title = "Prognoza 24h" if lang == "pl" else "24h Forecast"
            ax.set_title(title, fontweight='bold')
            
            ax.grid(True, which='major', linestyle='--', linewidth=1.5)
            
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            if is_portrait:
                fig.autofmt_xdate(rotation=45, ha='right')
                fig.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.15)
            else:
                fig.autofmt_xdate(rotation=0, ha='center')
                fig.subplots_adjust(left=0.08, right=0.99, top=0.90, bottom=0.15)

            buf = io.BytesIO()
            canvas.print_png(buf)
            buf.seek(0)
            return buf.getvalue()
    except Exception as e:
        _LOGGER.error(f"Failed to generate weather forecast graph: {e}")
        return None

def _generate_graph_image(
    hass,
    history_data: dict,
    entity_ids: list[str],
    graph_type: str,
    show_points: bool,
    orientation: str,
) -> bytes | None:
    if not history_data:
        _LOGGER.warning(f"No historical data provided for entities: {entity_ids}")
        return None

    # --- KONFIGURACJA DLA JOAN 6 ---
    my_params = {
        'font.size': 16,             
        'axes.titlesize': 22,        
        'axes.labelsize': 18,        
        'xtick.labelsize': 14,       
        'ytick.labelsize': 16,       
        'lines.linewidth': 4,        
        'lines.markersize': 10,      
        'figure.facecolor': 'white', 'axes.facecolor': 'white',
        'savefig.facecolor': 'white', 'text.color': 'black', 'axes.labelcolor': 'black',
        'xtick.color': 'black', 'ytick.color': 'black', 'axes.edgecolor': 'black',
        'legend.fontsize': 18        
    }

    line_cycler = (cycler('linestyle', ['-', '--', ':', '-.']))
    bar_colors = ['#222222', '#666666', '#999999', '#BBBBBB']

    is_portrait = orientation in ["0", "2"]

    if is_portrait:
        figsize = (6.0, 8.0) 
    else:
        figsize = (8.0, 6.0)

    # --- DODAJ TE DWIE LINIE PONIŻEJ JEŚLI ICH BRAKUJE ---
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    # -----------------------------------------------------

    # Kontekst izolujący style
    with plt.style.context(('grayscale', my_params)):
        fig = Figure(figsize=figsize, dpi=100, constrained_layout=False)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        
        has_data = False
        ax.set_prop_cycle(line_cycler)
        num_entities = len(entity_ids)

        for i, entity_id in enumerate(entity_ids):
            if entity_id not in history_data: continue
            states = history_data[entity_id]
            timestamps, values = [], []
            for state in states:
                try:
                    if state.state not in UNKNOWN_STRINGS:
                        values.append(float(state.state))
                        timestamps.append(state.last_updated)
                except (ValueError, TypeError): continue
            if not values: continue
            has_data = True
            
            entity_state = hass.states.get(entity_id)
            entity_name = entity_state.name if entity_state else entity_id
            
            plot_args = {'label': entity_name}
            
            if graph_type == 'line':
                if show_points: plot_args['marker'] = 'o'
                ax.plot(timestamps, values, **plot_args)
                
            elif graph_type == 'bar':
                # ZMIANA: Zmniejszono szerokość z 0.8 na 0.5 (żeby się mniej stykały)
                total_bar_width = timedelta(hours=0.5)
                bar_width = total_bar_width / max(1, num_entities)
                offset = (i - (num_entities - 1) / 2) * bar_width
                bar_timestamps = [ts + offset for ts in timestamps]
                plot_args['color'] = bar_colors[i % len(bar_colors)]
                
                # ZMIANA: Dodano alpha=0.6 (przezroczystość) i edgecolor (obwódkę)
                # Dzięki temu widać słupki "z tyłu"
                ax.bar(bar_timestamps, values, width=bar_width, alpha=0.6, edgecolor='black', **plot_args)
                
            else:
                if show_points: plot_args['marker'] = 'o'
                ax.plot(timestamps, values, **plot_args)

        if not has_data: return None

        # Siatka i osie
        ax.grid(True, which='major', linestyle='--', linewidth=1.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        if is_portrait:
            fig.autofmt_xdate(rotation=45, ha='right')
        else:
            fig.autofmt_xdate(rotation=0, ha='center')

        # --- LEGENDA I MARGINESY ---
        handles, labels = ax.get_legend_handles_labels()
        
        if len(labels) >= 1:
            fig.legend(
                handles, labels,
                loc='upper center',
                bbox_to_anchor=(0.5, 0.99),
                ncol=1,           
                frameon=False    
            )
            
            items_count = len(labels)
            top_margin = 0.90 - (0.07 * items_count)
            if top_margin < 0.4: top_margin = 0.4

            if is_portrait:
                fig.subplots_adjust(top=top_margin, bottom=0.12, left=0.16, right=0.96)
            else:
                fig.subplots_adjust(top=top_margin, bottom=0.15, left=0.10, right=0.98)
        else:
            fig.subplots_adjust(top=0.95, bottom=0.12, left=0.16, right=0.95)

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf.getvalue()

async def create_weather_url(
    hass, 
    weather_state, 
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
    
    sun_state = hass.states.get("sun.sun")
    is_day = sun_state and sun_state.state == "above_horizon"
    
    # POPRAWKA: Zaktualizowany icon_map z ikonami dziennymi/nocnymi
    icon_map = {
        "sunny": "wi-day-sunny.svg" if is_day else "wi-night-clear.svg",
        "clear-night": "wi-night-clear.svg",
        "cloudy": "wi-cloudy.svg",
        "fog": "wi-day-fog.svg" if is_day else "wi-fog.svg",
        "hail": "wi-day-hail.svg" if is_day else "wi-hail.svg",
        "lightning": "wi-day-lightning.svg" if is_day else "wi-lightning.svg",
        "lightning-rainy": "wi-storm-showers.svg",
        "partlycloudy": "wi-day-cloudy.svg" if is_day else "wi-night-alt-cloudy.svg",
        "pouring": "wi-showers.svg",
        "rainy": "wi-rain.svg",
        "snowy": "wi-snow.svg",
        "snowy-rainy": "wi-rain-mix.svg",
        "windy": "wi-strong-wind.svg",
        "windy-variant": "wi-cloudy-gusts.svg",
        "exceptional": "wi-tornado.svg",
    }

    async def get_weather_icon(condition_state):
        icon_name = icon_map.get(condition_state, "wi-cloud.svg")
        return await async_get_icon_as_base64(hass, icon_name)
    
    is_portrait = orientation in ["0", "2"]

    style_css = f"""
        body {{ font-family: sans-serif; background-color: white; color: black; margin: 0; padding: 25px; box-sizing: border-box; display: flex; flex-direction: column; height: 100vh; width: 100vw; }}
        hr {{ border: 0; border-top: 2px solid black; margin: 15px 0; }}
        .flex {{ display: flex; }} .col {{ flex-direction: column; }} .center {{ align-items: center; justify-content: center; }}
        .space-around {{ justify-content: space-around; }} .space-between {{ justify-content: space-between; }}
        .icon {{ width: 1em; height: 1em; vertical-align: middle; }}
        
        .weather-graph-panel {{ display: flex; flex-direction: column; height: 100%; width: 100%; }}
        .graph-section {{ flex: 7; display: flex; align-items: center; justify-content: center; width: 100%; }}
        .graph-section img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .current-conditions-section {{ flex: 2; border-top: 3px solid black; margin-top: 20px; padding-top: 15px; }}
        
        .summary-header {{ width: 100%; text-align: center; }}
        .summary-main {{ display: flex; align-items: center; justify-content: center; margin: 10px 0; }}
        .summary-main .temp {{ font-size: {'10em' if small_screen else '12em'}; font-weight: bold; line-height: 1; }}
        .summary-main .icon {{ width: {'220px' if small_screen else '300px'}; height: {'220px' if small_screen else '300px'}; margin-left: 20px; }}
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
        .daily-list-standalone .daily-item .precip {{ display: flex; align-items: center; justify-content: flex-end; flex: 0 0 {'180px' if small_screen else '220px'}; font-size: 0.8em; }}
        .daily-list-standalone .daily-item .precip .icon {{ width: {'32px' if small_screen else '40px'}; height: {'32px' if small_screen else '40px'}; margin-right: 10px; }}
    """
    
    html_body = ""
    temp = f"{round(_get_attr_as_float(attrs, 'temperature'))}&deg;"
    apparent_temp_val = _get_attr_as_float(attrs, 'apparent_temperature', default=_get_attr_as_float(attrs, 'temperature'))
    feels_like = f"{round(apparent_temp_val)}&deg;"
    main_icon_url = await get_weather_icon(state)

    temp_unit = attrs.get('temperature_unit') or "°C"

    if layout == "weather_graph_panel":
        graph_bytes = await hass.async_add_executor_job(
            _generate_weather_forecast_graph, hourly_forecast or [], lang, temp_unit, is_portrait
        )
        if graph_bytes:
            graph_b64 = base64.b64encode(graph_bytes).decode("utf-8")
            graph_img = f"data:image/png;base64,{graph_b64}"
            graph_html = f'<div class="graph-section"><img src="{graph_img}" alt="forecast graph" /></div>'
        else:
            msg = no_graph_data_label
            graph_html = f'<div class="graph-section"><div style="font-size:2em;opacity:.7;text-align:center;">{html.escape(msg)}</div></div>'
        
        humidity = f"{int(_get_attr_as_float(attrs, 'humidity', 0))}%"
        wind_speed = f"{_get_attr_as_float(attrs, 'wind_speed', 0)} {attrs.get('wind_speed_unit', 'km/h')}"
        wind_dir = wind_deg_to_direction(attrs.get('wind_bearing'), lang)
        pressure = f"{_get_attr_as_float(attrs, 'pressure', 0)} {attrs.get('pressure_unit', 'hPa')}"
        sunrise, sunset = "---", "---"
        sun_attrs = getattr(sun_state, "attributes", None) or {}
        try:
            sunrise_dt = dt_util.parse_datetime(sun_attrs.get("next_rising", "")) if sun_attrs else None
            sunset_dt = dt_util.parse_datetime(sun_attrs.get("next_setting", "")) if sun_attrs else None
            if sunrise_dt: sunrise = sunrise_dt.strftime("%H:%M")
            if sunset_dt: sunset = sunset_dt.strftime("%H:%M")
        except Exception:
            pass

        current_html = f"""
        <div class="current-conditions-section">
            <div class="summary-header">
                <div class="summary-main">
                    <div class="temp">{temp}</div>
                    <img src="{main_icon_url}" class="icon" />
                </div>
                <div class="feels-like">{feels_like_label}: {feels_like}</div>
            </div>
            <div class="summary-details">
                <div class="detail-item">{wind_label}: {wind_dir} {wind_speed}</div>
                <div class="detail-item">{pressure_label}: {pressure}</div>
                <div class="detail-item">{humidity_label}: {humidity}</div>
                <div class="detail-item">
                    <img src="{await async_get_icon_as_base64(hass, 'wi-sunrise.svg')}" class="icon" /> {sunrise} /
                    <img src="{await async_get_icon_as_base64(hass, 'wi-sunset.svg')}" class="icon" /> {sunset}
                </div>
            </div>
        </div>
        """
        html_body = f'<div class="weather-graph-panel">{graph_html}{current_html}</div>'

    elif layout == "daily_forecast_list":
        items_html = ""
        if not daily_forecast:
            items_html = f"<div style='text-align:center;font-size:2em;opacity:.7;'>{html.escape(no_daily_data_label)}</div>"
        else:
            drop_icon = await async_get_icon_as_base64(hass, "wi-raindrops.svg")
            # ZMIANA: Zamiast 0% pokazujemy opady w mm lub wiatr, jeśli opadów brak
            for day in daily_forecast[:5]: 
                try:
                    day_dt = dt_util.parse_datetime(day.get('datetime'))
                    day_name = day_dt.strftime("%a") if lang == "en" else _PL_DAY_ABBR[day_dt.weekday()]
                except Exception:
                    day_name = "?"
                icon_url = await get_weather_icon(day.get('condition'))
                temp_high = f"{round(day.get('temperature', 0))}&deg;"
                temp_low = f"{round(day.get('templow', 0))}&deg;"
                
                precip_html = ""
                pp = day.get('precipitation_probability')
                if pp is not None and pp > 0:
                     precip_html = f"<div class='precip'><img src='{drop_icon}' class='icon' /> {int(pp)}%</div>"
                else:
                    # Jeśli brak %, sprawdź ilość opadów
                    amt = day.get('precipitation')
                    if amt is not None and amt > 0:
                         # Zakładamy mm, bo to standard w HA, choć idealnie byłoby brać jednostkę z encji
                         precip_html = f"<div class='precip'><img src='{drop_icon}' class='icon' /> {amt} mm</div>"
                    else:
                        # Jeśli brak opadów, spróbuj pokazać wiatr
                        ws = day.get('wind_speed')
                        if ws is not None and ws > 0:
                            wind_icon = await async_get_icon_as_base64(hass, "wi-strong-wind.svg")
                            unit_ws = attrs.get('wind_speed_unit', 'km/h')
                            precip_html = f"<div class='precip'><img src='{wind_icon}' class='icon' /> {int(ws)} {unit_ws}</div>"

                items_html += f"""
                <div class="daily-item">
                    <div class="day">{day_name}</div>
                    <img src="{icon_url}" class="icon" />
                    <div class="temps">{temp_high} / {temp_low}</div>
                    {precip_html}
                </div>
                """
        html_body = f'<div class="daily-list-standalone">{items_html}</div>'

    else:  # Detailed Summary
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
            # ZMIANA: Ograniczenie do 4 dni w widoku szczegółowym, aby nie wystawało
            for day in daily_forecast[:4]:
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

    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{weather_title}</title><style>{style_css}</style></head><body>{html_body}{cache_buster_comment}</body></html>'
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

def create_simple_cache_buster(url: str) -> str:
    if url.startswith("data:"):
        return url
    timestamp, separator = int(time.time()), "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}"

async def create_keypad_url(hass, title: str, webhook_url: str) -> str:
    """Generates a data URL for a full-screen numeric keypad view."""
    import urllib.parse
    import html
    import json

    icon_backspace = await async_get_icon_as_base64(hass, "backspace-outline.svg")
    icon_enter = await async_get_icon_as_base64(hass, "keyboard-return.svg")

    style_css = f"""
        body, html {{
            width: 100%; height: 100%; margin: 0; padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: white; color: black;
            -webkit-user-select: none; -moz-user-select: none; user-select: none;
        }}
        body {{
            display: flex; flex-direction: column;
            box-sizing: border-box; padding: 20px;
        }}
        .container {{
            flex-grow: 1;
            display: flex; flex-direction: column;
            width: 100%; max-width: 600px; margin: 0 auto;
        }}
        .header {{
            font-size: 4em; font-weight: bold; text-align: center;
            flex-shrink: 0;
        }}
        #pin-display {{
            height: 100px; background-color: #eee; border: 3px solid black;
            font-size: 5em; text-align: center; line-height: 100px;
            margin: 20px 0; letter-spacing: 0.3em;
            font-family: 'Courier New', Courier, monospace;
            flex-shrink: 0;
        }}
        .keypad-grid {{
            flex-grow: 1;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(4, 1fr);
            gap: 20px;
        }}
        .key {{
            border: 3px solid black; font-size: 4.5em; font-weight: bold;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; background-color: white; border-radius: 10px;
        }}
        .key:active {{
            background-color: #ccc;
        }}
        .key img {{
            width: 1.2em; height: 1.2em;
        }}
    """

    html_body = f"""
    <div class="container">
        <div class="header">{html.escape(title)}</div>
        <div id="pin-display"></div>
        <div class="keypad-grid">
            <div class="key" onclick="handleKey('1')">1</div>
            <div class="key" onclick="handleKey('2')">2</div>
            <div class="key" onclick="handleKey('3')">3</div>
            <div class="key" onclick="handleKey('4')">4</div>
            <div class="key" onclick="handleKey('5')">5</div>
            <div class="key" onclick="handleKey('6')">6</div>
            <div class="key" onclick="handleKey('7')">7</div>
            <div class="key" onclick="handleKey('8')">8</div>
            <div class="key" onclick="handleKey('9')">9</div>
            <div class="key" onclick="handleKey('clear')"><img src="{icon_backspace}"></div>
            <div class="key" onclick="handleKey('0')">0</div>
            <div class="key" onclick="handleKey('enter')"><img src="{icon_enter}"></div>
        </div>
    </div>
    """

    script_js = f"""
        const webhook = {json.dumps(webhook_url)};
        let pin = '';
        const display = document.getElementById('pin-display');
        const MAX_PIN_LENGTH = 10;

        function updateDisplay() {{
            display.textContent = '*'.repeat(pin.length);
        }}

        function handleKey(key) {{
            if (key === 'enter') {{
                if (pin.length > 0) sendPin();
            }} else if (key === 'clear') {{
                pin = '';
            }} else {{
                if (pin.length < MAX_PIN_LENGTH) {{
                    pin += key;
                }}
            }}
            updateDisplay();
        }}
        
        function sendPin() {{
            display.textContent = '...';
            try {{
                fetch(webhook, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ pin: pin }})
                }}).catch(function(){{}}).finally(function(){{
                    setTimeout(function(){{ __vectLock = false; }}, 800);
                }});
            }} catch (e) {{
                display.textContent = 'Error';
            }}
        }}
        
        updateDisplay();
    """

    html_content = (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<title>{html.escape(title)}</title><style>{style_css}</style></head>'
        f'<body>{html_body}<script>{script_js}</script></body></html>'
    )
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def create_button_panel_url(hass, title: str, buttons: list[dict], small_screen: bool) -> str:
    """
    Generuje panel przycisków. Jeśli title jest pusty -> brak nagłówka.
    """
    title = (title or "").strip()

    num_buttons = len(buttons)
    if num_buttons <= 4:
        cols = 2
    elif num_buttons <= 6:
        cols = 3
    elif num_buttons <= 8:
        cols = 4
    else:  # 9-12
        cols = 3

    rows = -(-num_buttons // cols)

    if small_screen:
        header_fs, button_name_fs, icon_size, gap, sub_name_fs = "2.8em", "1.3em", "3.5em", "15px", "1.0em"
        header_padding = "0 0 10px 0"
    else:
        header_fs, button_name_fs, icon_size, gap, sub_name_fs = "3.5em", "1.5em", "4.5em", "20px", "1.2em"
        header_padding = "0 0 20px 0"

    style_css = f"""
        body, html {{
            width: 100%; height: 100%; margin: 0; padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: white; color: black;
            -webkit-user-select: none; user-select: none;
        }}
        .container {{
            display: flex; flex-direction: column;
            box-sizing: border-box; padding: 20px;
            height: 100%;
        }}
        .header {{
            font-size: {header_fs}; font-weight: bold; text-align: center;
            flex-shrink: 0; padding: {header_padding};
        }}
        .grid {{
            flex-grow: 1; display: grid;
            grid-template-columns: repeat({cols}, 1fr);
            grid-template-rows: repeat({rows}, 1fr);
            gap: {gap};
        }}
        .button-item {{
            border: 3px solid black;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            cursor: pointer; background-color: white; border-radius: 10px;
            padding: 10px; text-align: center;
            text-decoration: none; color: black;
        }}
        .button-item:active {{
            background-color: #ccc;
        }}
        .button-item .icon {{
            width: {icon_size}; height: {icon_size}; margin-bottom: 8px;
        }}
        .button-item .name {{
            font-size: {button_name_fs}; font-weight: bold; line-height: 1.2;
        }}
        .button-item .sub-name {{
            font-size: {sub_name_fs}; opacity: 0.8; margin-top: 5px; line-height: 1.1;
        }}
    """

    buttons_html = ""
    for button_data in buttons[:12]:
        webhook_url = button_data.get("webhook_url")
        icon_name = button_data.get("icon")
        button_name = button_data.get("name", "")
        sub_name = button_data.get("sub_name", "")

        if not webhook_url:
            continue

        icon_data_url = await async_get_icon_as_base64(hass, icon_name) if icon_name else ""
        
        icon_html = f'<img src="{icon_data_url}" class="icon" />' if icon_data_url else ""
        name_html = f'<div class="name">{html.escape(button_name)}</div>' if button_name else ""
        sub_name_html = f'<div class="sub-name">{html.escape(sub_name)}</div>' if sub_name else ""
        
        buttons_html += f"""
        <div class="button-item" onclick="triggerWebhook('{webhook_url}')">
            {icon_html}
            {name_html}
            {sub_name_html}
        </div>
        """
        
    script_js = """
        function triggerWebhook(url) {
            if (!url) return;
            try {
                fetch(url, { method: 'POST', body: '{}' }).catch(function(e){ console.error('Webhook failed'); });
            } catch (e) { console.error('Error triggering webhook'); }
        }
    """

    header_html = f'<div class="header">{html.escape(title)}</div>' if title else ""

    cache_buster_comment = f'<!-- cb:{int(time.time())} -->'
    html_body = f"""
    <div class="container">
        {header_html}
        <div class="grid">{buttons_html}</div>
    </div>
    {cache_buster_comment}
    """
    
    html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Button Panel</title><style>{style_css}</style></head><body>{html_body}<script>{script_js}</script></body></html>'
    return f"data:text/html;charset=UTF-8,{urllib.parse.quote(html_content)}"
