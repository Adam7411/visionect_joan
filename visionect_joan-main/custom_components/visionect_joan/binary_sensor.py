import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Visionect Joan binary sensors."""
    # POPRAWKA: Pobieramy słownik, a z niego koordynator
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    
    entities = []
    for device_uuid in coordinator.data:
        entities.append(JoanHealthBinarySensor(coordinator, device_uuid))
        entities.append(JoanChargingBinarySensor(coordinator, device_uuid))
    
    async_add_entities(entities)

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
             return data["Status"].get("IsCharging", False)
        return False