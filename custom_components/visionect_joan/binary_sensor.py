import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN, is_vss_device_connected
from .entity import VisionectEntity
from .recovery_eco import resolve_expected_dashboard_url
from .url_push import get_configured_url_from_coordinator, urls_equivalent

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Visionect Joan binary sensors."""
    # POPRAWKA: Pobieramy słownik, a z niego koordynator
    data = hass.data[DOMAIN][entry.entry_id]
    device_coordinators = data.get("device_coordinators", {})
    
    entities = []
    for device_uuid, device_coordinator in device_coordinators.items():
        entities.append(JoanOnlineBinarySensor(device_coordinator, device_uuid))
        entities.append(JoanHealthBinarySensor(device_coordinator, device_uuid))
        entities.append(JoanChargingBinarySensor(device_coordinator, device_uuid))
        entities.append(JoanDashboardOkBinarySensor(device_coordinator, device_uuid))
    
    async_add_entities(entities)

class JoanOnlineBinarySensor(VisionectEntity, BinarySensorEntity):
    """Binary sensor showing online/offline state of the device."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_online"
        self._attr_translation_key = "online"

    @property
    def is_on(self) -> bool:
        """Return True if device is connected (online, sleeping, or charging)."""
        data = self.coordinator.data.get(self.uuid, {})
        status = data.get("Status", {})
        val = data.get("State", status.get("State"))
        return is_vss_device_connected(val)



class JoanHealthBinarySensor(VisionectEntity, BinarySensorEntity):
    """Binary sensor indicating if device has any diagnostic problems (orphaned session)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_health"
        self._attr_translation_key = "health_status"
        # Fallback name if translation missing
        self._attr_name = "Health Status"

    @property
    def is_on(self) -> bool:
        """Return True if device has problems."""
        data = self.coordinator.data.get(self.uuid)
        if data and data.get("OrphanError"):
            return True
        return False

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self.coordinator.data.get(self.uuid)
        if data and data.get("OrphanError"):
            return {
                "error_message": data["OrphanError"]
            }
        return {}

class JoanChargingBinarySensor(VisionectEntity, BinarySensorEntity):
    """Binary sensor indicating if device is charging."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_is_charging"
        self._attr_translation_key = "is_charging"

    @property
    def is_on(self) -> bool:
        """Return True if device is charging."""
        data = self.coordinator.data.get(self.uuid)
        if data and "Status" in data:
             status = data.get("Status", {}) or {}
             is_charging_raw = str(status.get("IsCharging", "")).strip().lower()
             charger_raw = str(status.get("Charger", "")).strip().lower()
             return (
                 is_charging_raw in {"1", "true", "yes", "on", "charging"}
                 or charger_raw in {"1", "true", "yes", "on", "charging", "ac", "usb", "plugged", "plugged_in"}
             )
        return False


class JoanDashboardOkBinarySensor(VisionectEntity, BinarySensorEntity):
    """True when the VSS session URL matches the expected AppDaemon dashboard."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_dashboard_ok"
        self._attr_translation_key = "dashboard_ok"

    @property
    def is_on(self) -> bool | None:
        entry_id = getattr(self.coordinator, "config_entry", None)
        if entry_id is None:
            return None
        entry_data = self.hass.data.get(DOMAIN, {}).get(entry_id.entry_id) or {}
        expected = resolve_expected_dashboard_url(entry_data, self.uuid)
        if not expected:
            return None
        current = get_configured_url_from_coordinator(self.coordinator, self.uuid)
        if not current:
            return False
        api = entry_data.get("api")
        if api is None:
            return None
        return urls_equivalent(api, current, expected)

    @property
    def extra_state_attributes(self):
        entry_id = getattr(self.coordinator, "config_entry", None)
        if entry_id is None:
            return None
        entry_data = self.hass.data.get(DOMAIN, {}).get(entry_id.entry_id) or {}
        expected = resolve_expected_dashboard_url(entry_data, self.uuid)
        current = get_configured_url_from_coordinator(self.coordinator, self.uuid)
        if not expected:
            return None
        return {
            "expected_url": expected,
            "configured_url": current or "",
        }