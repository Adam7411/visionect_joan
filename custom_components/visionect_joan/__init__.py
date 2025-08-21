# custom_components/visionect_joan/__init__.py
import logging
import time
import urllib.parse
import asyncio
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall
    from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, ATTR_DEVICE_ID
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
    import homeassistant.helpers.config_validation as cv
    from homeassistant.helpers import device_registry as dr

    from .api import VisionectAPI
    from .const import (
        DOMAIN, CONF_API_KEY, CONF_API_SECRET, SCAN_INTERVAL,
        UNKNOWN_STRINGS
    )
except ImportError as e:
    _LOGGER.critical(f"Krytyczny błąd importu w __init__.py: {e}")
    raise

PLATFORMS = ["sensor"]

# Definicje usług i atrybutów
SERVICE_SET_URL = "set_url"
SERVICE_SEND_TEXT = "send_text"

ATTR_URL = "url"
ATTR_USE_WEB = "use_web"
ATTR_MESSAGE = "message"
ATTR_TEXT_COLOR = "text_color"
ATTR_BACKGROUND_COLOR = "background_color"
ATTR_TEXT_SIZE = "text_size"
ATTR_TEXT_ALIGN = "text_align"
ATTR_FONT_FAMILY = "font_family"

# Kolory dla e-ink (tylko czarny i biały)
EINK_COLORS = ["black", "white"]

# Czcionki zoptymalizowane dla e-ink
PREDEFINED_FONTS = [
    "Arial, Helvetica, sans-serif",
    "Georgia, 'Times New Roman', serif",
    "Verdana, Geneva, sans-serif",
    "Tahoma, Geneva, sans-serif",
    "'Trebuchet MS', Helvetica, sans-serif",
    "'Lucida Grande', 'Lucida Sans Unicode', sans-serif",
    "Palatino, 'Palatino Linotype', serif",
    "'Courier New', Courier, monospace",
    "'Franklin Gothic Medium', Arial, sans-serif",
    "Garamond, 'Times New Roman', serif"
]

# Schematy walidacji
SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string, 
    vol.Required(ATTR_URL): cv.url,
    vol.Optional(ATTR_USE_WEB, default=False): cv.boolean
})

SERVICE_SEND_TEXT_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_MESSAGE): cv.string,
    vol.Optional(ATTR_TEXT_COLOR, default="black"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_BACKGROUND_COLOR, default="white"): vol.In(EINK_COLORS),
    vol.Optional(ATTR_TEXT_SIZE, default="28px"): cv.string,
    vol.Optional(ATTR_TEXT_ALIGN, default="center"): vol.In(["left", "center", "right"]),
    vol.Optional(ATTR_FONT_FAMILY, default="Arial, Helvetica, sans-serif"): vol.In(PREDEFINED_FONTS),
})

def create_simple_cache_buster(url: str) -> str:
    """Tworzy prosty cache buster."""
    timestamp = int(time.time())
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}cb={timestamp}"

def create_text_message_url(message: str, text_color: str = "black", 
                           background_color: str = "white", text_size: str = "28px",
                           text_align: str = "center", font_family: str = "Arial, Helvetica, sans-serif") -> str:
    """Tworzy Data URI z wiadomością tekstową."""
    
    import html
    escaped_message = html.escape(message).replace('\n', '<br>')
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-ink Message</title>
    <style>
        body {{ 
            font-family: {font_family}; 
            color: {text_color}; 
            background-color: {background_color};
            text-align: {text_align};
            font-size: {text_size};
            font-weight: 500;
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
    """Konfiguracja integracji na podstawie wpisu konfiguracyjnego."""
    _LOGGER.info("Rozpoczynanie konfiguracji integracji Visionect Joan.")
    hass.data.setdefault(DOMAIN, {})

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
        """Pobiera i scala dane urządzeń."""
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
        hass,
        _LOGGER,
        name=f"visionect_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )
    
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api, 
        "coordinator": coordinator
    }
    device_reg = dr.async_get(hass)

    async def get_uuids_from_call(call: ServiceCall) -> list[str]:
        """Helper to get UUIDs from a service call."""
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if isinstance(device_ids, str):
            device_ids = [device_ids]
        
        uuids = []
        for device_id in device_ids:
            device_entry = device_reg.async_get(device_id)
            if device_entry and (uuid := next((i[1] for i in device_entry.identifiers if i[0] == DOMAIN), None)):
                uuids.append(uuid)
        return uuids

    async def handle_set_url(call: ServiceCall):
        """Obsługuje zmianę URL na czystym serwerze Visionect."""
        uuids = await get_uuids_from_call(call)
        original_url = call.data[ATTR_URL]
        
        # Prosty cache buster
        url_with_buster = create_simple_cache_buster(original_url)
        
        _LOGGER.info(f"🧹 CZYSTY SERWER - ustawianie URL")
        _LOGGER.info(f"Oryginalny URL: {original_url}")
        _LOGGER.info(f"URL z cache buster: {url_with_buster}")
        
        for uuid in uuids:
            try:
                _LOGGER.info(f"📡 Ustawianie URL dla {uuid} na czystym serwerze")
                
                success = await api.async_set_device_url_clean_server(uuid, url_with_buster)
                    
                if success:
                    _LOGGER.info(f"✅ URL ustawiony pomyślnie dla {uuid}")
                    
                    # Krótkie opóźnienie przed restartem sesji
                    await asyncio.sleep(1)
                    await api.async_restart_session(uuid)
                    _LOGGER.info(f"🔄 Sesja zrestartowana dla {uuid}")
                else:
                    _LOGGER.error(f"❌ Nie udało się ustawić URL dla {uuid}")
                    
            except Exception as e:
                _LOGGER.error(f"❌ Błąd dla {uuid}: {e}")
                
        # Odśwież dane
        await asyncio.sleep(2)
        await coordinator.async_request_refresh()

    async def handle_send_text(call: ServiceCall):
        """Obsługuje wysyłanie wiadomości tekstowej."""
        uuids = await get_uuids_from_call(call)
        message = call.data[ATTR_MESSAGE]
        text_color = call.data.get(ATTR_TEXT_COLOR, "black")
        background_color = call.data.get(ATTR_BACKGROUND_COLOR, "white")
        text_size = call.data.get(ATTR_TEXT_SIZE, "28px")
        text_align = call.data.get(ATTR_TEXT_ALIGN, "center")
        font_family = call.data.get(ATTR_FONT_FAMILY, "Arial, Helvetica, sans-serif")
        
        _LOGGER.info(f"📝 Wysyłanie tekstu: '{message}' do {len(uuids)} urządzeń")
        
        data_url = create_text_message_url(
            message, text_color, background_color, 
            text_size, text_align, font_family
        )
        
        for uuid in uuids:
            try:
                _LOGGER.info(f"📡 Wysyłanie tekstu do {uuid}")
                success = await api.async_set_device_url_clean_server(uuid, data_url)
                
                if success:
                    _LOGGER.info(f"✅ Tekst wysłany pomyślnie do {uuid}")
                    await asyncio.sleep(1)
                    await api.async_restart_session(uuid)
                else:
                    _LOGGER.error(f"❌ Nie udało się wysłać tekstu do {uuid}")
                    
            except Exception as e:
                _LOGGER.error(f"❌ Błąd wysyłania tekstu do {uuid}: {e}")
        
        await asyncio.sleep(2)
        await coordinator.async_request_refresh()

    # Rejestracja usług
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SERVICE_SEND_TEXT_SCHEMA)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Integracja Visionect Joan została pomyślnie zainicjalizowana.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usuwa wpis konfiguracyjny."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_TEXT)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok