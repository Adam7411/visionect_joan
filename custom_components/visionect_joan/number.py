# custom_components/visionect_joan/number.py
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTime

from .const import DOMAIN
from .entity import VisionectEntity
# ---> NOWOŚĆ: Importujemy nazwę zdarzenia z __init__.py <---
from .__init__ import EVENT_COMMAND_RESULT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja encji number na podstawie wpisu konfiguracyynego."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectReloadIntervalNumber(coordinator, uuid) for uuid in coordinator.data
        )

class VisionectReloadIntervalNumber(VisionectEntity, NumberEntity):
    """Encja number do ustawiania interwału odświeżania (ReloadTimeout)."""

    def __init__(self, coordinator, uuid: str):
        """Inicjalizacja encji."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "reload_interval"
        self._attr_unique_id = f"{uuid}_reload_interval"
        self._attr_icon = "mdi:timer-sync-outline"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_native_min_value = 0
        self._attr_native_max_value = 86400
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Zwraca aktualną wartość interwału odświeżania."""
        device_data = self.coordinator.data.get(self.uuid, {})
        config = device_data.get("Config", {})
        reload_timeout_str = config.get("ReloadTimeout", "0")

        try:
            return float(reload_timeout_str)
        except (ValueError, TypeError):
            _LOGGER.warning(f"Nie udało się sparsować ReloadTimeout dla {self.uuid}: '{reload_timeout_str}'")
            return None

    # ---> ZMIANA: Całkowicie nowa, poprawiona logika ustawiania wartości <---
    async def async_set_native_value(self, value: float) -> None:
        """Ustawia nową wartość interwału odświeżania i restartuje sesję."""
        api = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        
        timeout_str = str(int(value))
        status = "failure"
        
        _LOGGER.debug(f"Ustawianie ReloadTimeout dla {self.uuid} na {timeout_str}s")
        success = await api.async_set_reload_timeout(self.uuid, timeout_str)

        if success:
            _LOGGER.info(f"ReloadTimeout dla {self.uuid} ustawiony. Restartowanie sesji, aby zastosować zmiany.")
            # Kluczowy krok: Restartujemy sesję, aby urządzenie pobrało nowe ustawienie.
            if await api.async_restart_session(self.uuid):
                _LOGGER.info(f"Sesja dla {self.uuid} pomyślnie zrestartowana.")
                status = "success"
                # Ręcznie aktualizujemy wartość w koordynatorze dla natychmiastowego efektu w UI
                if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                    self.coordinator.data[self.uuid]["Config"]["ReloadTimeout"] = timeout_str
                    self.async_write_ha_state()
            else:
                _LOGGER.error(f"Nie udało się zrestartować sesji dla {self.uuid} po zmianie ReloadTimeout.")
        else:
            _LOGGER.error(f"Nie udało się ustawić ReloadTimeout dla {self.uuid}.")

        # Emitujemy zdarzenie, aby automatyzacje mogły reagować na powodzenie lub błąd
        self.hass.bus.async_fire(EVENT_COMMAND_RESULT, {
            "uuid": self.uuid,
            "service": "number.set_value",
            "entity_id": self.entity_id,
            "status": status,
            "params": {"value": timeout_str}
        })
        
        # Prosimy o pełne odświeżenie danych w tle
        await self.coordinator.async_request_refresh()