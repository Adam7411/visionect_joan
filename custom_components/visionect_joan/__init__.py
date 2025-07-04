# custom_components/visionect_joan/__init__.py
import logging
import time
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
        MIN_REFRESH_INTERVAL, MAX_REFRESH_INTERVAL
    )
except ImportError as e:
    _LOGGER.critical(f"Krytyczny błąd importu w __init__.py: {e}")
    raise

PLATFORMS = ["sensor", "button"]

# Definicje usług
SERVICE_SET_URL = "set_url"
SERVICE_SET_CONFIG = "set_config"
SERVICE_SET_SLEEP_MODE = "set_sleep_mode"
SERVICE_SET_ORIENTATION = "set_orientation"
SERVICE_CLEAR_SCREEN = "clear_screen"
SERVICE_SET_REFRESH_INTERVAL = "set_refresh_interval"

# Atrybuty usług
ATTR_URL = "url"
ATTR_CONFIG_KEY = "config_key"
ATTR_CONFIG_VALUE = "config_value"
ATTR_SLEEP_MODE = "sleep_mode"
ATTR_ORIENTATION = "orientation"
ATTR_REFRESH_INTERVAL = "refresh_interval"

# Schematy walidacji usług
SERVICE_SET_URL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_URL): cv.url,
    }
)

SERVICE_SET_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_CONFIG_KEY): cv.string,
        vol.Required(ATTR_CONFIG_VALUE): cv.string,
    }
)

SERVICE_SET_SLEEP_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_SLEEP_MODE): vol.In(["manual", "auto", "disabled"]),
    }
)

SERVICE_SET_ORIENTATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_ORIENTATION): vol.In(["portrait", "landscape", "portrait_flipped", "landscape_flipped"]),
    }
)

SERVICE_CLEAR_SCREEN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
    }
)

SERVICE_SET_REFRESH_INTERVAL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_REFRESH_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=MIN_REFRESH_INTERVAL, max=MAX_REFRESH_INTERVAL)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja integracji na podstawie wpisu konfiguracyjnego."""
    _LOGGER.info("Rozpoczynanie konfiguracji integracji Visionect Joan (async_setup_entry).")
    start_time = time.time()
    
    hass.data.setdefault(DOMAIN, {})

    try:
        api = VisionectAPI(
            hass,
            entry.data[CONF_HOST],
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            entry.data.get(CONF_API_KEY),
            entry.data.get(CONF_API_SECRET)
        )
    except Exception as e:
        _LOGGER.critical(f"Nie udało się stworzyć instancji VisionectAPI: {e}")
        return False
    
    _LOGGER.debug("Testowanie autentykacji...")
    if not await api.async_test_authentication():
        _LOGGER.error("Autentykacja nie powiodła się. Nie można załadować integracji.")
        return False
    _LOGGER.debug("Autentykacja pomyślna.")

    async def async_update_data():
        _LOGGER.debug("Rozpoczynanie aktualizacji danych z Visionect API.")
        update_start_time = time.time()
        
        devices_summary = await api.async_get_all_devices()
        if devices_summary is None:
            _LOGGER.error("Błąd podczas pobierania listy urządzeń. Otrzymano None.")
            return {}

        if not devices_summary:
            _LOGGER.warning("Nie znaleziono żadnych urządzeń Visionect.")
            return {}
        
        _LOGGER.debug(f"Znaleziono {len(devices_summary)} urządzeń. Przetwarzanie...")
        data = {}
        for i, device_summary in enumerate(devices_summary):
            uuid = device_summary.get("Uuid")
            if not uuid:
                continue

            _LOGGER.debug(f"Przetwarzanie urządzenia {i+1}/{len(devices_summary)}: {uuid}")
            try:
                device_details = await api.async_get_device_data(uuid)
                session_data = await api.async_get_session_data(uuid)

                if not device_details:
                    _LOGGER.warning(f"Brak danych szczegółowych dla urządzenia {uuid}, pomijanie.")
                    continue

                final_data = device_details
                if session_data:
                    final_data["Session"] = session_data

                if "Config" not in final_data:
                    final_data["Config"] = {}
                
                device_name_from_summary = device_summary.get("Options", {}).get("Name")
                
                if device_name_from_summary:
                    _LOGGER.debug(f"Znaleziono nazwę dla {uuid}: '{device_name_from_summary}'")
                    final_data["Config"]["Name"] = device_name_from_summary
                else:
                    _LOGGER.debug(f"Nie znaleziono nazwy dla {uuid} w 'Options', zostanie użyta domyślna.")

                data[uuid] = final_data
            except Exception as e:
                _LOGGER.exception(f"Nieoczekiwany błąd podczas przetwarzania urządzenia {uuid}")
        
        _LOGGER.debug(f"Zakończono aktualizację danych w {time.time() - update_start_time:.2f} sekundy.")
        return data

    _LOGGER.debug("Tworzenie koordynatora danych.")
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"visionect_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    _LOGGER.debug("Wykonywanie pierwszej aktualizacji danych...")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Pierwsza aktualizacja zakończona.")

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    device_reg = dr.async_get(hass)

    async def _handle_service_call(call: ServiceCall, api_method, *args):
        """Pomocnicza funkcja do obsługi wywołań usług."""
        target_device_ids = call.data[ATTR_DEVICE_ID]
        if isinstance(target_device_ids, str):
            target_device_ids = [target_device_ids]

        for device_id in target_device_ids:
            device_entry = device_reg.async_get(device_id)
            if not device_entry:
                _LOGGER.warning(f"Nie znaleziono urządzenia o ID: {device_id}")
                continue
            
            uuid = next((identifier[1] for identifier in device_entry.identifiers if identifier[0] == DOMAIN), None)
            if uuid:
                _LOGGER.info(f"Wywołanie usługi {call.service} dla urządzenia {uuid} z danymi: {call.data}")
                success = await api_method(uuid, *args)
                if success:
                    await coordinator.async_request_refresh()
            else:
                _LOGGER.warning(f"Nie można znaleźć identyfikatora UUID dla urządzenia {device_id} w domenie {DOMAIN}")

    async def handle_set_url(call: ServiceCall):
        await _handle_service_call(call, api.async_set_device_url, call.data[ATTR_URL])

    async def handle_set_config(call: ServiceCall):
        await _handle_service_call(call, api.async_set_device_config, call.data[ATTR_CONFIG_KEY], call.data[ATTR_CONFIG_VALUE])

    async def handle_set_sleep_mode(call: ServiceCall):
        await _handle_service_call(call, api.async_set_device_config, "SleepMode", call.data[ATTR_SLEEP_MODE])

    async def handle_set_orientation(call: ServiceCall):
        await _handle_service_call(call, api.async_set_device_config, "Orientation", call.data[ATTR_ORIENTATION])

    async def handle_clear_screen(call: ServiceCall):
        await _handle_service_call(call, api.async_clear_screen)

    async def handle_set_refresh_interval(call: ServiceCall):
        await _handle_service_call(call, api.async_set_device_config, "RefreshInterval", str(call.data[ATTR_REFRESH_INTERVAL]))

    # Rejestracja usług
    hass.services.async_register(DOMAIN, SERVICE_SET_URL, handle_set_url, schema=SERVICE_SET_URL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_CONFIG, handle_set_config, schema=SERVICE_SET_CONFIG_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_SLEEP_MODE, handle_set_sleep_mode, schema=SERVICE_SET_SLEEP_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_ORIENTATION, handle_set_orientation, schema=SERVICE_SET_ORIENTATION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_SCREEN, handle_clear_screen, schema=SERVICE_CLEAR_SCREEN_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_REFRESH_INTERVAL, handle_set_refresh_interval, schema=SERVICE_SET_REFRESH_INTERVAL_SCHEMA)

    _LOGGER.debug("Przekazywanie konfiguracji do platform (sensor, button)...")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info(f"Integracja Visionect Joan została pomyślnie zainicjalizowana w {time.time() - start_time:.2f} sekundy.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usuwa wpis konfiguracyjny."""
    _LOGGER.info("Rozpoczynanie usuwania integracji Visionect Joan.")
    
    # Usunięcie zarejestrowanych usług
    hass.services.async_remove(DOMAIN, SERVICE_SET_URL)
    hass.services.async_remove(DOMAIN, SERVICE_SET_CONFIG)
    hass.services.async_remove(DOMAIN, SERVICE_SET_SLEEP_MODE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_ORIENTATION)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_SCREEN)
    hass.services.async_remove(DOMAIN, SERVICE_SET_REFRESH_INTERVAL)
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Integracja Visionect Joan została pomyślnie usunięta.")
    else:
        _LOGGER.warning("Problem podczas usuwania platform integracji Visionect Joan.")
    return unload_ok