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
from homeassistant.helpers.network import get_url
import logging
from datetime import datetime
from urllib.parse import urlparse

from .const import (
    DOMAIN, STATE_ONLINE, STATE_OFFLINE, STATE_SLEEPING,
    UNKNOWN_STRINGS, DISPLAY_ROTATIONS, vss_error_code_sensor_state,
)
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)


def _replace_ha_host_with_alias(url: str, hass: HomeAssistant) -> str:
    """Replace current HA host:port in URL with stable IPHA alias."""
    if not isinstance(url, str) or not url:
        return url
    try:
        ha_url = get_url(hass, allow_external=False, allow_ip=True)
        ha_parsed = urlparse(ha_url)
        target = urlparse(url)
        if target.hostname and ha_parsed.hostname and target.hostname == ha_parsed.hostname:
            # Keep userinfo/port from the target URL, replace only host label.
            auth = ""
            if target.username:
                auth = target.username
                if target.password:
                    auth += f":{target.password}"
                auth += "@"
            port = f":{target.port}" if target.port else ""
            netloc = f"{auth}IPHA{port}"
            return target._replace(netloc=netloc).geturl()
    except Exception:
        pass
    return url


def _format_url_for_sensor_state(url: str) -> str:
    """Return path-only URL label for HA UI state."""
    if not isinstance(url, str) or not url:
        return url
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return parsed.path or "/"
    if url.startswith("data:text/html,"):
        return "data-url"
    return url

# Dictionary of sensor definitions
# Format: (DeviceClass, Icon, StateClass, EnabledByDefault)
SENSOR_TYPES = {
    "state": (SensorDeviceClass.ENUM, "mdi:tablet", None, True),
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
    "error_code": (None, "mdi:alert-circle-outline", None, True),
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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    device_coordinators = entry_data.get("device_coordinators", {})
    if device_coordinators:
        async_add_entities(
            VisionectSensor(device_coordinator, uuid, sensor_type)
            for uuid, device_coordinator in device_coordinators.items()
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
        
        if self._attr_device_class == SensorDeviceClass.ENUM:
            if sensor_type == "state":
                self._attr_options = [STATE_ONLINE, STATE_OFFLINE, STATE_SLEEPING]

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
                val = device_data.get("State", status.get("State"))
                if val is not None:
                    api_state = str(val).lower()
                    if api_state in ["1", "online"]:
                        return STATE_ONLINE
                    elif api_state in ["2", "sleeping"]:
                        return STATE_SLEEPING
                return STATE_OFFLINE
            
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
            
            if self.sensor_type == "configured_url":
                url = _get_value_or_none(config.get("Url"))
                if not url:
                    return None
                display_url = _replace_ha_host_with_alias(url, self.hass)
                return _format_url_for_sensor_state(display_url)

            if self.sensor_type == "connect_reason":
                return _get_value_or_none(status.get("ConnectReason"))
            
            if self.sensor_type == "error_code":
                return vss_error_code_sensor_state(status.get("ErrorCode"))
                
            return None
        except (TypeError, ValueError) as e:
            _LOGGER.warning(f"Error processing value for sensor {self.unique_id}: {e}")
            return None

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if self.sensor_type == "error_code":
            device_data = self.coordinator.data.get(self.uuid, {})
            status = device_data.get("Status", {}) if isinstance(device_data, dict) else {}
            if not isinstance(status, dict):
                return None
            attrs: dict[str, str] = {}
            raw_ec = status.get("ErrorCode")
            if raw_ec is not None and str(raw_ec).strip():
                attrs["raw_error_code"] = str(raw_ec).strip()
            last_status = status.get("LastStatus")
            if last_status is not None and str(last_status).strip():
                attrs["last_status"] = str(last_status).strip()
            return attrs or None

        if self.sensor_type == "configured_url":
            device_data = self.coordinator.data.get(self.uuid, {})
            config = device_data.get("Config", {})
            full_url = config.get("Url")
            
            # W atrybutach trzymamy zawsze PEŁNY, ORYGINALNY adres
            if full_url and full_url.lower() not in UNKNOWN_STRINGS and not full_url.startswith("data:text/html,"):
                return {
                    "full_url": full_url,
                    "full_url_ipha": _replace_ha_host_with_alias(full_url, self.hass),
                }
        
        return None