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
    DEFAULT_REFRESH_INTERVAL, IP_UNKNOWN, UNKNOWN_STRINGS
)
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES = {
    # Podstawowe sensory
    "state": ("Status", None, None, "mdi:tablet", None, True),
    "battery": ("Bateria", SensorDeviceClass.BATTERY, PERCENTAGE, "mdi:battery", SensorStateClass.MEASUREMENT, True),
    "temperature": ("Temperatura", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorStateClass.MEASUREMENT, True),
    "rssi": ("Sygnał WiFi", SensorDeviceClass.SIGNAL_STRENGTH, "dBm", "mdi:wifi", SensorStateClass.MEASUREMENT, True),
    "uptime": ("Czas pracy", SensorDeviceClass.DURATION, UnitOfTime.SECONDS, "mdi:timer", SensorStateClass.TOTAL_INCREASING, True),
    "storage_free": ("Wolne miejsce", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "battery_voltage": ("Napięcie baterii", SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, "mdi:flash", SensorStateClass.MEASUREMENT, False),
    "refresh_interval": ("Interwał odświeżania", SensorDeviceClass.DURATION, UnitOfTime.SECONDS, "mdi:timer-cog", SensorStateClass.MEASUREMENT, True),
    "uuid": ("UUID", None, None, "mdi:identifier", None, False),
    
    # Pozostałe sensory
    "application_version": ("Wersja aplikacji", None, None, "mdi:package-variant", None, True),
    "storage_total": ("Całkowita pamięć", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "storage_used": ("Używana pamięć", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "error_count": ("Liczba błędów", None, None, "mdi:alert-circle", SensorStateClass.TOTAL_INCREASING, False),
    "restart_count": ("Liczba restartów", None, None, "mdi:restart", SensorStateClass.TOTAL_INCREASING, False),
}


async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Konfiguracja sensorów."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []
    if coordinator.data:
        for uuid in coordinator.data:
            for sensor_type in SENSOR_TYPES:
                entities.append(VisionectSensor(coordinator, uuid, sensor_type))
    async_add_entities(entities)

class VisionectSensor(VisionectEntity, SensorEntity):
    """Sensor dla urządzenia Visionect."""

    def __init__(self, coordinator, uuid, sensor_type):
        super().__init__(coordinator, uuid)
        self.sensor_type = sensor_type
        
        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = sensor_config[0]
        self._attr_unique_id = f"{uuid}_{sensor_type}"
        self._attr_device_class = sensor_config[1]
        self._attr_native_unit_of_measurement = sensor_config[2]
        self._attr_icon = sensor_config[3]
        self._attr_state_class = sensor_config[4]
        self._attr_entity_registry_enabled_default = sensor_config[5]

    @property
    def native_value(self):
        """Zwraca natywną wartość sensora."""
        if self.sensor_type == "uuid":
            return self.uuid

        device_data = self.coordinator.data.get(self.uuid, {})
        
        try:
            if self.sensor_type == "state":
                api_state = device_data.get("State")
                if api_state and isinstance(api_state, str):
                    return STATE_ONLINE if api_state.lower() == "online" else STATE_OFFLINE
                return STATE_OFFLINE

            status = device_data.get("Status", {})
            config = device_data.get("Config", {})

            # Helper function to check if a value should be considered None/Unknown
            def _get_value_or_none(value):
                if value is None or (isinstance(value, str) and value.lower() in UNKNOWN_STRINGS):
                    return None
                return value

            # NOWY SENSOR - ADRES IP (USUNIĘTY - nie jest potrzebny)
            # if self.sensor_type == "ip_address":
            #     ip_value = status.get("IPAddress")
            #     if ip_value and str(ip_value).lower() not in UNKNOWN_STRINGS and ip_value != IP_UNKNOWN:
            #         return ip_value
            #     return None

            # Istniejące sensory
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
                if free_str is None: return None
                try:
                    return round(float(free_str) / (1024 * 1024), 2)
                except ValueError:
                    return None
            if self.sensor_type == "battery_voltage":
                return _get_value_or_none(status.get("BatteryVoltage"))
            if self.sensor_type == "refresh_interval":
                return _get_value_or_none(config.get("RefreshInterval", DEFAULT_REFRESH_INTERVAL))
                
            # POZOSTAŁE SENSORY:
            if self.sensor_type == "application_version":
                return _get_value_or_none(status.get("ApplicationVersion"))
            if self.sensor_type == "storage_total":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                if total_str is None: return None
                try:
                    return round(float(total_str) / (1024 * 1024), 2)
                except ValueError:
                    return None
            if self.sensor_type == "storage_used":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                free_str = _get_value_or_none(status.get("FsFreeSize"))
                if total_str is None or free_str is None:
                    return None
                try:
                    return round((float(total_str) - float(free_str)) / (1024 * 1024), 2)
                except ValueError:
                    return None
            if self.sensor_type == "error_count":
                return _get_value_or_none(status.get("ErrorCount", 0))
            if self.sensor_type == "restart_count":
                return _get_value_or_none(status.get("RestartCount", 0))
                
            return None
        except (TypeError, ValueError) as e:
            _LOGGER.warning(f"Błąd przetwarzania wartości dla sensora {self.unique_id}: {e}")
            return None

    @property
    def extra_state_attributes(self):
        """Zwraca dodatkowe atrybuty stanu."""
        if self.sensor_type == "state":
            device_data = self.coordinator.data.get(self.uuid, {})
            config = device_data.get("Config", {})
            configured_url = config.get("Url")
            
            return {"configured_url": configured_url if configured_url and configured_url.lower() not in UNKNOWN_STRINGS else None}
        
        return None