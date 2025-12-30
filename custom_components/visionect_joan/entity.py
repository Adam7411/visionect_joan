# custom_components/visionect_joan/entity.py

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import CONF_HOST  # <-- POPRAWKA: dodano import CONF_HOST

from .const import DOMAIN, MODEL_JOAN6, UNKNOWN_STRINGS

class VisionectEntity(CoordinatorEntity):
    """Base class for all Visionect entities."""

    def __init__(self, coordinator, uuid: str):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.uuid = uuid
        
        # With _attr_has_entity_name = True in child entities, Home Assistant
        # will prefix the entity's name with the device name automatically.
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for the parent device."""
        device_data = self.coordinator.data.get(self.uuid, {})
        status = device_data.get("Status", {})
        config = device_data.get("Config", {})
        
        device_name = config.get("Name")
        if not device_name or str(device_name).lower() in UNKNOWN_STRINGS:
            device_name = self.uuid

        config_url = None
        # Expose the Visionect server URL as configuration_url if available
        if hasattr(self.coordinator, 'config_entry'):
            host = self.coordinator.config_entry.data.get(CONF_HOST)  # <-- POPRAWKA: używamy CONF_HOST zamiast 'host'
            if host:
                if not host.startswith(('http://', 'https://')):
                    host = f"http://{host}"
                config_url = host

        return DeviceInfo(
            identifiers={(DOMAIN, self.uuid)},
            name=device_name,
            manufacturer="Visionect",
            model=MODEL_JOAN6,
            sw_version=status.get("ApplicationVersion"),
            configuration_url=config_url
        )