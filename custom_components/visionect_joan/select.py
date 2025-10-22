# Plik: custom_components/visionect_joan/select.py

import logging
from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store
from homeassistant.components.persistent_notification import async_create

from .const import DOMAIN, DITHERING_OPTIONS, ENCODING_OPTIONS
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

# Klucz dla opcji wyświetlającej powiadomienie z instrukcją
SHOW_CONFIG_HELP_KEY = "[Show Configuration Help]"

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

    for uuid in coordinator.data:
        entities.append(VisionectViewSelect(coordinator, uuid, views))
        entities.append(VisionectDitheringSelect(coordinator, uuid))
        entities.append(VisionectEncodingSelect(coordinator, uuid))
        entities.append(VisionectBackViewSelect(hass, coordinator, entry, uuid, views))

    async_add_entities(entities)

def _create_config_notification(hass: HomeAssistant):
    """Tworzy trwałe powiadomienie z instrukcją konfiguracji."""
    _LOGGER.info("User requested configuration instructions. Creating notification.")
    
    title = "Configure Views for Visionect Joan"
    message = (
        "You can define a list of named views in your `configuration.yaml` file. These views will then be available in all selectors.\n\n"
        "**Example:**\n"
        "```yaml\n"
        "visionect_joan:\n"
        "  # These views will appear in the 'Choose view' and 'Back button target' selectors\n"
        "  views:\n"
        "    - name: \"Dashboard AppDaemon\"\n"
        "      url: \"http://<YOUR_HA_IP>:5050/dashboard_name\"\n"
        "    - name: \"Main Dashboard\"\n"
        "      url: \"http://<YOUR_HA_IP>:5050/main_dashboard\"\n"
        "    - name: \"Kitchen View\"\n"
        "      url: \"http://<YOUR_HA_IP>:5050/kitchen_view\"\n"
        "    - name: \"Family Photo\"\n"
        "      url: \"http://<YOUR_HA_IP>:8123/local/family.png\"\n"
        "    - name: \"Example URL\"\n"
        "      url: \"https://www.home-assistant.io/\"\n"
        "```\n\n"
        "You can also set a global fallback URL for the 'Back' button. This is used when no other destination is specified:\n\n"
        "```yaml\n"
        "visionect_joan:\n"
        "  main_menu_url: \"http://<YOUR_HA_IP>:5050/main_dashboard\"\n"
        "```"
    )

    async_create(
        hass,
        message,
        title=title,
        notification_id="visionect_joan_setup_views"
    )

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
        options.append(SHOW_CONFIG_HELP_KEY) # Zawsze dodaj opcję pomocy
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
        if option == SHOW_CONFIG_HELP_KEY:
            _create_config_notification(self.hass)
            self.async_write_ha_state() # Resetuje selektor do poprzedniego stanu
            return

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

class VisionectBackViewSelect(VisionectEntity, SelectEntity):
    """Select entity to choose default 'Back' button target for overlays."""
    _attr_translation_key = "back_view_select"

    def __init__(self, hass: HomeAssistant, coordinator, entry: ConfigEntry, uuid: str, views: list):
        super().__init__(coordinator, uuid)
        self._hass = hass
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{uuid}_back_view_select"
        self._attr_icon = "mdi:arrow-left-bold"

        self._views = {view["name"]: view["url"] for view in views}
        options = list(self._views.keys())
        options.append(SHOW_CONFIG_HELP_KEY)
        self._attr_options = options

    def _get_prefs(self) -> dict:
        return self._hass.data[DOMAIN][self._entry_id].setdefault("prefs", {"back_targets": {}})

    def _get_store(self) -> Store:
        return self._hass.data[DOMAIN][self._entry_id].get("prefs_store")

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        prefs = self._get_prefs()
        url = prefs.get("back_targets", {}).get(self.uuid)
        if not url:
            return None

        for name, view_url in self._views.items():
            if view_url == url:
                return name
        return None

    async def async_select_option(self, option: str) -> None:
        """Handle a selection change."""
        if option == SHOW_CONFIG_HELP_KEY:
            _create_config_notification(self.hass)
            self.async_write_ha_state()
            return

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