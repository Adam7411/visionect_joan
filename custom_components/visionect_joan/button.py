import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

class VisionectButtonBase(VisionectEntity, ButtonEntity):
    """Bazowa klasa dla przycisków Visionect."""

    def __init__(self, coordinator, uuid, api):
        """Inicjalizacja przycisku."""
        super().__init__(coordinator, uuid)
        self._api = api


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja przycisków na podstawie wpisu konfiguracyjnego."""
    visionect_data = hass.data[DOMAIN][entry.entry_id]
    api = visionect_data["api"]
    coordinator = visionect_data["coordinator"]

    entities = []
    if coordinator.data:
        for uuid in coordinator.data:
            entities.extend([
                VisionectRebootButton(coordinator, uuid, api),
                VisionectRestartSessionButton(coordinator, uuid, api),
                VisionectForceRefreshButton(coordinator, uuid, api),
                VisionectClearScreenButton(coordinator, uuid, api),
            ])

    async_add_entities(entities)


class VisionectRebootButton(VisionectButtonBase):
    """Przycisk do restartowania urządzenia Visionect."""
    
    _attr_icon = "mdi:restart"
    _attr_translation_key = "reboot"

    def __init__(self, coordinator, uuid, api):
        """Inicjalizacja."""
        super().__init__(coordinator, uuid, api)
        self._attr_unique_id = f"{uuid}_reboot"

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku restartu."""
        _LOGGER.info(f"Wysyłanie komendy restartu do urządzenia: {self.uuid}")
        if await self._api.async_reboot_device(self.uuid):
            _LOGGER.info(f"Komenda restartu wysłana pomyślnie do {self.uuid}")
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Nie udało się wysłać komendy restartu do {self.uuid}")


class VisionectRestartSessionButton(VisionectButtonBase):
    """Przycisk do restartowania sesji na urządzeniu Visionect."""

    _attr_icon = "mdi:restart-alert"
    _attr_translation_key = "restart_session"

    def __init__(self, coordinator, uuid, api):
        """Inicjalizacja."""
        super().__init__(coordinator, uuid, api)
        self._attr_unique_id = f"{uuid}_restart_session"

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku restartu sesji."""
        _LOGGER.info(f"Wysyłanie komendy restartu sesji do urządzenia: {self.uuid}")
        if await self._api.async_restart_session(self.uuid):
            _LOGGER.info(f"Komenda restartu sesji wysłana pomyślnie do {self.uuid}")
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Nie udało się wysłać komendy restartu sesji do {self.uuid}")


class VisionectForceRefreshButton(VisionectButtonBase):
    """Przycisk do wymuszenia odświeżenia ekranu na urządzeniu Visionect."""

    _attr_icon = "mdi:refresh"
    _attr_translation_key = "force_refresh"

    def __init__(self, coordinator, uuid, api):
        """Inicjalizacja."""
        super().__init__(coordinator, uuid, api)
        self._attr_unique_id = f"{uuid}_force_refresh"

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku wymuszenia odświeżenia."""
        _LOGGER.info(f"Wysyłanie komendy odświeżenia do urządzenia: {self.uuid}")
        if await self._api.async_force_refresh(self.uuid):
            _LOGGER.info(f"Komenda odświeżenia wysłana pomyślnie do {self.uuid}")
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Nie udało się wysłać komendy odświeżenia do {self.uuid}")


class VisionectClearScreenButton(VisionectButtonBase):
    """Przycisk do czyszczenia ekranu urządzenia Visionect."""

    _attr_icon = "mdi:notification-clear-all"
    _attr_translation_key = "clear_screen"

    def __init__(self, coordinator, uuid, api):
        """Inicjalizacja."""
        super().__init__(coordinator, uuid, api)
        self._attr_unique_id = f"{uuid}_clear_screen"

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku czyszczenia ekranu."""
        _LOGGER.info(f"Wysyłanie komendy czyszczenia ekranu do urządzenia: {self.uuid}")
        if await self._api.async_clear_screen(self.uuid):
            _LOGGER.info(f"Komenda czyszczenia ekranu wysłana pomyślnie do {self.uuid}")
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Nie udało się wysłać komendy czyszczenia ekranu do {self.uuid}")