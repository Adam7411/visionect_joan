# custom_components/visionect_joan/sensor.py
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    UnitOfInformation,
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfTime
)
import logging

from .const import (
    DOMAIN, STATE_ONLINE, STATE_OFFLINE,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS
)
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

# Sensor definitions: (device_class, icon, state_class, enabled_by_default)
SENSOR_TYPES = {
    "state": (None, "mdi:tablet", None, True),
    "battery": (SensorDeviceClass.BATTERY, "mdi:battery", SensorStateClass.MEASUREMENT, True),
    "temperature": (SensorDeviceClass.TEMPERATURE, "mdi:thermometer", SensorStateClass.MEASUREMENT, True),
    "rssi": (SensorDeviceClass.SIGNAL_STRENGTH, "mdi:wifi", SensorStateClass.MEASUREMENT, True),
    "uptime": (SensorDeviceClass.DURATION, "mdi:timer", SensorStateClass.TOTAL_INCREASING, True),
    "battery_voltage": (SensorDeviceClass.VOLTAGE, "mdi:flash", SensorStateClass.MEASUREMENT, False),
    "display_rotation": (None, "mdi:screen-rotation", None, True),
    "application_version": (None, "mdi:package-variant", None, False),
    "storage_free": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "storage_total": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "storage_used": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "error_count": (None, "mdi:alert-circle", SensorStateClass.TOTAL_INCREASING, False),
    "restart_count": (None, "mdi:restart", SensorStateClass.TOTAL_INCREASING, False),
}

# Unit definitions
SENSOR_UNITS = {
    "battery": PERCENTAGE,
    "temperature": UnitOfTemperature.CELSIUS,
    "rssi": "dBm",
    "uptime": UnitOfTime.SECONDS,
    "storage_free": UnitOfInformation.MEGABYTES,
    "storage_total": UnitOfInformation.MEGABYTES,
    "storage_used": UnitOfInformation.MEGABYTES,
    "battery_voltage": UnitOfElectricPotential.VOLT,
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectSensor(coordinator, uuid, sensor_type)
            for uuid in coordinator.data
            for sensor_type in SENSOR_TYPES
        )

class VisionectSensor(VisionectEntity, SensorEntity):
    """Represents a Visionect sensor."""

    def __init__(self, coordinator, uuid, sensor_type):
        super().__init__(coordinator, uuid)
        self.sensor_type = sensor_type
        sensor_config = SENSOR_TYPES[sensor_type]

        self._attr_translation_key = sensor_type
        self._attr_unique_id = f"{uuid}_{sensor_type}"
        self._attr_device_class = sensor_config[0]
        self._attr_icon = sensor_config[1]
        self._attr_state_class = sensor_config[2]
        self._attr_entity_registry_enabled_default = sensor_config[3]
        self._attr_native_unit_of_measurement = SENSOR_UNITS.get(sensor_type)

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        device_data = self.coordinator.data.get(self.uuid, {})
        status = device_data.get("Status", {})
        config = device_data.get("Config", {})

        def _get_value_or_none(value):
            if value is None or (isinstance(value, str) and value.lower() in UNKNOWN_STRINGS):
                return None
            return value

        try:
            if self.sensor_type == "state":
                api_state = device_data.get("State")
                return STATE_ONLINE if api_state and api_state.lower() == "online" else STATE_OFFLINE

            if self.sensor_type == "battery":
                return _get_value_or_none(status.get("Battery"))
            if self.sensor_type == "temperature":
                return _get_value_or_none(status.get("Temperature"))
            if self.sensor_type == "rssi":
                return _get_value_or_none(status.get("RSSI"))
            if self.sensor_type == "uptime":
                return _get_value_or_none(status.get("Uptime"))
            if self.sensor_type == "battery_voltage":
                return _get_value_or_none(status.get("BatteryVoltage"))
            if self.sensor_type == "display_rotation":
                rotation_val = config.get("DisplayRotation")
                if rotation_val is not None:
                    return DISPLAY_ROTATIONS.get(str(rotation_val), f"Unknown ({rotation_val})")
                return None
            if self.sensor_type == "application_version":
                return _get_value_or_none(status.get("ApplicationVersion"))
            if self.sensor_type == "storage_free":
                free_str = _get_value_or_none(status.get("FsFreeSize"))
                return round(float(free_str) / (1024 * 1024), 2) if free_str else None
            if self.sensor_type == "storage_total":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                return round(float(total_str) / (1024 * 1024), 2) if total_str else None
            if self.sensor_type == "storage_used":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                free_str = _get_value_or_none(status.get("FsFreeSize"))
                if total_str and free_str:
                    return round((float(total_str) - float(free_str)) / (1024 * 1024), 2)
                return None
            if self.sensor_type == "error_count":
                return _get_value_or_none(status.get("ErrorCount", 0))
            if self.sensor_type == "restart_count":
                return _get_value_or_none(status.get("RestartCount", 0))

        except (TypeError, ValueError) as e:
            _LOGGER.warning(f"Error processing value for sensor {self.unique_id}: {e}")
            return None

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {}
        device_data = self.coordinator.data.get(self.uuid, {})
        config = device_data.get("Config", {})

        if self.sensor_type == "state":
            configured_url = config.get("Url")
            attrs["configured_url"] = configured_url if configured_url and configured_url.lower() not in UNKNOWN_STRINGS else None

        if self.sensor_type == "display_rotation":
            attrs["available_rotations"] = list(DISPLAY_ROTATIONS.keys())
            attrs["rotation_id"] = config.get("DisplayRotation")

        return attrs if attrs else None