import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.persistent_notification import async_create

from .const import DOMAIN, DITHERING_OPTIONS, ENCODING_OPTIONS
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

INSTRUCTION_OPTION_KEY = "unconfigured_prompt"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    if not (coordinator and coordinator.data):
        return

    entities = []
    
    # Get predefined views from configuration.yaml
    views = hass.data[DOMAIN].get('views', [])

    # For each device, create one select entity for choosing views
    for uuid in coordinator.data:
        entities.append(VisionectViewSelect(coordinator, uuid, views))
        # --- NEW: Add image quality select entities ---
        entities.append(VisionectDitheringSelect(coordinator, uuid))
        entities.append(VisionectEncodingSelect(coordinator, uuid))
            
    async_add_entities(entities)

class VisionectViewSelect(VisionectEntity, SelectEntity):
    """Select entity to switch predefined views on a Visionect device."""

    def __init__(self, coordinator, uuid: str, views: list):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "view_select"
        self._attr_unique_id = f"{uuid}_view_select"
        self._attr_icon = "mdi:view-dashboard-outline"
        
        self._is_configured = bool(views)
        self._views = {view["name"]: view["url"] for view in views}
        
        options = list(self._views.keys())
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
        for name, url in self._views.items():
            if url == current_url:
                return name
        if current_url.startswith("data:text/html,"):
            if "visionect_snapshot" in current_url:
                return "Camera Snapshot"
            return "Dynamic Content (HTML)"
        return "Custom URL"

    async def async_select_option(self, option: str) -> None:
        """Handle a selection change."""
        if option == INSTRUCTION_OPTION_KEY:
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
            
        if option not in self._views:
            _LOGGER.error(f"An unknown view was selected: {option}")
            return
            
        target_url = self._views[option]
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

# --- NEW: Dithering Select Entity ---
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


# --- NEW: Encoding Select Entity ---
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