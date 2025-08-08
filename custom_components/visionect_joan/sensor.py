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
    DEFAULT_REFRESH_INTERVAL, IP_UNKNOWN, UNKNOWN_STRINGS, DISPLAY_ROTATIONS
)
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

# Słownik SENSOR_TYPES z nazwami sensorów
SENSOR_TYPES = {
    # Podstawowe sensory
    "state": (None, "mdi:tablet", None, True, "Stan"),
    "battery": (SensorDeviceClass.BATTERY, "mdi:battery", SensorStateClass.MEASUREMENT, True, "Bateria"),
    "temperature": (SensorDeviceClass.TEMPERATURE, "mdi:thermometer", SensorStateClass.MEASUREMENT, True, "Temperatura"),
    "rssi": (SensorDeviceClass.SIGNAL_STRENGTH, "mdi:wifi", SensorStateClass.MEASUREMENT, True, "Siła sygnału WiFi"),
    "uptime": (SensorDeviceClass.DURATION, "mdi:timer", SensorStateClass.TOTAL_INCREASING, True, "Czas pracy"),
    "storage_free": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False, "Wolne miejsce"),
    "battery_voltage": (SensorDeviceClass.VOLTAGE, "mdi:flash", SensorStateClass.MEASUREMENT, False, "Napięcie baterii"),
    "refresh_interval": (SensorDeviceClass.DURATION, "mdi:timer-cog", SensorStateClass.MEASUREMENT, True, "Interwał odświeżania"),
    "uuid": (None, "mdi:identifier", None, False, "UUID"),
    "display_rotation": (None, "mdi:rotate-3d", None, True, "Orientacja"),
    
    # Pozostałe sensory
    "application_version": (None, "mdi:package-variant", None, True, "Wersja aplikacji"),
    "storage_total": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False, "Całkowite miejsce"),
    "storage_used": (SensorDeviceClass.DATA_SIZE, "mdi:harddisk", SensorStateClass.MEASUREMENT, False, "Zajęte miejsce"),
    "error_count": (None, "mdi:alert-circle", SensorStateClass.TOTAL_INCREASING, False, "Liczba błędów"),
    "restart_count": (None, "mdi:restart", SensorStateClass.TOTAL_INCREASING, False, "Liczba restartów"),
}

# Słownik jednostek
SENSOR_UNITS = {
    "battery": PERCENTAGE,
    "temperature": UnitOfTemperature.CELSIUS,
    "rssi": "dBm",
    "uptime": UnitOfTime.SECONDS,
    "storage_free": UnitOfInformation.MEGABYTES,
    "storage_total": UnitOfInformation.MEGABYTES,
    "storage_used": UnitOfInformation.MEGABYTES,
    "battery_voltage": UnitOfElectricPotential.VOLT,
    "refresh_interval": UnitOfTime.SECONDS,
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
        self._attr_translation_key = sensor_type
        self._attr_unique_id = f"{uuid}_{sensor_type}"
        
        self._attr_device_class = sensor_config[0]
        self._attr_icon = sensor_config[1]
        self._attr_state_class = sensor_config[2]
        self._attr_entity_registry_enabled_default = sensor_config[3]
        self._attr_native_unit_of_measurement = SENSOR_UNITS.get(sensor_type)
        
        # Zapisz nazwę sensora z konfiguracji
        self._sensor_name = sensor_config[4] if len(sensor_config) > 4 else sensor_type.replace('_', ' ').title()

    @property
    def name(self):
        """Zwraca nazwę sensora - nazwę opisową zamiast nazwy urządzenia."""
        return self._sensor_name

    def _get_device_name(self):
        """Pobiera nazwę urządzenia z danych koordynatora."""
        try:
            device_data = self.coordinator.data.get(self.uuid, {})
            config = device_data.get("Config", {})
            name = config.get("Name")
            if name and name.lower() not in UNKNOWN_STRINGS:
                return name
            return f"Urządzenie {self.uuid[-8:]}"  # Ostatnie 8 znaków UUID jako fallback
        except:
            return f"Urządzenie {self.uuid[-8:]}"

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

            def _get_value_or_none(value):
                if value is None or (isinstance(value, str) and value.lower() in UNKNOWN_STRINGS):
                    return None
                return value

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
                try: return round(float(free_str) / (1024 * 1024), 2)
                except (ValueError, TypeError): return None
            if self.sensor_type == "battery_voltage":
                return _get_value_or_none(status.get("BatteryVoltage"))
            if self.sensor_type == "refresh_interval":
                return _get_value_or_none(config.get("RefreshInterval", DEFAULT_REFRESH_INTERVAL))
            if self.sensor_type == "display_rotation":
                display_rotation = config.get("DisplayRotation")
                if display_rotation is not None:
                    return DISPLAY_ROTATIONS.get(str(display_rotation), f"Nieznana ({display_rotation})")
                return None
            if self.sensor_type == "application_version":
                return _get_value_or_none(status.get("ApplicationVersion"))
            if self.sensor_type == "storage_total":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                if total_str is None: return None
                try: return round(float(total_str) / (1024 * 1024), 2)
                except (ValueError, TypeError): return None
            if self.sensor_type == "storage_used":
                total_str = _get_value_or_none(status.get("FsTotalSize"))
                free_str = _get_value_or_none(status.get("FsFreeSize"))
                if total_str is None or free_str is None: return None
                try: return round((float(total_str) - float(free_str)) / (1024 * 1024), 2)
                except (ValueError, TypeError): return None
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
        device_name = self._get_device_name()
        
        if self.sensor_type == "state":
            device_data = self.coordinator.data.get(self.uuid, {})
            config = device_data.get("Config", {})
            configured_url = config.get("Url")
            
            return {
                "configured_url": configured_url if configured_url and configured_url.lower() not in UNKNOWN_STRINGS else None,
                "device_name": device_name
            }
        elif self.sensor_type == "display_rotation":
            device_data = self.coordinator.data.get(self.uuid, {})
            config = device_data.get("Config", {})
            display_rotation_raw = config.get("DisplayRotation")
            
            return {
                "display_rotation_id": display_rotation_raw,
                "available_rotations": list(DISPLAY_ROTATIONS.keys()),
                "device_name": device_name,
                "device_uuid": self.uuid
            }
        
        # Dla wszystkich innych sensorów dodaj nazwę urządzenia jako atrybut
        return {
            "device_name": device_name
        }