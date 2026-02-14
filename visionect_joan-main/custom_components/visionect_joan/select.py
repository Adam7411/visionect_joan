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

# Nowa etykieta pozycji pomocowej w listach: "Configuration"/"Konfiguracja"
SHOW_CONFIG_HELP_KEY = "[Configuration]"

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
    """Tworzy trwałe powiadomienie z instrukcją (bez YAML)."""
    _LOGGER.info("User requested configuration instructions. Creating notification.")

    # Wybór języka powiadomienia

    # 1. Sprawdź wymuszenie w opcjach
    override = None
    if DOMAIN in hass.data and "tablet_language" in hass.data[DOMAIN]:
        override = hass.data[DOMAIN]["tablet_language"]
    
    if override == "pl":
        lang = "pl"
    elif override == "en":
        lang = "en"
    else:
        # 2. Fallback do języka serwera
        lang = (getattr(getattr(hass, "config", None), "language", "en") or "en").lower()

    is_pl = lang.startswith("pl")

    if is_pl:
        title = "Konfiguracja widoków (Visionect Joan)"
        message = (
            "Aby zarządzać widokami dostępnymi w listach „Wybierz widok” oraz „Cel przycisku Wstecz”:\n\n"
            "1) Przejdź do: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj\n"
            "2) Wybierz menu „Widoki” (Views).\n"
            "3) Tam znajdziesz opcje:\n"
            "   • Dodaj widok: Wpisz nazwę i adres URL, a następnie zapisz.\n"
            "   • Usuń widok: Wybierz widok z listy, aby go usunąć.\n"
            "   • Edytuj widok: Wybierz widok z listy, aby zmienić jego nazwę lub URL.\n\n"
            "Widoki są zapisywane globalnie i będą dostępne na wszystkich Twoich urządzeniach Visionect."
        )
    else:
        title = "Views configuration (Visionect Joan)"
        message = (
            "To manage views used by “Choose view” and “Back button target” lists:\n\n"
            "1) Go to: Settings → Devices & Services → Visionect Joan → Configure\n"
            "2) Select the “Views” menu.\n"
            "3) There you will find options:\n"
            "   • Add view: Enter a name and URL, then save.\n"
            "   • Remove view: Select a view from the list to delete it.\n"
            "   • Edit view: Select a view from the list to change its name or URL.\n\n"
            "Views are saved globally and will be available for all your Visionect devices."
        )

    async_create(
        hass,
        message,
        title=title,
        notification_id="visionect_joan_setup_views"
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
        options.append(SHOW_CONFIG_HELP_KEY)  # pozycja „Konfiguracja”
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
            self.async_write_ha_state()
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
        device_data = self.coordinator.data.get(self.uuid, {})
        return device_data.get("SessionOptions", {}).get("DefaultDithering")

    async def async_select_option(self, option: str) -> None:
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
        device_data = self.coordinator.data.get(self.uuid, {})
        encoding = device_data.get("SessionOptions", {}).get("DefaultEncoding")
        return str(encoding) if encoding is not None else None

    async def async_select_option(self, option: str) -> None:
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
        prefs = self._get_prefs()
        url = prefs.get("back_targets", {}).get(self.uuid)
        if not url:
            return None

        for name, view_url in self._views.items():
            if view_url == url:
                return name
        return None

    async def async_select_option(self, option: str) -> None:
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