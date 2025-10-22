import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UNKNOWN_STRINGS
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

# Definitions for binary sensors
# Format: (DeviceClass, Icon, Enabled by default)
BINARY_SENSOR_TYPES = {
    "is_charging": (BinarySensorDeviceClass.BATTERY_CHARGING, "mdi:power-plug", True),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectBinarySensor(coordinator, uuid, sensor_type)
            for uuid in coordinator.data
            for sensor_type in BINARY_SENSOR_TYPES
        )

class VisionectBinarySensor(VisionectEntity, BinarySensorEntity):
    """Binary sensor for a Visionect device."""

    def __init__(self, coordinator, uuid, sensor_type):
        super().__init__(coordinator, uuid)
        self.sensor_type = sensor_type
        
        sensor_config = BINARY_SENSOR_TYPES[sensor_type]
        
        self._attr_translation_key = sensor_type
        self._attr_unique_id = f"{uuid}_{sensor_type}"
        self._attr_device_class = sensor_config[0]
        self._attr_icon = sensor_config[1]
        self._attr_entity_registry_enabled_default = sensor_config[2]

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        device_data = self.coordinator.data.get(self.uuid, {})
        status = device_data.get("Status", {})

        def _get_value_or_none(value):
            if value is None or (isinstance(value, str) and value.lower() in UNKNOWN_STRINGS):
                return None
            return value

        if self.sensor_type == "is_charging":
            # FIX: We check the "Charger" field. We assume a value of '1' means charging.
            charger_status = _get_value_or_none(status.get("Charger"))
            if charger_status is not None:
                return str(charger_status) == "1"
            return None
        
        return None