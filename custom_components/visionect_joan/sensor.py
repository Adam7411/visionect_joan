from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_HOST,
    UnitOfInformation,
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfTime
)
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.network import get_url
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging
from datetime import datetime
from urllib.parse import urlparse

from .const import (
    DOMAIN, STATE_ONLINE, STATE_OFFLINE, STATE_SLEEPING, is_vss_device_connected,
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
    # Options.ScheduledWakeup (API read-only) — useful when Sleep Manager put device to sleep
    "scheduled_wakeup": (None, "mdi:alarm", None, False),
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
    coordinator = entry_data.get("coordinator")
    entities: list = []
    if coordinator is not None:
        entities.append(VssDefaultUrlSensor(coordinator, entry))
        entities.append(VssHubInfoSensor(coordinator, entry))
        entities.append(VssDevicesOnlineSensor(coordinator, entry))
        entities.append(VssSessionsSensor(coordinator, entry))
        entities.append(VssOrphansSensor(coordinator, entry))
    for uuid, device_coordinator in device_coordinators.items():
        for sensor_type in SENSOR_TYPES:
            entities.append(VisionectSensor(device_coordinator, uuid, sensor_type))
    if entities:
        async_add_entities(entities)


def _vss_hub_device_info(entry: ConfigEntry, entry_data: dict | None = None) -> DeviceInfo:
    """Shared DeviceInfo for Visionect Server (VSS) hub entities."""
    host = entry.data.get(CONF_HOST) or ""
    if host and not str(host).startswith(("http://", "https://")):
        host = f"http://{host}"
    hub = (entry_data or {}).get("vss_hub") if isinstance(entry_data, dict) else None
    hub = hub if isinstance(hub, dict) else {}
    model = "Software Suite"
    deployment = hub.get("deployment_name")
    if deployment:
        model = f"Software Suite ({deployment})"
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_vss")},
        name="Visionect Server (VSS)",
        manufacturer="Visionect",
        model=model,
        configuration_url=host or None,
    )


class VssDefaultUrlSensor(CoordinatorEntity, SensorEntity):
    """VSS HTML Backend Default URL from GET /api/config."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "vss_default_url"
    _attr_icon = "mdi:link-box-outline"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vss_default_url"

    @property
    def device_info(self) -> DeviceInfo:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        return _vss_hub_device_info(self._entry, entry_data)

    @property
    def native_value(self) -> str | None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        url = entry_data.get("vss_default_url")
        if not url:
            return None
        display = _replace_ha_host_with_alias(str(url), self.hass)
        return _format_url_for_sensor_state(display)

    @property
    def extra_state_attributes(self):
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        raw = entry_data.get("vss_default_url")
        return {
            "full_url": raw or "",
            "hint": (
                "Same as VSS Settings → HTML Backend → Default URL. "
                "Set via integration Options → Default URL (Apply to VSS)."
            ),
        }


class VssHubInfoSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic overview of VSS server config (deployment, timezone, features…)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "vss_hub_info"
    _attr_icon = "mdi:server-network"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vss_hub_info"

    @property
    def device_info(self) -> DeviceInfo:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        return _vss_hub_device_info(self._entry, entry_data)

    @property
    def native_value(self) -> str | None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        hub = entry_data.get("vss_hub") if isinstance(entry_data.get("vss_hub"), dict) else {}
        name = hub.get("deployment_name")
        if name:
            return str(name)[:255]
        tz = hub.get("timezone")
        if tz:
            return str(tz)[:255]
        if hub:
            return "ok"
        return None

    @property
    def extra_state_attributes(self):
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        hub = dict(entry_data.get("vss_hub") or {})
        # Flatten nested server_status into attributes with prefix.
        status = hub.pop("server_status", None)
        attrs = {k: v for k, v in hub.items() if v is not None}
        if isinstance(status, dict):
            for key, value in status.items():
                attrs[f"status_{key}"] = value
        attrs["hint"] = (
            "From VSS GET /api/config (+ /api/status). "
            "Device/session counts refresh with the VSS watchdog."
        )
        return attrs


class VssDevicesOnlineSensor(CoordinatorEntity, SensorEntity):
    """How many tablets report a live VSS link (online / sleeping / charging)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "vss_devices_online"
    _attr_icon = "mdi:tablet-dashboard"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vss_devices_online"

    @property
    def device_info(self) -> DeviceInfo:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        return _vss_hub_device_info(self._entry, entry_data)

    @property
    def native_value(self) -> int | None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        counts = entry_data.get("vss_device_counts")
        if not isinstance(counts, dict):
            return None
        return int(counts.get("connected", 0))

    @property
    def extra_state_attributes(self):
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        counts = entry_data.get("vss_device_counts")
        if not isinstance(counts, dict):
            return {}
        attrs = {
            "total": counts.get("total"),
            "online": counts.get("online"),
            "sleeping": counts.get("sleeping"),
            "charging": counts.get("charging"),
            "flashing": counts.get("flashing"),
            "sending": counts.get("sending"),
            "receiving": counts.get("receiving"),
            "updating": counts.get("updating"),
            "unavailable": counts.get("unavailable"),
            "offline": counts.get("offline"),
            "hint": (
                "Connected = online + sleeping + charging + mid-transfer "
                "(sending/receiving/flashing/updating). States from VSS / PRTG Joan."
            ),
        }
        fleet = entry_data.get("vss_device_fleet")
        if isinstance(fleet, dict):
            if fleet.get("firmware_versions"):
                attrs["firmware_versions"] = fleet["firmware_versions"]
            if fleet.get("hardware_revisions"):
                attrs["hardware_revisions"] = fleet["hardware_revisions"]
            if fleet.get("pending_firmware_flash"):
                attrs["pending_firmware_flash"] = fleet["pending_firmware_flash"]
        return {k: v for k, v in attrs.items() if v not in (None, 0, {})}


class VssSessionsSensor(CoordinatorEntity, SensorEntity):
    """Active WebKit sessions vs MaxSessions from VSS config."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "vss_sessions"
    _attr_icon = "mdi:application-array-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vss_sessions"

    @property
    def device_info(self) -> DeviceInfo:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        return _vss_hub_device_info(self._entry, entry_data)

    @property
    def native_value(self) -> int | None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        val = entry_data.get("vss_sessions_count")
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self):
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        hub = entry_data.get("vss_hub") if isinstance(entry_data.get("vss_hub"), dict) else {}
        attrs = {
            "max_sessions": hub.get("max_sessions") or hub.get("sessions_max"),
            "sessions_free": hub.get("sessions_free"),
            "hint": (
                "GET /api/session vs Okular.MaxSessions. "
                "When full, VSS ignores new session requests."
            ),
        }
        return {k: v for k, v in attrs.items() if v is not None}


class VssOrphansSensor(CoordinatorEntity, SensorEntity):
    """Problematic sessions from GET /api/orphans (hub health signal)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "vss_orphans"
    _attr_icon = "mdi:lan-disconnect"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vss_orphans"

    @property
    def device_info(self) -> DeviceInfo:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        return _vss_hub_device_info(self._entry, entry_data)

    @property
    def native_value(self) -> int | None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        val = entry_data.get("vss_orphans_count")
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self):
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        return {
            "orphans_deferred": entry_data.get("vss_orphans_deferred"),
            "hint": (
                "GET /api/orphans — real session problems. "
                "orphans_deferred = online devices still without a session (?all=true). "
                "Use Check Health / Repairs on the tablet when > 0."
            ),
        }


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
                    if api_state in ["2", "sleeping"]:
                        return STATE_SLEEPING
                    if is_vss_device_connected(api_state):
                        # online / charging / "1" — charging is still a live link
                        return STATE_ONLINE
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

            if self.sensor_type == "scheduled_wakeup":
                # Official API: Options.ScheduledWakeup is read-only (when Sleep Manager
                # schedules the next wake). Also accept Status for newer firmware dumps.
                opts = device_data.get("Options") or {}
                return _get_value_or_none(
                    opts.get("ScheduledWakeup") or status.get("ScheduledWakeup")
                )
                
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

        if self.sensor_type in {"battery", "rssi", "temperature"}:
            entry = getattr(self.coordinator, "config_entry", None)
            if entry is None:
                return None
            entry_data = self.hass.data.get(DOMAIN, {}).get(entry.entry_id) or {}
            summaries = entry_data.get("status_history_by_uuid") or {}
            summary = summaries.get(str(self.uuid).strip().lower())
            if not isinstance(summary, dict) or not summary.get("samples"):
                return None
            prefix = self.sensor_type
            attrs = {
                f"{prefix}_24h_min": summary.get(f"{prefix}_min"),
                f"{prefix}_24h_max": summary.get(f"{prefix}_max"),
                "history_samples": summary.get("samples"),
                "history_hours": summary.get("hours"),
            }
            return {k: v for k, v in attrs.items() if v is not None} or None
        
        return None
