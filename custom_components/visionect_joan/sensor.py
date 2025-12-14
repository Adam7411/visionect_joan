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
from datetime import datetime

from .const import (
    DOMAIN, STATE_ONLINE, STATE_OFFLINE,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS
)
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

# ---> ZMIANA: Skrócony limit wyświetlania znaków <---
MAX_URL_DISPLAY_LENGTH = 30

# Dictionary of sensor definitions
# Format: (DeviceClass, Icon, StateClass, EnabledByDefault)
SENSOR_TYPES = {
    "state": (None, "mdi:tablet", None, True),
    "battery": (SensorDeviceClass.BATTERY, "mdi:battery", SensorStateClass.MEASUREMENT, True),
    "temperature": (SensorDeviceClass.TEMPERATURE, "mdi:thermometer", SensorStateClass.MEASUREMENT, True),
    "rssi": (SensorDeviceClass.SIGNAL_STRENGTH, "mdi:wifi", SensorStateClass.MEASUREMENT, True),
    "uptime": (SensorDeviceClass.DURATION, "mdi:timer", SensorStateClass.TOTAL_INCREASING, True),
    "storage_free": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "battery_voltage": (SensorDeviceClass.VOLTAGE, "mdi:flash", SensorStateClass.MEASUREMENT, False),
    "uuid": (None, "mdi:identifier", None, False),
    "display_rotation": (None, "mdi:screen-rotation", None, True),
    "application_version": (None, "mdi:package-variant", None, False),
    "storage_total": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "storage_used": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "last_seen": (SensorDeviceClass.TIMESTAMP, "mdi:clock-outline", None, True),
    "configured_url": (None, "mdi:link-variant", None, True),
    # <--- NOWE SENSORY DIAGNOSTYCZNE --->
    "connect_reason": (None, "mdi:connection", None, False),
    "error_code": (None, "mdi:alert-circle-outline", None, False),
}

# Dictionary of units
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
    """Set up the sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectSensor(coordinator, uuid, sensor_type)
            for uuid in coordinator.data
            for sensor_type in SENSOR_TYPES
        )

class VisionectSensor(VisionectEntity, SensorEntity):
    """Sensor for a Visionect device."""

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
        if self.sensor_type == "uuid":
            return self.uuid

        device_data = self.coordinator.data.get(self.uuid, {})
        
        try:
            status = device_data.get("Status", {})
            config = device_data.get("Config", {})

            def _get_value_or_none(value):
                if value is None or (isinstance(value, str) and value.lower() in UNKNOWN_STRINGS):
                    return None
                return value

            if self.sensor_type == "state":
                api_state = device_data.get("State")
                return STATE_ONLINE if api_state and isinstance(api_state, str) and api_state.lower() == "online" else STATE_OFFLINE
            
            if self.sensor_type == "battery":
                return _get_value_or_none(status.get("Battery"))
            if self.sensor_type == "temperature":
                return _get_value_or_none(status.get("Temperature"))
            if self.sensor_type == "rssi":
                return _get_value_or_none(status.get("RSSI"))
            if self.sensor_type == "uptime":
                return _get_value_or_none(status.get("Uptime"))
            if self.sensor_type == "storage_free":
                free_str = _get_value_or_none(status.get("FsFreeSize"))
                return round(float(free_str) / (1024 * 1024), 2) if free_str else None
            if self.sensor_type == "battery_voltage":
                return _get_value_or_none(status.get("BatteryVoltage"))
            if self.sensor_type == "display_rotation":
                rotation = config.get("DisplayRotation")
                return DISPLAY_ROTATIONS.get(str(rotation)) if rotation is not None else None
            if self.sensor_type == "application_version":
                return _get_value_or_none(status.get("ApplicationVersion"))
            if self.sensor_type == "storage_total":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                return round(float(total_str) / (1024 * 1024), 2) if total_str else None
            if self.sensor_type == "storage_used":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                free_str = _get_value_or_none(status.get("FsFreeSize"))
                if total_str and free_str:
                    return round((float(total_str) - float(free_str)) / (1024 * 1024), 2)
                return None
            if self.sensor_type == "last_seen":
                return device_data.get("LastUpdated")
            
            # ---> ZMIENIONA LOGIKA WYŚWIETLANIA URL <---
            if self.sensor_type == "configured_url":
                url = _get_value_or_none(config.get("Url"))
                if not url:
                    return None
                
                # Obsługa specjalnych adresów "data:..."
                if url.startswith("data:text/html,"):
                    if "visionect_snapshot" in url:
                        return "Camera Snapshot"
                    return "Dynamic Content (HTML)"
                
                # Tworzymy kopię do wyświetlania
                display_url = url

                # Podmieniamy konkretne IP na krótki tekst
                # Najpierw pełne adresy z portem
                display_url = display_url.replace("http://192.168.1.200:8123", "IP_HA")
                display_url = display_url.replace("https://192.168.1.200:8123", "IP_HA")
                
                # Potem samo IP (dla pewności, jeśli port jest inny lub go brak)
                display_url = display_url.replace("192.168.1.200", "IP_HA")
                
                # Sprawdzamy długość po skróceniu
                if len(display_url) > MAX_URL_DISPLAY_LENGTH:
                    return f"{display_url[:MAX_URL_DISPLAY_LENGTH-3]}..."
                
                return display_url
            
            # <--- KONIEC ZMIAN URL --->

            if self.sensor_type == "connect_reason":
                return _get_value_or_none(status.get("ConnectReason"))
            
            if self.sensor_type == "error_code":
                return _get_value_or_none(status.get("ErrorCode"))
                
            return None
        except (TypeError, ValueError) as e:
            _LOGGER.warning(f"Error processing value for sensor {self.unique_id}: {e}")
            return None

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if self.sensor_type == "configured_url":
            device_data = self.coordinator.data.get(self.uuid, {})
            config = device_data.get("Config", {})
            full_url = config.get("Url")
            
            # W atrybutach trzymamy zawsze PEŁNY, ORYGINALNY adres
            if full_url and full_url.lower() not in UNKNOWN_STRINGS and not full_url.startswith("data:text/html,"):
                return {"full_url": full_url}
        
        return None