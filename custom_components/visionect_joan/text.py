# custom_components/visionect_joan/text.py
import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UNKNOWN_STRINGS
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja encji text na podstawie wpisu konfiguracyjnego."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectDeviceNameText(coordinator, uuid) for uuid in coordinator.data
        )

class VisionectDeviceNameText(VisionectEntity, TextEntity):
    """Encja text do zmiany nazwy urządzenia Visionect."""

    def __init__(self, coordinator, uuid: str):
        """Inicjalizacja encji."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "device_name"
        self._attr_unique_id = f"{uuid}_device_name"
        self._attr_icon = "mdi:form-textbox"

    @property
    def native_value(self) -> str | None:
        """Zwraca aktualną nazwę urządzenia."""
        device_data = self.coordinator.data.get(self.uuid, {})
        config = device_data.get("Config", {})
        name = config.get("Name")
        if name and str(name).lower() not in UNKNOWN_STRINGS:
            return name
        return self.uuid # Zwróć UUID jako fallback

    async def async_set_value(self, value: str) -> None:
        """Ustawia nową nazwę urządzenia."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        
        _LOGGER.debug(f"Ustawianie nowej nazwy dla {self.uuid}: '{value}'")
        
        if await api.async_set_device_name(self.uuid, value):
            _LOGGER.info(f"Nazwa dla {self.uuid} została pomyślnie zmieniona na '{value}'.")
            # Ręczna aktualizacja danych w koordynatorze dla natychmiastowego efektu w UI
            if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["Config"]["Name"] = value
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Nie udało się ustawić nowej nazwy dla {self.uuid}.")