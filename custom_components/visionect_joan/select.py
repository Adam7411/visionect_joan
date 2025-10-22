
import logging
from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .const import DOMAIN, DITHERING_OPTIONS, ENCODING_OPTIONS
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

INSTRUCTION_OPTION_KEY = "unconfigured_prompt"
MAIN_MENU_OPTION = "[Main menu]"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.get("coordinator")
    if not (coordinator and coordinator.data):
        return

    entities = []
    views = hass.data[DOMAIN].get('views', [])
    has_main_menu = bool(hass.data[DOMAIN].get("main_menu_url"))

    for uuid in coordinator.data:
        # Choose active view to display now
        entities.append(VisionectViewSelect(coordinator, uuid, views, has_main_menu))

        # Image quality controls
        entities.append(VisionectDitheringSelect(coordinator, uuid))
        entities.append(VisionectEncodingSelect(coordinator, uuid))

        # NEW: select default Back target for overlays
        entities.append(VisionectBackViewSelect(hass, coordinator, entry, uuid, views, has_main_menu))

    async_add_entities(entities)

class VisionectViewSelect(VisionectEntity, SelectEntity):
    """Select entity to switch predefined views on a Visionect device (and Main menu)."""

    def __init__(self, coordinator, uuid: str, views: list, has_main_menu: bool):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "view_select"
        self._attr_unique_id = f"{uuid}_view_select"
        self._attr_icon = "mdi:view-dashboard-outline"

        self._is_configured = bool(views)
        self._views = {view["name"]: view["url"] for view in views}

        options = list(self._views.keys())
        if has_main_menu:
            options.append(MAIN_MENU_OPTION)
        if not self._is_configured:
            options.append(INSTRUCTION_OPTION_KEY)
        self._attr_options = options

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self._is_configured:
            return "unconfigured_state"

        device_data = self.coordinator.data.get(self.uuid, {})
        current_url = device_data.get("Config", {}).get("Url")
        if not current_url:
            return None

        # Exact match to named view
        for name, url in self._views.items():
            if url == current_url:
                return name

        # Main menu?
        main_menu_url = self.hass.data[DOMAIN].get("main_menu_url")
        if main_menu_url and current_url == main_menu_url:
            return MAIN_MENU_OPTION

        if current_url.startswith("data:text/html,"):
            if "visionect_snapshot" in current_url:
                return "Camera Snapshot"
            return "Dynamic Content (HTML)"

        return "Custom URL"

    async def async_select_option(self, option: str) -> None:
        """Handle a selection change."""
        if option == INSTRUCTION_OPTION_KEY:
            from homeassistant.components.persistent_notification import async_create

            _LOGGER.info("User requested configuration instructions. Creating notification.")

            title = "Configure Views for Visionect Joan"
            message = (
                "The Visionect Joan integration has no views configured for the select entity.\n\n"
                "Add the following example to your configuration.yaml and restart Home Assistant:\n\n"
                "```yaml\n"
                "visionect_joan:\n"
                "  views:\n"
                "    - name: \"Dashboard AppDaemon\"\n"
                "      url: \"http://<YOUR_HA_IP>:5050/dashboard_name\"\n"
                "    - name: \"Example Photo\"\n"
                "      url: \"http://<YOUR_HA_IP>:8123/local/image.png\"\n"
                "    - name: \"Example URL\"\n"
                "      url: \"https://www.home-assistant.io/\"\n"
                "```\n\n"
                "Optionally, set a main menu URL used by the back button overlay:\n\n"
                "```yaml\n"
                "visionect_joan:\n"
                "  main_menu_url: \"http://<YOUR_HA_IP>:5050/appdaemon_dashboard_name\"\n"
                "```"
            )

            async_create(
                self.hass,
                message,
                title=title,
                notification_id="visionect_joan_setup_views"
            )
            self.async_write_ha_state()
            return

        target_url: Optional[str] = None
        if option == MAIN_MENU_OPTION:
            target_url = self.hass.data[DOMAIN].get("main_menu_url")
            if not target_url:
                _LOGGER.error("Main menu URL is not configured in configuration.yaml (visionect_joan: main_menu_url).")
                return
        else:
            target_url = self._views.get(option)

        if not target_url:
            _LOGGER.error(f"An unknown view was selected: {option}")
            return

        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        _LOGGER.info(f"Changing view for {self.uuid} to '{option}' ({target_url})")

        if await api.async_set_device_url(self.uuid, target_url):
            _LOGGER.info(f"View for {self.uuid} changed successfully.")
            if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["Config"]["Url"] = target_url
                self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to change view for {self.uuid}.")
        await self.coordinator.async_request_refresh()

# --- Dithering Select Entity ---
class VisionectDitheringSelect(VisionectEntity, SelectEntity):
    """Select entity to change the dithering method on a Visionect device."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "dithering_select"
        self._attr_unique_id = f"{uuid}_dithering_select"
        self._attr_icon = "mdi:image-filter-black-white"
        self._attr_options = DITHERING_OPTIONS
        self._attr_entity_registry_enabled_default = False

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        device_data = self.coordinator.data.get(self.uuid, {})
        return device_data.get("SessionOptions", {}).get("DefaultDithering")

    async def async_select_option(self, option: str) -> None:
        """Handle a selection change."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        
        if await api.async_set_session_options(self.uuid, dithering=option):
            _LOGGER.info(f"Dithering for {self.uuid} changed successfully to {option}.")
            if self.uuid in self.coordinator.data and "SessionOptions" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["SessionOptions"]["DefaultDithering"] = option
                self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to change dithering for {self.uuid}.")
        await self.coordinator.async_request_refresh()

# --- Encoding Select Entity ---
class VisionectEncodingSelect(VisionectEntity, SelectEntity):
    """Select entity to change the bit depth (encoding) on a Visionect device."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "encoding_select"
        self._attr_unique_id = f"{uuid}_encoding_select"
        self._attr_icon = "mdi:layers-triple"
        self._attr_options = ENCODING_OPTIONS
        self._attr_entity_registry_enabled_default = False

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        device_data = self.coordinator.data.get(self.uuid, {})
        encoding = device_data.get("SessionOptions", {}).get("DefaultEncoding")
        return str(encoding) if encoding is not None else None

    async def async_select_option(self, option: str) -> None:
        """Handle a selection change."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        
        if await api.async_set_session_options(self.uuid, encoding=option):
            _LOGGER.info(f"Encoding for {self.uuid} changed successfully to {option}.")
            if self.uuid in self.coordinator.data and "SessionOptions" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["SessionOptions"]["DefaultEncoding"] = option
                self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to change encoding for {self.uuid}.")
        await self.coordinator.async_request_refresh()

# --- NEW: Back target select entity ---
class VisionectBackViewSelect(VisionectEntity, SelectEntity):
    """Select entity to choose default 'Back' button target for overlays."""

    _attr_translation_key = "back_view_select"

    def __init__(self, hass: HomeAssistant, coordinator, entry: ConfigEntry, uuid: str, views: list, has_main_menu: bool):
        super().__init__(coordinator, uuid)
        self._hass = hass
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{uuid}_back_view_select"
        self._attr_icon = "mdi:arrow-left-bold"

        self._views = {view["name"]: view["url"] for view in views}
        options = list(self._views.keys())
        if has_main_menu:
            options.append(MAIN_MENU_OPTION)
        self._attr_options = options or [MAIN_MENU_OPTION]

    def _get_prefs(self) -> dict:
        return self._hass.data[DOMAIN][self._entry_id].setdefault("prefs", {"back_targets": {}})

    def _get_store(self) -> Store:
        return self._hass.data[DOMAIN][self._entry_id].get("prefs_store")

    @property
    def current_option(self) -> str | None:
        """Return the current selected option (by matching stored URL)."""
        prefs = self._get_prefs()
        back_targets = prefs.get("back_targets", {})
        url = back_targets.get(self.uuid)
        if not url:
            return None

        for name, view_url in self._views.items():
            if view_url == url:
                return name

        main_menu_url = self._hass.data[DOMAIN].get("main_menu_url")
        if main_menu_url and url == main_menu_url:
            return MAIN_MENU_OPTION

        return None

    async def async_select_option(self, option: str) -> None:
        """Persist selected back target URL for this device."""
        if option == MAIN_MENU_OPTION:
            url = self._hass.data[DOMAIN].get("main_menu_url")
            if not url:
                _LOGGER.error("Cannot set Back target to Main menu: main_menu_url not configured.")
                return
        else:
            url = self._views.get(option)

        if not url:
            _LOGGER.error(f"Unknown Back target selection: {option}")
            return

        prefs = self._get_prefs()
        prefs.setdefault("back_targets", {})[self.uuid] = url

        store = self._get_store()
        if store:
            await store.async_save(prefs)

        _LOGGER.info(f"Saved Back target for {self.uuid}: {option} -> {url}")
        self.async_write_ha_state()