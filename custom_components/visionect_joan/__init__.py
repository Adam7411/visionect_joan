# custom_components/visionect_joan/__init__.py
import logging
import time
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

# Definicje usług i atrybutów - tylko działające
SERVICE_SET_URL = "set_url"

ATTR_URL = "url"
ATTR_USE_WEB = "use_web"

# Schematy walidacji - tylko dla działającej usługi
SERVICE_SET_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string, 
    vol.Required(ATTR_URL): cv.url,
    vol.Optional(ATTR_USE_WEB, default=False): cv.boolean
})

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
            
            # Preferuj nazwę z "Options" w podsumowaniu, jeśli dostępna i nie jest "nieznana"
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
    
    # WAŻNE: Dodaj referencję do config_entry w coordinator
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
        """Obsługuje zmianę URL - tylko przez API."""
        uuids = await get_uuids_from_call(call)
        original_url = call.data[ATTR_URL]
        
        # Dodaj cache buster
        timestamp = int(time.time())
        separator = "&" if "?" in original_url else "?"
        url_with_buster = f"{original_url}{separator}timestamp={timestamp}"
        _LOGGER.info(f"Oryginalny URL: {original_url}, URL z cache buster: {url_with_buster}")
        
        for uuid in uuids:
            # Używaj tylko API - usuń obsługę web interface
            _LOGGER.info(f"Ustawianie URL przez API dla {uuid}")
            success = await api.async_set_device_url(uuid, url_with_buster)
                
            if success:
                # Restart sesji po udanej zmianie URL
                await api.async_restart_session(uuid)
                _LOGGER.info(f"Sesja urządzenia {uuid} została zrestartowana")
            else:
                _LOGGER.error(f"Nie udało się zmienić URL urządzenia {uuid}")
                
        # Odśwież dane po zmianie
        await coordinator.async_request_refresh()

    # Rejestracja tylko działającej usługi
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Integracja Visionect Joan została pomyślnie zainicjalizowana.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usuwa wpis konfiguracyjny."""
    # Usuń tylko zarejestrowaną usługę
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok