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
        MIN_REFRESH_INTERVAL, MAX_REFRESH_INTERVAL,
        ORIENTATION_PORTRAIT, ORIENTATION_LANDSCAPE, ORIENTATION_PORTRAIT_FLIPPED, ORIENTATION_LANDSCAPE_FLIPPED,
        SLEEP_MODE_MANUAL, SLEEP_MODE_AUTO, SLEEP_MODE_DISABLED, UNKNOWN_STRINGS # Dodano UNKNOWN_STRINGS
    )
except ImportError as e:
    _LOGGER.critical(f"Krytyczny błąd importu w __init__.py: {e}")
    raise

PLATFORMS = ["sensor", "button"]

# Definicje usług i atrybutów
SERVICE_SET_URL = "set_url"
SERVICE_SET_ORIENTATION = "set_orientation"
SERVICE_SET_REFRESH_INTERVAL = "set_refresh_interval"
SERVICE_SET_SLEEP_MODE = "set_sleep_mode"
SERVICE_SET_CONFIG = "set_config"

ATTR_URL = "url"
ATTR_ORIENTATION = "orientation"
ATTR_REFRESH_INTERVAL = "refresh_interval"
ATTR_SLEEP_MODE = "sleep_mode"
ATTR_CONFIG_KEY = "config_key"
ATTR_CONFIG_VALUE = "config_value"

# Schematy walidacji
SERVICE_SET_URL_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string, vol.Required(ATTR_URL): cv.url})

SERVICE_SET_ORIENTATION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_ORIENTATION): vol.In([
        ORIENTATION_PORTRAIT, ORIENTATION_LANDSCAPE, 
        ORIENTATION_PORTRAIT_FLIPPED, ORIENTATION_LANDSCAPE_FLIPPED
    ])
})

SERVICE_SET_REFRESH_INTERVAL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_REFRESH_INTERVAL): vol.All(
        vol.Coerce(int),
        vol.Range(min=MIN_REFRESH_INTERVAL, max=MAX_REFRESH_INTERVAL)
    )
})

SERVICE_SET_SLEEP_MODE_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_SLEEP_MODE): vol.In([
        SLEEP_MODE_MANUAL, SLEEP_MODE_AUTO, SLEEP_MODE_DISABLED
    ])
})

SERVICE_SET_CONFIG_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_CONFIG_KEY): cv.string,
    vol.Required(ATTR_CONFIG_VALUE): cv.string,
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
            # WAŻNE: Nie ustawiaj domyślnej nazwy typu "Visionect Joan XXXX" tutaj.
            # Pozwól VisionectEntity (entity.py) zająć się domyślną nazwą (UUID),
            # jeśli Config.Name jest nadal puste lub "nieznane" po pobraniu danych.
            # Dzięki temu Config.Name pozostanie None/puste, jeśli API go nie dostarczy,
            # a encja ustawia wtedy UUID.
        
            data[uuid] = final_data
        
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"visionect_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {"api": api, "coordinator": coordinator}
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
        uuids = await get_uuids_from_call(call)
        
        original_url = call.data[ATTR_URL]
        timestamp = int(time.time())
        separator = "&" if "?" in original_url else "?"
        url_with_buster = f"{original_url}{separator}timestamp={timestamp}"
        _LOGGER.info(f"Oryginalny URL: {original_url}, URL z cache buster: {url_with_buster}")
        
        for uuid in uuids:
            if await api.async_set_device_url(uuid, url_with_buster):
                await api.async_restart_session(uuid)
        await coordinator.async_request_refresh()

    async def handle_set_orientation(call: ServiceCall):
        """Obsługuje zmianę orientacji ekranu."""
        uuids = await get_uuids_from_call(call)
        orientation = call.data[ATTR_ORIENTATION]
        for uuid in uuids:
            if await api.async_set_device_orientation(uuid, orientation):
                await api.async_restart_session(uuid)
        await coordinator.async_request_refresh()

    async def handle_set_refresh_interval(call: ServiceCall):
        """Obsługuje zmianę interwału odświeżania."""
        uuids = await get_uuids_from_call(call)
        interval = call.data[ATTR_REFRESH_INTERVAL]
        for uuid in uuids:
            if await api.async_set_refresh_interval(uuid, interval):
                await api.async_restart_session(uuid)
        await coordinator.async_request_refresh()

    async def handle_set_sleep_mode(call: ServiceCall):
        """Obsługuje zmianę trybu uśpienia."""
        uuids = await get_uuids_from_call(call)
        sleep_mode = call.data[ATTR_SLEEP_MODE]
        for uuid in uuids:
            config_updates = {"SleepMode": sleep_mode}
            if await api.async_set_device_config(uuid, config_updates):
                await api.async_restart_session(uuid)
        await coordinator.async_request_refresh()

    async def handle_set_config(call: ServiceCall):
        """Obsługuje ustawienie dowolnego parametru konfiguracji."""
        uuids = await get_uuids_from_call(call)
        config_key = call.data[ATTR_CONFIG_KEY]
        config_value = call.data[ATTR_CONFIG_VALUE]
        for uuid in uuids:
            config_updates = {config_key: config_value}
            if await api.async_set_device_config(uuid, config_updates):
                await api.async_restart_session(uuid)
        await coordinator.async_request_refresh()

    # Rejestracja usług
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_ORIENTATION, handle_set_orientation, schema=SERVICE_SET_ORIENTATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_REFRESH_INTERVAL, handle_set_refresh_interval, schema=SERVICE_SET_REFRESH_INTERVAL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_SLEEP_MODE, handle_set_sleep_mode, schema=SERVICE_SET_SLEEP_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_CONFIG, handle_set_config, schema=SERVICE_SET_CONFIG_SCHEMA)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Integracja Visionect Joan została pomyślnie zainicjalizowana.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usuwa wpis konfiguracyjny."""
    services_to_remove = [
        SERVICE_SET_URL,
        SERVICE_SET_ORIENTATION,
        SERVICE_SET_REFRESH_INTERVAL,
        SERVICE_SET_SLEEP_MODE,
        SERVICE_SET_CONFIG
    ]
    
    for service in services_to_remove:
        hass.services.async_remove(DOMAIN, service)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok