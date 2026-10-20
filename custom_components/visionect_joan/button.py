import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.components.persistent_notification import (
    async_create as async_create_persistent_notification,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TABLET_LANGUAGE, DOMAIN, resolve_tablet_content_lang
from . import repairs as visionect_repairs
from .entity import VisionectEntity
from .notification_i18n import ntr

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Visionect Joan buttons."""
    # POPRAWKA: Pobieramy słownik, a z niego koordynator
    data = hass.data[DOMAIN][entry.entry_id]
    device_coordinators = data.get("device_coordinators", {})
    coordinator = data.get("coordinator")
    
    entities = []
    if coordinator is not None:
        entities.append(VssDisableSleepManagerButton(coordinator, entry))
    for device_uuid, device_coordinator in device_coordinators.items():
        entities.append(JoanCheckOrphansButton(device_coordinator, device_uuid))
        entities.append(JoanRebootButton(device_coordinator, device_uuid))
        entities.append(JoanForceRefreshButton(device_coordinator, device_uuid))
        entities.append(JoanClearCacheButton(device_coordinator, device_uuid))
        entities.append(JoanOllamaAnalyzeLogsButton(device_coordinator, device_uuid))

    async_add_entities(entities)


class VssDisableSleepManagerButton(CoordinatorEntity, ButtonEntity):
    """Disable global VSS Sleep Manager (Always Online homes)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_translation_key = "disable_sleep_manager"
    _attr_icon = "mdi:sleep-off"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_disable_sleep_manager"

    @property
    def device_info(self) -> DeviceInfo:
        host = self._entry.data.get(CONF_HOST) or ""
        if host and not str(host).startswith(("http://", "https://")):
            host = f"http://{host}"
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_vss")},
            name="Visionect Server (VSS)",
            manufacturer="Visionect",
            model="Software Suite",
            configuration_url=host or None,
        )

    async def async_press(self) -> None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id) or {}
        api = entry_data.get("api") or getattr(self.coordinator, "api", None)
        if api is None:
            _LOGGER.error("No VSS API — cannot disable Sleep Manager")
            return
        ok = await api.async_toggle_sleep_manager(False)
        entry_data["vss_sleep_manager_enabled"] = False if ok else True
        visionect_repairs.async_sync_sleep_manager_issue(
            self.hass, self._entry.entry_id, enabled=not ok
        )
        self.coordinator.async_update_listeners()
        lang = resolve_tablet_content_lang(
            (self._entry.options or {}).get(CONF_TABLET_LANGUAGE, "auto"),
            getattr(self.hass.config, "language", None),
        )
        if ok:
            async_create_persistent_notification(
                self.hass,
                ntr(lang, "sleep_manager_disabled_message"),
                title=ntr(lang, "sleep_manager_disabled_title"),
                notification_id=f"visionect_sleep_manager_{self._entry.entry_id}",
            )
        else:
            async_create_persistent_notification(
                self.hass,
                ntr(lang, "sleep_manager_disable_failed_message"),
                title=ntr(lang, "sleep_manager_disabled_title"),
                notification_id=f"visionect_sleep_manager_{self._entry.entry_id}",
            )

def _health_notify_lang(hass, coordinator) -> str:
    """Language for Check Health persistent notifications (tablet option or HA locale)."""
    entry = getattr(coordinator, "config_entry", None)
    tablet_lang = "auto"
    if entry is not None:
        tablet_lang = (entry.options or {}).get(CONF_TABLET_LANGUAGE, "auto")
    return resolve_tablet_content_lang(
        tablet_lang,
        getattr(hass.config, "language", None),
    )

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

        api = getattr(self.coordinator, "api", None)
        if api is not None:
            api.invalidate_orphans_cache()

        await self.coordinator.async_request_refresh()

        data = self.coordinator.data.get(self.uuid) or {}
        error = data.get("OrphanError")
        lang = _health_notify_lang(self.hass, self.coordinator)
        device_name = (data.get("Config") or {}).get("Name") or self.uuid
        notif_id = f"joan_orphan_{self.uuid}"
        title = ntr(lang, "health_check_title", device_name=device_name)

        if error:
            _LOGGER.warning(f"Device {self.uuid} has problem: {error}")
            body = ntr(lang, "health_check_problem", error=error)
        else:
            _LOGGER.info(f"Device {self.uuid} is healthy")
            body = ntr(lang, "health_check_ok")

        async_create_persistent_notification(
            self.hass,
            body,
            title=title,
            notification_id=notif_id,
        )

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

class JoanOllamaAnalyzeLogsButton(VisionectEntity, ButtonEntity):
    """Run Ollama log analysis focused on this tablet (on demand)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_icon = "mdi:brain"

    def __init__(self, coordinator, device_uuid):
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_ollama_analyze_logs"
        self._attr_translation_key = "ollama_analyze_logs"

    async def async_press(self) -> None:
        """Show logs (and Ollama summary when configured)."""
        # Late import avoids circular import while __init__ loads platforms.
        from . import async_run_ollama_device_analysis_for_device

        entry = getattr(self.coordinator, "config_entry", None)
        if entry is None:
            _LOGGER.error("Visionect coordinator has no config_entry; cannot run Ollama analysis")
            return
        api = getattr(self.coordinator, "api", None)
        if api is None:
            _LOGGER.error("Visionect coordinator has no api; cannot run Ollama analysis")
            return
        await async_run_ollama_device_analysis_for_device(
            self.hass,
            entry,
            api,
            self.coordinator,
            self.uuid,
        )


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
