import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Visionect Joan buttons."""
    # POPRAWKA: Pobieramy słownik, a z niego koordynator
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    
    entities = []
    for device_uuid in coordinator.data:
        entities.append(JoanCheckOrphansButton(coordinator, device_uuid))
        entities.append(JoanRebootButton(coordinator, device_uuid))
        entities.append(JoanForceRefreshButton(coordinator, device_uuid))
        entities.append(JoanClearCacheButton(coordinator, device_uuid))
    
    async_add_entities(entities)

class JoanCheckOrphansButton(VisionectEntity, ButtonEntity):
    """Button to manually check for orphaned sessions/problems."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_icon = "mdi:stethoscope"

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_check_orphans"
        # Translation key for localized name
        self._attr_translation_key = "check_orphans"
        self._attr_name = "Check Health"

    async def async_press(self) -> None:
        """Check orphans and notify."""
        _LOGGER.debug(f"Manually checking orphans for {self.uuid}")
        
        # Force coordinator refresh to fetch latest orphans
        await self.coordinator.async_request_refresh()
        
        # Check result
        data = self.coordinator.data.get(self.uuid)
        if data and data.get("OrphanError"):
            error = data["OrphanError"]
            _LOGGER.warning(f"Device {self.uuid} has problem: {error}")
            
            # Send notification
            self.hass.components.persistent_notification.async_create(
                f"⚠️ Visionect Device Problem detected:\n{error}",
                title=f"Joan Diagnostic: {self.uuid}",
                notification_id=f"joan_orphan_{self.uuid}"
            )
        else:
            _LOGGER.info(f"Device {self.uuid} is healthy")

class JoanRebootButton(VisionectEntity, ButtonEntity):
    """Button to reboot the device."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_reboot"
        self._attr_translation_key = "reboot_device"

    async def async_press(self) -> None:
        """Handle the button press."""
        api = self.coordinator.api
        await api.async_reboot_device(self.uuid)

class JoanForceRefreshButton(VisionectEntity, ButtonEntity):
    """Button to force refresh (restart session)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_force_refresh"
        self._attr_translation_key = "force_refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        api = self.coordinator.api
        await api.async_restart_session(self.uuid)

class JoanClearCacheButton(VisionectEntity, ButtonEntity):
    """Button to clear webkit cache."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_icon = "mdi:eraser"

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_clear_cache"
        self._attr_translation_key = "clear_web_cache"

    async def async_press(self) -> None:
        """Handle the button press."""
        api = self.coordinator.api
        await api.async_clear_webkit_cache([self.uuid])