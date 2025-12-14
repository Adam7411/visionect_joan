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
    """Set up text entities based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectDeviceNameText(coordinator, uuid) for uuid in coordinator.data
        )

class VisionectDeviceNameText(VisionectEntity, TextEntity):
    """Text entity to change the name of the Visionect device."""

    def __init__(self, coordinator, uuid: str):
        """Initialize the entity."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "device_name"
        self._attr_unique_id = f"{uuid}_device_name"
        self._attr_icon = "mdi:form-textbox"

    @property
    def native_value(self) -> str | None:
        """Return the current name of the device."""
        device_data = self.coordinator.data.get(self.uuid, {})
        config = device_data.get("Config", {})
        name = config.get("Name")
        if name and str(name).lower() not in UNKNOWN_STRINGS:
            return name
        return self.uuid # Return UUID as a fallback

    async def async_set_value(self, value: str) -> None:
        """Set a new name for the device."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        
        _LOGGER.debug(f"Setting new name for {self.uuid}: '{value}'")
        
        if await api.async_set_device_name(self.uuid, value):
            _LOGGER.info(f"Name for {self.uuid} was successfully changed to '{value}'.")
            # Manually update data in the coordinator for an immediate UI effect
            if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["Config"]["Name"] = value
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to set new name for {self.uuid}.")