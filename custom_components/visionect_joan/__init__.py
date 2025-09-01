# custom_components/visionect_joan/__init__.py
import logging
import time
import urllib.parse
import voluptuous as vol
import html

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
        UNKNOWN_STRINGS, DISPLAY_ROTATIONS
    )
except ImportError as e:
    _LOGGER.critical(f"Krytyczny błąd importu w __init__.py: {e}")
    raise

PLATFORMS = ["sensor"]

# Definicje usług i atrybutów
SERVICE_SET_URL = "set_url"
SERVICE_SEND_TEXT = "send_text"
SERVICE_SET_DISPLAY_ROTATION = "set_display_rotation"

ATTR_URL = "url"
ATTR_MESSAGE = "message"
ATTR_TEXT_COLOR = "text_color"
ATTR_BACKGROUND_COLOR = "background_color"
ATTR_TEXT_SIZE = "text_size"
ATTR_TEXT_ALIGN = "text_align"
ATTR_FONT_FAMILY = "font_family"
ATTR_FONT_WEIGHT = "font_weight"
ATTR_DISPLAY_ROTATION = "display_rotation"

# Kolory dla e-ink
EINK_COLORS = ["black", "white"]

# Wagi czcionki
FONT_WEIGHTS = ["normal", "bold"]

# ZMIANA: Zaktualizowana mapa czcionek
THEMED_FONTS = {
    "Nowoczesna": "'Trebuchet MS', Helvetica, sans-serif",
    "Czytelna": "Verdana, Geneva, sans-serif",
    # --- Czcionki z Google Fonts ---
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

# ZMIANA: Nowy, zbiorczy link do importu wszystkich czcionek.
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
})

SERVICE_SET_DISPLAY_ROTATION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_DISPLAY_ROTATION): vol.In(list(DISPLAY_ROTATIONS.keys())),
})

def create_simple_cache_buster(url: str) -> str:
    timestamp = int(time.time())
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}"

def create_text_message_url(message: str, text_color: str = "black",
                           background_color: str = "white", text_size: str = "28px",
                           text_align: str = "center", font_family_key: str = "Nowoczesna",
                           font_weight: str = "normal") -> str:
    font_family_css = THEMED_FONTS.get(font_family_key, "'Trebuchet MS', sans-serif")
    font_import_rule = f"@import url('{GOOGLE_FONTS_IMPORT_URL}');"
    escaped_message = html.escape(message).replace('\n', '<br>')

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
            text-align: {text_align};
            font-size: {text_size};
            font-weight: {font_weight};
            margin: 20px;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            box-sizing: border-box;
            line-height: 1.5;
            letter-spacing: 0.5px;
            -webkit-font-smoothing: none;
            -moz-osx-font-smoothing: unset;
            font-smooth: never;
            text-rendering: optimizeLegibility;
        }}
        .message {{
            max-width: 90%;
            word-wrap: break-word;
            word-spacing: 2px;
        }}
        .timestamp {{
            position: absolute;
            bottom: 15px;
            right: 15px;
            font-size: 20px;
            opacity: 0.8;
            font-family: 'Courier New', Courier, monospace;
            font-weight: 700;
            letter-spacing: 1px;
        }}
    </style>
</head>
<body>
    <div class="message">{escaped_message}</div>
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
            if await api.async_set_device_url(uuid, url_with_buster):
                await api.async_restart_session(uuid)
                _LOGGER.info(f"URL dla {uuid} ustawiony, sesja zrestartowana.")
            else:
                _LOGGER.error(f"Nie udało się ustawić URL dla {uuid}")
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
        _LOGGER.info(f"Renderowana wiadomość: '{message}'")
        _LOGGER.info(f"Wysyłanie tekstu do {len(uuids)} urządzeń")
        data_url = create_text_message_url(
            message, text_color, background_color, text_size_px, text_align, font_family_key, font_weight
        )
        for uuid in uuids:
            _LOGGER.info(f"Wysyłanie tekstu do {uuid}")
            if await api.async_set_device_url(uuid, data_url):
                await api.async_restart_session(uuid)
                _LOGGER.info(f"Tekst wysłany pomyślnie do {uuid}, sesja zrestartowana.")
            else:
                _LOGGER.error(f"Nie udało się wysłać tekstu do {uuid}")
        await coordinator.async_request_refresh()
    async def handle_set_display_rotation(call: ServiceCall):
        uuids = await get_uuids_from_call(call)
        display_rotation = call.data[ATTR_DISPLAY_ROTATION]
        _LOGGER.info(f"Ustawianie rotacji ekranu na '{display_rotation}' dla {len(uuids)} urządzeń")
        for uuid in uuids:
            _LOGGER.info(f"Ustawianie rotacji ekranu dla {uuid}")
            if await api.async_set_display_rotation(uuid, display_rotation):
                await api.async_reboot_device(uuid)
                _LOGGER.info(f"Rotacja ekranu dla {uuid} zmieniona, urządzenie restartowane.")
            else:
                _LOGGER.error(f"Nie udało się zmienić rotacji ekranu dla {uuid}")
        await coordinator.async_request_refresh()

    # Rejestracja usług
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SERVICE_SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DISPLAY_ROTATION, handle_set_display_rotation, schema=SERVICE_SET_DISPLAY_ROTATION_SCHEMA)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Integracja Visionect Joan została pomyślnie zainicjalizowana.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DISPLAY_ROTATION)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok