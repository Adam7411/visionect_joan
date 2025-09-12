# custom_components/visionect_joan/__init__.py
import logging
import time
import urllib.parse
import voluptuous as vol
import html
from datetime import datetime, timezone
import io
import base64
import qrcode

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.template import Template

from .api import VisionectAPI
from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY,
    SERVICE_SLEEP_DEVICE, SERVICE_WAKE_DEVICE, SERVICE_SEND_QR_CODE
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

EINK_COLORS = ["black", "white"]
FONT_WEIGHTS = ["normal", "bold"]
LAYOUT_OPTIONS = ["text_only", "image_top", "image_bottom", "image_left", "image_right"]

THEMED_FONTS = { "Nowoczesna": "'Trebuchet MS', Helvetica, sans-serif", "Czytelna": "Verdana, Geneva, sans-serif", "Archivo Black": "'Archivo Black', sans-serif", "Arbutus": "'Arbutus', serif", "Asimovian": "'Asimovian', sans-serif", "Bangers": "'Bangers', cursive", "Blaka": "'Blaka', cursive", "Bungee": "'Bungee', cursive", "Bungee Shade": "'Bungee Shade', cursive", "Cherry Bomb One": "'Cherry Bomb One', cursive", "Cinzel Decorative": "'Cinzel Decorative', serif", "Damion": "'Damion', cursive", "Diplomata SC": "'Diplomata SC', cursive", "Fascinate": "'Fascinate', cursive", "Joti One": "'Joti One', cursive", "Libertinus Keyboard": "'Libertinus Keyboard', serif", "MedievalSharp": "'MedievalSharp', cursive", "Michroma": "'Michroma', sans-serif", "New Rocker": "'New Rocker', cursive", "Rubik Wet Paint": "'Rubik Wet Paint', cursive", "Spicy Rice": "'Spicy Rice', cursive", "Story Script": "'Story Script', cursive", }
GOOGLE_FONTS_IMPORT_URL = "https://fonts.googleapis.com/css2?family=Archivo+Black&family=Arbutus&family=Asimovian&family=Bangers&family=Blaka&family=Bungee&family=Bungee+Shade&family=Cherry+Bomb+One&family=Cinzel+Decorative:wght@400;700;900&family=Damion&family=Diplomata+SC&family=Fascinate&family=Joti+One&family=Libertinus+Keyboard&family=MedievalSharp&family=Michroma&family=New+Rocker&family=Rubik+Wet+Paint&family=Spicy+Rice&family=Story+Script&display=swap"

SERVICE_SET_URL_SCHEMA = vol.Schema({ vol.Required(ATTR_DEVICE_ID): cv.string, vol.Required(ATTR_URL): cv.string, })
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
SERVICE_SET_DISPLAY_ROTATION_SCHEMA = vol.Schema({ vol.Required(ATTR_DEVICE_ID): cv.string, vol.Required(ATTR_DISPLAY_ROTATION): vol.In(list(DISPLAY_ROTATIONS.keys())), })
SERVICE_DEVICE_SCHEMA = vol.Schema({ vol.Required(ATTR_DEVICE_ID): cv.string, })
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

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Ustawia globalną konfigurację dla integracji z pliku YAML."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        hass.data[DOMAIN]["views"] = config[DOMAIN].get("views", [])
    else:
        hass.data[DOMAIN]["views"] = []
    return True

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

def create_simple_cache_buster(url: str) -> str:
    timestamp = int(time.time())
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}"

def create_text_message_url(message: str, text_color: str = "black", background_color: str = "white", text_size: str = "28px", text_align: str = "center", font_family_key: str = "Nowoczesna", font_weight: str = "normal", layout: str = "text_only", image_url: str = None, image_zoom: int = 100) -> str:
    font_family_css = THEMED_FONTS.get(font_family_key, "'Trebuchet MS', sans-serif")
    font_import_rule = f"@import url('{GOOGLE_FONTS_IMPORT_URL}');"
    escaped_message = html.escape(message).replace('\n', '<br>')
    image_html = ""
    if layout != "text_only" and image_url:
        scale_factor = image_zoom / 100.0
        zoom_style = f"transform: scale({scale_factor}); image-rendering: pixelated;"
        image_html = f'<div class="image-container"><img src="{image_url}" style="{zoom_style}" /></div>'
    flex_direction = "column"
    if layout == "image_bottom": flex_direction = "column-reverse"
    elif layout == "image_left": flex_direction = "row"
    elif layout == "image_right": flex_direction = "row-reverse"
    auto_retry_script = """<script>function scheduleRetry() { console.log('Visionect: Network error detected. Retrying in 60 seconds...'); setTimeout(function() { window.location.reload(true); }, 60000); } window.VECT = window.VECT || {}; window.VECT.onNetworkError = scheduleRetry; window.addEventListener('error', function(event) { if (event.target.src) { console.log('Visionect: Failed to load resource: ' + event.target.src); scheduleRetry(); } }, true); </script>"""
    html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Wiadomość E-ink</title>{auto_retry_script}<style>{font_import_rule} body {{ font-family: {font_family_css}; color: {text_color}; background-color: {background_color}; margin: 0; padding: 0; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; text-align: {text_align}; box-sizing: border-box; -webkit-font-smoothing: none; font-smooth: never; }} .container {{ display: flex; flex-direction: {flex_direction}; align-items: center; justify-content: center; width: 90%; height: 90%; gap: 20px; }} .text-container {{ font-size: {text_size}; font-weight: {font_weight}; line-height: 1.5; word-wrap: break-word; flex-shrink: 1; }} .image-container {{ flex-shrink: 0; max-width: {'40%' if layout in ['image_left', 'image_right'] else '90%'}; max-height: {'90%' if layout in ['image_left', 'image_right'] else '40%'}; display: flex; align-items: center; justify-content: center;}} img {{ max-width: 100%; max-height: 100%; object-fit: contain; }} .timestamp {{ position: absolute; bottom: 10px; right: 10px; font-size: 16px; opacity: 0.8; font-family: 'Courier New', Courier, monospace; font-weight: 700; }}</style></head><body><div class="container">{image_html if layout != 'text_only' else ''}<div class="text-container">{escaped_message}</div></div><div class="timestamp">{time.strftime("%Y-%m-%d %H:%M")}</div></body></html>"""
    encoded = urllib.parse.quote(html_content, safe='')
    return f"data:text/html,{encoded}"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Rozpoczynanie konfiguracji wpisu dla Visionect Joan.")
    
    api = VisionectAPI(hass, entry.data[CONF_HOST], entry.data.get(CONF_USERNAME), entry.data.get(CONF_PASSWORD), entry.data.get(CONF_API_KEY), entry.data.get(CONF_API_SECRET))
    if not await api.async_test_authentication():
        _LOGGER.error("Autentykacja nie powiodła się. Nie można załadować integracji.")
        return False

    async def async_update_data():
        devices_summary = await api.async_get_all_devices()
        if not devices_summary: return {}
        data = {}
        for device_summary in devices_summary:
            uuid = device_summary.get("Uuid")
            if not uuid: continue
            device_details = await api.async_get_device_data(uuid)
            if not device_details: continue
            final_data = device_details
            if "Config" not in final_data: final_data["Config"] = {}
            device_name = device_summary.get("Options", {}).get("Name")
            if device_name and device_name.lower() not in UNKNOWN_STRINGS:
                final_data["Config"]["Name"] = device_name
            final_data["LastUpdated"] = datetime.now(timezone.utc)
            data[uuid] = final_data
        return data

    coordinator = DataUpdateCoordinator(hass, _LOGGER, name=f"visionect_{entry.entry_id}", update_method=async_update_data, update_interval=SCAN_INTERVAL)
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {"api": api, "coordinator": coordinator}
    
    device_reg = dr.async_get(hass)

    async def get_uuids_from_call(call: ServiceCall) -> list[str]:
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if isinstance(device_ids, str): device_ids = [device_ids]
        uuids = []
        for device_id in device_ids:
            device_entry = device_reg.async_get(device_id)
            if device_entry and (uuid := next((i[1] for i in device_entry.identifiers if i[0] == DOMAIN), None)):
                uuids.append(uuid)
        return uuids

    async def handle_set_url(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        original_url = call.data[ATTR_URL]
        url_with_buster = create_simple_cache_buster(original_url)
        for uuid in uuids:
            status = "failure"
            if await api.async_set_device_url(uuid, url_with_buster) and await api.async_restart_session(uuid): status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_SET_URL, "status": status, "params": {"url": original_url}})
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        if isinstance(message_template, Template): message_template.hass = hass
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        data_url = create_text_message_url(
            message,
            call.data[ATTR_TEXT_COLOR],
            call.data[ATTR_BACKGROUND_COLOR],
            f"{call.data[ATTR_TEXT_SIZE]}px",
            call.data[ATTR_TEXT_ALIGN],
            call.data[ATTR_FONT_FAMILY],
            call.data[ATTR_FONT_WEIGHT],
            call.data[ATTR_LAYOUT],
            call.data.get(ATTR_IMAGE_URL),
            call.data.get(ATTR_IMAGE_ZOOM)
        )
        for uuid in uuids:
            status = "failure"
            if await api.async_set_device_url(uuid, data_url) and await api.async_restart_session(uuid): status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_SEND_TEXT, "status": status, "params": {"message": message}})
        await coordinator.async_request_refresh()

    async def handle_set_display_rotation(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        rotation = call.data[ATTR_DISPLAY_ROTATION]
        for uuid in uuids:
            status = "failure"
            if await api.async_set_display_rotation(uuid, rotation) and await api.async_reboot_device(uuid): status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status, "params": {"display_rotation": rotation}})
        await coordinator.async_request_refresh()

    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        for uuid in uuids:
            status = "failure"
            if await api.async_restart_session(uuid): status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_FORCE_REFRESH, "status": status})

    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        for uuid in uuids:
            status = "failure"
            if await api.async_set_device_url(uuid, blank_url) and await api.async_restart_session(uuid): status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_CLEAR_DISPLAY, "status": status})
            
    async def handle_sleep_device(call: ServiceCall):
        """Obsługuje usypianie urządzenia."""
        uuids = await get_uuids_from_call(call)
        duration = call.data[ATTR_DURATION]
        sleep_url = f"data:text/html,<html><script>window.VECT.setSleep({duration});</script></html>"
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie komendy uśpienia do {uuid} na {duration} sekund.")
            status = "failure"
            if await api.async_set_device_url(uuid, sleep_url) and await api.async_restart_session(uuid):
                status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_SLEEP_DEVICE, "status": status, "params": {"duration": duration}})

    async def handle_wake_device(call: ServiceCall):
        """Obsługuje wybudzanie urządzenia."""
        uuids = await get_uuids_from_call(call)
        wake_url = "data:text/html,<html><script>window.VECT.setSleep(0);</script></html>"
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie komendy wybudzenia do {uuid}.")
            status = "failure"
            if await api.async_set_device_url(uuid, wake_url) and await api.async_restart_session(uuid):
                status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_WAKE_DEVICE, "status": status})

    async def handle_send_qr_code(call: ServiceCall):
        """Obsługuje generowanie i wysyłanie kodu QR."""
        uuids = await get_uuids_from_call(call)
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
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie kodu QR do {uuid}.")
            status = "failure"
            if await api.async_set_device_url(uuid, qr_url) and await api.async_restart_session(uuid):
                status = "success"
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {"uuid": uuid, "service": SERVICE_SEND_QR_CODE, "status": status})

    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SERVICE_SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DISPLAY_ROTATION, handle_set_display_rotation, schema=SERVICE_SET_DISPLAY_ROTATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_FORCE_REFRESH, handle_force_refresh, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_DISPLAY, handle_clear_display, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SLEEP_DEVICE, handle_sleep_device, schema=SERVICE_SLEEP_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_WAKE_DEVICE, handle_wake_device, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_QR_CODE, handle_send_qr_code, schema=SERVICE_SEND_QR_CODE_SCHEMA)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Wpis konfiguracyjny dla Visionect Joan został pomyślnie zainicjalizowany.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DISPLAY_ROTATION)
    hass.services.async_remove(DOMAIN, SERVICE_FORCE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_DISPLAY)
    hass.services.async_remove(DOMAIN, SERVICE_SLEEP_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_WAKE_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_QR_CODE)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok