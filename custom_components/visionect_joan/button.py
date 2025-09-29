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
    """Set up button entities based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        entities = []
        for uuid in coordinator.data:
            entities.append(VisionectForceRefreshButton(coordinator, uuid))
            entities.append(VisionectRebootButton(coordinator, uuid))
        async_add_entities(entities)

class VisionectForceRefreshButton(VisionectEntity, ButtonEntity):
    """Button entity to force a refresh of the Visionect device screen."""

    def __init__(self, coordinator, uuid: str):
        """Initialize the button entity."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "force_refresh"
        self._attr_unique_id = f"{uuid}_force_refresh"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        _LOGGER.info(f"Force refresh button pressed for device {self.uuid}")
        
        if await api.async_restart_session(self.uuid):
            _LOGGER.info(f"Session for {self.uuid} was successfully restarted (refreshed).")
        else:
            _LOGGER.error(f"Failed to restart session for {self.uuid}")
        
        await self.coordinator.async_request_refresh()

class VisionectRebootButton(VisionectEntity, ButtonEntity):
    """Button entity to reboot the Visionect device."""

    def __init__(self, coordinator, uuid: str):
        """Initialize the button entity."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "reboot_device"
        self._attr_unique_id = f"{uuid}_reboot_device"
        self._attr_icon = "mdi:restart"
        self._attr_entity_registry_enabled_default = False 

    async def async_press(self) -> None:
        """Handle the button press."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        _LOGGER.warning(f"Reboot requested for device {self.uuid} via button press.")
        
        if await api.async_reboot_device(self.uuid):
            _LOGGER.info(f"Reboot command for {self.uuid} was sent successfully.")
        else:
            _LOGGER.error(f"Failed to send reboot command for {self.uuid}")