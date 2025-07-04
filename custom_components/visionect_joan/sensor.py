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
    DEFAULT_REFRESH_INTERVAL, IP_UNKNOWN
)
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    # Istniejące sensory
    "state": ("Status", None, None, "mdi:tablet", None, True),
    "battery": ("Bateria", SensorDeviceClass.BATTERY, PERCENTAGE, "mdi:battery", SensorStateClass.MEASUREMENT, True),
    "temperature": ("Temperatura", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorStateClass.MEASUREMENT, True),
    "rssi": ("Sygnał WiFi", SensorDeviceClass.SIGNAL_STRENGTH, "dBm", "mdi:wifi", SensorStateClass.MEASUREMENT, True),
    "uptime": ("Czas pracy", SensorDeviceClass.DURATION, UnitOfTime.SECONDS, "mdi:timer", SensorStateClass.TOTAL_INCREASING, True),
    "storage_free": ("Wolne miejsce", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "battery_voltage": ("Napięcie baterii", SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, "mdi:flash", SensorStateClass.MEASUREMENT, False),
    "refresh_interval": ("Interwał odświeżania", SensorDeviceClass.DURATION, UnitOfTime.SECONDS, "mdi:timer-cog", SensorStateClass.MEASUREMENT, True),
    "uuid": ("UUID", None, None, "mdi:identifier", None, False),
    
    # NOWE SENSORY:
    "ip_address": ("Adres IP", None, None, "mdi:ip-network", None, True),
    "mac_address": ("Adres MAC", None, None, "mdi:lan", None, False),
    "application_version": ("Wersja aplikacji", None, None, "mdi:package-variant", None, True),
    "backend_version": ("Wersja backend", None, None, "mdi:server", None, False),
    "current_url": ("Aktualny URL", None, None, "mdi:web", None, True),
    "last_seen": ("Ostatnio widziany", SensorDeviceClass.TIMESTAMP, None, "mdi:clock-outline", None, True),
    "memory_usage": ("Użycie pamięci", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:memory", SensorStateClass.MEASUREMENT, False),
    "storage_total": ("Całkowita pamięć", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "storage_used": ("Używana pamięć", SensorDeviceClass.DATA_SIZE, UnitOfInformation.MEGABYTES, "mdi:harddisk", SensorStateClass.MEASUREMENT, False),
    "display_orientation": ("Orientacja ekranu", None, None, "mdi:screen-rotation", None, True),
    "sleep_mode": ("Tryb uśpienia", None, None, "mdi:sleep", None, True),
    "charging_status": ("Status ładowania", None, None, "mdi:battery-charging", None, True),
    "network_type": ("Typ sieci", None, None, "mdi:network", None, True),
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

            # Istniejące sensory
            if self.sensor_type == "battery":
                return status.get("Battery")
            if self.sensor_type == "temperature":
                return status.get("Temperature")
            if self.sensor_type == "rssi":
                return status.get("RSSI")
            if self.sensor_type == "uptime":
                return status.get("Uptime")
            if self.sensor_type == "storage_free":
                free_str = status.get("FsFreeSize")
                return round(float(free_str) / (1024 * 1024), 2) if free_str is not None else None
            if self.sensor_type == "battery_voltage":
                return status.get("BatteryVoltage")
            if self.sensor_type == "refresh_interval":
                return config.get("RefreshInterval", DEFAULT_REFRESH_INTERVAL)
                
            # NOWE SENSORY:
            if self.sensor_type == "ip_address":
                return status.get("IPAddress", IP_UNKNOWN)
            if self.sensor_type == "mac_address":
                return status.get("MacAddress")
            if self.sensor_type == "application_version":
                return status.get("ApplicationVersion")
            if self.sensor_type == "backend_version":
                return status.get("BackendVersion")
            if self.sensor_type == "current_url":
                return config.get("Url")
            if self.sensor_type == "last_seen":
                # Konwertuj timestamp na format datetime
                timestamp = status.get("LastSeen")
                if timestamp:
                    from datetime import datetime, timezone
                    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
                return None
            if self.sensor_type == "memory_usage":
                mem_str = status.get("MemoryUsage")
                return round(float(mem_str) / (1024 * 1024), 2) if mem_str is not None else None
            if self.sensor_type == "storage_total":
                total_str = status.get("FsTotalSize")
                return round(float(total_str) / (1024 * 1024), 2) if total_str is not None else None
            if self.sensor_type == "storage_used":
                total_str = status.get("FsTotalSize")
                free_str = status.get("FsFreeSize")
                if total_str and free_str:
                    return round((float(total_str) - float(free_str)) / (1024 * 1024), 2)
                return None
            if self.sensor_type == "display_orientation":
                return config.get("Orientation", "Unknown")
            if self.sensor_type == "sleep_mode":
                return config.get("SleepMode", "Unknown")
            if self.sensor_type == "charging_status":
                return status.get("ChargingStatus", "Unknown")
            if self.sensor_type == "network_type":
                return status.get("NetworkType", "Unknown")
            if self.sensor_type == "error_count":
                return status.get("ErrorCount", 0)
            if self.sensor_type == "restart_count":
                return status.get("RestartCount", 0)
                
            return None
        except (TypeError, ValueError) as e:
            _LOGGER.warning(f"Błąd przetwarzania wartości dla sensora {self.unique_id}: {e}")
            return None

    @property
    def extra_state_attributes(self):
        if self.sensor_type == "state":
            config = self.coordinator.data.get(self.uuid, {}).get("Config", {})
            return {"configured_url": config.get("Url")}
        return None