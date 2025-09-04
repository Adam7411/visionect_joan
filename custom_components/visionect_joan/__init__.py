# custom_components/visionect_joan/__init__.py
import logging
import time
import urllib.parse
import voluptuous as vol
import html
from datetime import datetime, timezone

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall
    from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
    import homeassistant.helpers.config_validation as cv
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers.template import Template

    from .api import VisionectAPI
    from .const import (
        DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
        UNKNOWN_STRINGS, DISPLAY_ROTATIONS, SERVICE_FORCE_REFRESH, SERVICE_CLEAR_DISPLAY
    )
except ImportError as e:
    _LOGGER.critical(f"Krytyczny błąd importu w __init__.py: {e}")
    raise

PLATFORMS = ["sensor", "binary_sensor", "number"]

# Definicje usług i atrybutów
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
# Usunięto: ATTR_IMAGE_DITHERING


# Kolory dla e-ink
EINK_COLORS = ["black", "white"]

# Wagi czcionki
FONT_WEIGHTS = ["normal", "bold"]

# Opcje layoutu
LAYOUT_OPTIONS = ["text_only", "image_top", "image_left", "image_right"]
# Usunięto: DITHERING_OPTIONS = ["none", "ordered", "floyd-steinberg"]


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

# Schematy walidacji
SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_URL): cv.url,
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
    vol.Optional(ATTR_IMAGE_URL): cv.url,
    # Usunięto: vol.Optional(ATTR_IMAGE_DITHERING, default="ordered"): vol.In(DITHERING_OPTIONS),
})


SERVICE_SET_DISPLAY_ROTATION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_DISPLAY_ROTATION): vol.In(list(DISPLAY_ROTATIONS.keys())),
})

SERVICE_DEVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
})


def create_simple_cache_buster(url: str) -> str:
    timestamp = int(time.time())
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}"

# ZMIANA W TEJ FUNKCJI (usunięcie parametru ditheringu i jego zastosowania)
def create_text_message_url(message: str, text_color: str = "black",
                           background_color: str = "white", text_size: str = "28px",
                           text_align: str = "center", font_family_key: str = "Nowoczesna",
                           font_weight: str = "normal", layout: str = "text_only",
                           image_url: str = None) -> str: # Usunięto: image_dithering: str = "ordered"
    font_family_css = THEMED_FONTS.get(font_family_key, "'Trebuchet MS', sans-serif")
    font_import_rule = f"@import url('{GOOGLE_FONTS_IMPORT_URL}');"
    escaped_message = html.escape(message).replace('\n', '<br>')

    image_html = ""
    if layout != "text_only" and image_url:
        # ZMIANA: Usunięto '-vss-dither: {image_dithering};'
        dither_style = "image-rendering: pixelated;"
        image_html = f'<div class="image-container"><img src="{image_url}" style="{dither_style}" /></div>'

    flex_direction = "column"
    if layout == "image_left": flex_direction = "row"
    if layout == "image_right": flex_direction = "row-reverse"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiadomość E-ink</title>
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
            -moz-osx-font-smoothing: unset;
            font-smooth: never;
            text-rendering: optimizeLegibility;
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
            letter-spacing: 0.5px;
            word-wrap: break-word;
            flex-shrink: 1;
        }}
        .image-container {{
            flex-shrink: 0;
            max-width: {'40%' if layout in ['image_left', 'image_right'] else '90%'};
            max-height: {'90%' if layout in ['image_left', 'image_right'] else '40%'};
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
    _LOGGER.info("Rozpoczynanie konfiguracji integracji Visionect Joan.")
    hass.data.setdefault(DOMAIN, {})
    api = VisionectAPI(
        hass, entry.data[CONF_HOST], entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PASSWORD), entry.data.get(CONF_API_KEY),
        entry.data.get(CONF_API_SECRET)
    )
    if not await api.async_test_authentication():
        _LOGGER.error("Autentykacja nie powiodła się. Nie można załadować integracji.")
        return False
    async def async_update_data():
        _LOGGER.debug("Rozpoczynanie aktualizacji danych z Visionect API.")
        devices_summary = await api.async_get_all_devices()
        if not devices_summary:
            _LOGGER.warning("Nie znaleziono żadnych urządzeń Visionect lub błąd API.")
            return {}
        data = {}
        for device_summary in devices_summary:
            uuid = device_summary.get("Uuid")
            if not uuid: continue
            device_details = await api.async_get_device_data(uuid)
            if not device_details:
                _LOGGER.warning(f"Brak danych szczegółowych dla urządzenia {uuid}, pomijanie.")
                continue
            final_data = device_details
            if "Config" not in final_data: final_data["Config"] = {}
            device_name_from_summary = device_summary.get("Options", {}).get("Name")
            if device_name_from_summary and device_name_from_summary.lower() not in UNKNOWN_STRINGS:
                final_data["Config"]["Name"] = device_name_from_summary
            
            final_data["LastUpdated"] = datetime.now(timezone.utc)
            
            data[uuid] = final_data
        return data
    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"visionect_{entry.entry_id}",
        update_method=async_update_data, update_interval=SCAN_INTERVAL,
    )
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
            _LOGGER.info(f"Ustawianie URL dla {uuid} na {url_with_buster}")
            status = "failure"
            if await api.async_set_device_url(uuid, url_with_buster):
                await api.async_restart_session(uuid)
                _LOGGER.info(f"URL dla {uuid} ustawiony, sesja zrestartowana.")
                status = "success"
            else:
                _LOGGER.error(f"Nie udało się ustawić URL dla {uuid}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SET_URL, "status": status,
                "params": {"url": original_url}
            })
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        message_template = call.data[ATTR_MESSAGE]
        if isinstance(message_template, Template):
            message_template.hass = hass
        message = message_template.async_render(parse_result=False) if isinstance(message_template, Template) else message_template
        
        text_color = call.data[ATTR_TEXT_COLOR]
        background_color = call.data[ATTR_BACKGROUND_COLOR]
        text_size_int = call.data[ATTR_TEXT_SIZE]
        text_size_px = f"{text_size_int}px"
        text_align = call.data[ATTR_TEXT_ALIGN]
        font_family_key = call.data[ATTR_FONT_FAMILY]
        font_weight = call.data[ATTR_FONT_WEIGHT]
        layout = call.data[ATTR_LAYOUT]
        image_url = call.data.get(ATTR_IMAGE_URL)
        # Usunięto: image_dithering = call.data[ATTR_IMAGE_DITHERING]

        _LOGGER.info(f"Renderowana wiadomość: '{message}' z layoutem '{layout}'")
        _LOGGER.info(f"Wysyłanie tekstu do {len(uuids)} urządzeń")
        
        data_url = create_text_message_url(
            message, text_color, background_color, text_size_px, text_align, 
            font_family_key, font_weight, layout, image_url
        ) # Usunięto: image_dithering
        
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie tekstu do {uuid}")
            status = "failure"
            if await api.async_set_device_url(uuid, data_url):
                await api.async_restart_session(uuid)
                _LOGGER.info(f"Tekst wysłany pomyślnie do {uuid}, sesja zrestartowana.")
                status = "success"
            else:
                _LOGGER.error(f"Nie udało się wysłać tekstu do {uuid}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SEND_TEXT, "status": status,
                "params": {"message": message, "layout": layout, "image_url": image_url}
            })
        await coordinator.async_request_refresh()

    async def handle_set_display_rotation(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        display_rotation = call.data[ATTR_DISPLAY_ROTATION]
        _LOGGER.info(f"Ustawianie rotacji ekranu na '{display_rotation}' dla {len(uuids)} urządzeń")
        for uuid in uuids:
            _LOGGER.info(f"Ustawianie rotacji ekranu dla {uuid}")
            status = "failure"
            if await api.async_set_display_rotation(uuid, display_rotation):
                await api.async_reboot_device(uuid)
                _LOGGER.info(f"Rotacja ekranu dla {uuid} zmieniona, urządzenie restartowane.")
                status = "success"
            else:
                _LOGGER.error(f"Nie udało się zmienić rotacji ekranu dla {uuid}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_SET_DISPLAY_ROTATION, "status": status,
                "params": {"display_rotation": display_rotation}
            })
        await coordinator.async_request_refresh()

    async def handle_force_refresh(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        _LOGGER.info(f"Wymuszanie odświeżenia (przez restart sesji) dla {len(uuids)} urządzeń")
        for uuid in uuids:
            status = "failure"
            if await api.async_restart_session(uuid):
                _LOGGER.info(f"Sesja dla {uuid} została pomyślnie zrestartowana (odświeżono).")
                status = "success"
            else:
                _LOGGER.error(f"Nie udało się zrestartować sesji dla {uuid}")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_FORCE_REFRESH, "status": status
            })

    async def handle_clear_display(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        _LOGGER.info(f"Czyszczenie ekranu dla {len(uuids)} urządzeń")
        blank_url = "data:text/html,<html><body style='background-color:white;'></body></html>"
        for uuid in uuids:
            status = "failure"
            if await api.async_set_device_url(uuid, blank_url):
                await api.async_restart_session(uuid)
                _LOGGER.info(f"Ekran dla {uuid} został pomyślnie wyczyszczony.")
                status = "success"
            else:
                _LOGGER.error(f"Nie udało się wyczyścić ekranu dla {uuid} (błąd przy ustawianiu URL).")
            hass.bus.async_fire(EVENT_COMMAND_RESULT, {
                "uuid": uuid, "service": SERVICE_CLEAR_DISPLAY, "status": status
            })

    # Rejestracja usług
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SERVICE_SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DISPLAY_ROTATION, handle_set_display_rotation, schema=SERVICE_SET_DISPLAY_ROTATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_FORCE_REFRESH, handle_force_refresh, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_DISPLAY, handle_clear_display, schema=SERVICE_DEVICE_SCHEMA)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Integracja Visionect Joan została pomyślnie zainicjalizowana.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DISPLAY_ROTATION)
    hass.services.async_remove(DOMAIN, SERVICE_FORCE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_DISPLAY)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok