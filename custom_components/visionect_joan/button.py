# custom_components/visionect_joan/button.py
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja encji przycisków na podstawie wpisu konfiguracyjnego."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        entities = []
        for uuid in coordinator.data:
            entities.append(VisionectForceRefreshButton(coordinator, uuid))
            entities.append(VisionectRebootButton(coordinator, uuid))
        async_add_entities(entities)

class VisionectForceRefreshButton(VisionectEntity, ButtonEntity):
    """Encja przycisku do wymuszenia odświeżenia ekranu urządzenia Visionect."""

    def __init__(self, coordinator, uuid: str):
        """Inicjalizacja encji przycisku."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "force_refresh"
        self._attr_unique_id = f"{uuid}_force_refresh"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Obsługuje naciśnięcie przycisku."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        _LOGGER.info(f"Naciśnięto przycisk wymuszenia odświeżenia dla urządzenia {self.uuid}")
        
        if await api.async_restart_session(self.uuid):
            _LOGGER.info(f"Sesja dla {self.uuid} została pomyślnie zrestartowana (odświeżono).")
        else:
            _LOGGER.error(f"Nie udało się zrestartować sesji dla {self.uuid}")
        
        await self.coordinator.async_request_refresh()

class VisionectRebootButton(VisionectEntity, ButtonEntity):
    """Encja przycisku do restartowania urządzenia Visionect."""

    def __init__(self, coordinator, uuid: str):
        """Inicjalizacja encji przycisku."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "reboot_device"
        self._attr_unique_id = f"{uuid}_reboot_device"
        self._attr_icon = "mdi:restart"
        self._attr_entity_registry_enabled_default = False 

    async def async_press(self) -> None:
        """Obsługuje naciśnięcie przycisku."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        _LOGGER.warning(f"Zażądano restartu urządzenia {self.uuid} przez naciśnięcie przycisku.")
        
        if await api.async_reboot_device(self.uuid):
            _LOGGER.info(f"Polecenie restartu dla {self.uuid} zostało wysłane pomyślnie.")
        else:
            _LOGGER.error(f"Nie udało się wysłać polecenia restartu dla {self.uuid}")