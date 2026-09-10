# Plik: custom_components/visionect_joan/select.py

import logging
from datetime import timedelta
from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store
from homeassistant.components.persistent_notification import async_create

from .notification_i18n import ntr
from .const import (
    DOMAIN,
    resolve_tablet_content_lang,
    DITHERING_OPTIONS,
    ENCODING_OPTIONS,
    ROTATION_OPTIONS,
    ROTATION_TO_API,
    DISPLAY_ROTATIONS,
    SLEEP_PERIODIC_OPTIONS,
    SLEEP_PERIODIC_TO_API,
    SLEEP_SCHEDULE_OPTIONS,
    SLEEP_SCHEDULE_TO_API,
    PUSH_MODE_OPTIONS,
    PUSH_MODE_TO_API,
)
from .screen_layout import infer_screen_size_from_device
from .entity import VisionectEntity
from .api import VisionectAPI
from .profile_tuning import (
    apply_api_cache_ttls_for_profile_map,
    normalize_device_uuid,
)

_LOGGER = logging.getLogger(__name__)

# Nowa etykieta pozycji pomocowej w listach: "Configuration"/"Konfiguracja"
SHOW_CONFIG_HELP_KEY = "[Configuration]"

# Per-device layout for integration-generated HTML (low battery, send_text scaling, …)
SCREEN_SIZE_SELECT_OPTIONS = ("auto", "joan6", "joan13")
REFRESH_PROFILE_SELECT_OPTIONS = ("eco", "normal", "alert")


def _normalize_refresh_profile(value: str | None) -> str:
    profile = str(value or "eco").strip().lower()
    if profile in REFRESH_PROFILE_SELECT_OPTIONS:
        return profile
    return "eco"


def _apply_runtime_tuning_for_single_tablet(hass: HomeAssistant, entry_id: str, uuid: str, profile: str) -> None:
    """Adjust only selected tablet coordinator interval."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id) or {}
    device_coordinators = entry_data.get("device_coordinators", {}) or {}
    device_coordinator = device_coordinators.get(uuid)
    if not device_coordinator:
        return
    p = _normalize_refresh_profile(profile)
    if p == "eco":
        device_coordinator.update_interval = timedelta(minutes=20)
    elif p == "alert":
        device_coordinator.update_interval = timedelta(minutes=5)
    else:
        device_coordinator.update_interval = timedelta(minutes=15)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    device_coordinators = data.get("device_coordinators", {})
    if not device_coordinators:
        return

    entities = []
    views = data.get("views", [])

    for uuid, device_coordinator in device_coordinators.items():
        entities.append(VisionectViewSelect(hass, device_coordinator, entry, uuid, views))
        entities.append(VisionectDitheringSelect(device_coordinator, uuid))
        entities.append(VisionectEncodingSelect(device_coordinator, uuid))
        entities.append(VisionectRotationSelect(device_coordinator, uuid))
        entities.append(VisionectBackViewSelect(hass, device_coordinator, entry, uuid, views))
        entities.append(VisionectScreenSizeSelect(hass, device_coordinator, entry, uuid))
        entities.append(VisionectRefreshProfileSelect(hass, device_coordinator, entry, uuid))
        # NOWE: Harmonogram uśpienia w minutach (0 = Always Online, >0 = cykliczne spanie)
        entities.append(VisionectSleepScheduleSelect(device_coordinator, uuid))

    async_add_entities(entities)

def _create_config_notification(hass: HomeAssistant):
    """Tworzy trwałe powiadomienie z instrukcją (bez YAML)."""
    _LOGGER.info("User requested configuration instructions. Creating notification.")

    # Wybór języka powiadomienia

    # 1. Sprawdź wymuszenie w opcjach
    override = None
    if DOMAIN in hass.data and "tablet_language" in hass.data[DOMAIN]:
        override = hass.data[DOMAIN]["tablet_language"]
    
    lang = resolve_tablet_content_lang(
        override,
        getattr(getattr(hass, "config", None), "language", None),
    )

    async_create(
        hass,
        ntr(lang, "select_config_message"),
        title=ntr(lang, "select_config_title"),
        notification_id="visionect_joan_setup_views"
    )


def _refresh_profile_notification(hass: HomeAssistant, uuid: str, device_name: str, profile: str) -> tuple[str, str]:
    """Build localized notification title/body for refresh profile change."""
    override = hass.data.get(DOMAIN, {}).get("tablet_language", "auto")
    lang = resolve_tablet_content_lang(
        override,
        getattr(getattr(hass, "config", None), "language", None),
    )
    name = device_name or uuid
    p = _normalize_refresh_profile(profile)
    title = ntr(lang, "refresh_profile_notification_title", device_name=name)
    body_key = f"refresh_profile_notification_body_{p}"
    body = ntr(lang, body_key, device_name=name)
    return title, body

def _view_name_for_url(views: dict[str, str], url: str | None) -> str | None:
    if not url:
        return None
    for name, view_url in views.items():
        if view_url == url:
            return name
    return None


class VisionectViewSelect(VisionectEntity, SelectEntity):
    """Select entity to switch predefined views on a Visionect device."""

    def __init__(self, hass: HomeAssistant, coordinator, entry: ConfigEntry, uuid: str, views: list):
        super().__init__(coordinator, uuid)
        self._hass = hass
        self._entry_id = entry.entry_id
        self._device_uuid = normalize_device_uuid(uuid)
        self._attr_translation_key = "view_select"
        self._attr_unique_id = f"{uuid}_view_select"
        self._attr_icon = "mdi:view-dashboard-outline"

        self._is_configured = bool(views)
        self._views = {view["name"]: view["url"] for view in views}

        options = list(self._views.keys())
        options.append(SHOW_CONFIG_HELP_KEY)  # pozycja „Konfiguracja”
        self._attr_options = options

    def _get_prefs(self) -> dict:
        prefs = self._hass.data[DOMAIN][self._entry_id].setdefault(
            "prefs",
            {
                "back_targets": {},
                "view_targets_by_uuid": {},
                "screen_size_by_uuid": {},
                "refresh_profile_by_uuid": {},
            },
        )
        return prefs

    def _get_store(self) -> Store | None:
        return self._hass.data[DOMAIN][self._entry_id].get("prefs_store")

    def _saved_home_url(self) -> str | None:
        url = (self._get_prefs().get("view_targets_by_uuid") or {}).get(self._device_uuid)
        return str(url).strip() if url else None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attrs: dict[str, str] = {"tablet_uuid": self._device_uuid}
        saved = self._saved_home_url()
        if saved:
            attrs["assigned_home_view"] = _view_name_for_url(self._views, saved) or saved
        back_url = (self._get_prefs().get("back_targets") or {}).get(self._device_uuid)
        if back_url:
            attrs["assigned_back_view"] = _view_name_for_url(self._views, back_url) or back_url
        return attrs

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

        if await api.async_set_device_url(self.uuid, target_url, force=True):
            _LOGGER.info(f"View for {self.uuid} changed successfully.")
            prefs = self._get_prefs()
            prefs.setdefault("view_targets_by_uuid", {})[self._device_uuid] = target_url
            store = self._get_store()
            if store:
                await store.async_save(prefs)
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
        self._device_uuid = normalize_device_uuid(uuid)
        self._attr_unique_id = f"{uuid}_back_view_select"
        self._attr_icon = "mdi:arrow-left-bold"

        self._views = {view["name"]: view["url"] for view in views}
        options = list(self._views.keys())
        options.append(SHOW_CONFIG_HELP_KEY)
        self._attr_options = options

    def _get_prefs(self) -> dict:
        return self._hass.data[DOMAIN][self._entry_id].setdefault(
            "prefs",
            {
                "back_targets": {},
                "view_targets_by_uuid": {},
                "screen_size_by_uuid": {},
                "refresh_profile_by_uuid": {},
            },
        )

    def _get_store(self) -> Store:
        return self._hass.data[DOMAIN][self._entry_id].get("prefs_store")

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        prefs = self._get_prefs()
        attrs: dict[str, str] = {"tablet_uuid": self._device_uuid}
        back_url = (prefs.get("back_targets") or {}).get(self._device_uuid)
        if back_url:
            attrs["assigned_back_view"] = _view_name_for_url(self._views, back_url) or back_url
        home_url = (prefs.get("view_targets_by_uuid") or {}).get(self._device_uuid)
        if home_url:
            attrs["assigned_home_view"] = _view_name_for_url(self._views, home_url) or home_url
        return attrs

    @property
    def current_option(self) -> str | None:
        prefs = self._get_prefs()
        url = prefs.get("back_targets", {}).get(self._device_uuid)
        if not url:
            return None

        return _view_name_for_url(self._views, url)

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
        prefs.setdefault("back_targets", {})[self._device_uuid] = url
        store = self._get_store()
        if store:
            await store.async_save(prefs)

        _LOGGER.info(
            "Saved Back target for tablet %s: %s -> %s",
            self._device_uuid,
            option,
            url,
        )
        self.async_write_ha_state()


class VisionectScreenSizeSelect(VisionectEntity, SelectEntity):
    """Per-device screen class for generated pages (low-battery screen, panel scaling)."""

    def __init__(self, hass: HomeAssistant, coordinator, entry: ConfigEntry, uuid: str):
        super().__init__(coordinator, uuid)
        self._hass = hass
        self._entry_id = entry.entry_id
        self._device_uuid = normalize_device_uuid(uuid)
        self._attr_translation_key = "screen_size_select"
        self._attr_unique_id = f"{uuid}_screen_size_select"
        self._attr_icon = "mdi:tablet-cellphone"
        self._attr_options = list(SCREEN_SIZE_SELECT_OPTIONS)

    def _get_prefs(self) -> dict:
        return self._hass.data[DOMAIN][self._entry_id].setdefault(
            "prefs", {"back_targets": {}, "screen_size_by_uuid": {}, "refresh_profile_by_uuid": {}}
        )

    def _get_store(self) -> Optional[Store]:
        return self._hass.data[DOMAIN][self._entry_id].get("prefs_store")

    def _stored_size(self) -> str | None:
        prefs = self._get_prefs()
        raw = (prefs.get("screen_size_by_uuid") or {}).get(self._device_uuid)
        if raw is None:
            return None
        s = str(raw).strip().lower()
        if s in ("joan6", "joan13"):
            return s
        return None

    @property
    def current_option(self) -> str | None:
        if self._stored_size() is None:
            return "auto"
        return self._stored_size()

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        device_data = self.coordinator.data.get(self.uuid, {}) or {}
        stored = self._stored_size()
        effective = stored if stored else infer_screen_size_from_device(device_data)
        return {"effective_screen_size": effective}

    async def async_select_option(self, option: str) -> None:
        if option not in SCREEN_SIZE_SELECT_OPTIONS:
            _LOGGER.error("Unknown screen size option: %s", option)
            return
        prefs = self._get_prefs()
        prefs.setdefault("screen_size_by_uuid", {})
        if option == "auto":
            prefs["screen_size_by_uuid"].pop(self._device_uuid, None)
        else:
            prefs["screen_size_by_uuid"][self._device_uuid] = option
        store = self._get_store()
        if store:
            await store.async_save(prefs)
        self.async_write_ha_state()


class VisionectRefreshProfileSelect(VisionectEntity, SelectEntity):
    """Per-device adaptive refresh profile (battery/performance behavior)."""

    def __init__(self, hass: HomeAssistant, coordinator, entry: ConfigEntry, uuid: str):
        super().__init__(coordinator, uuid)
        self._hass = hass
        self._entry_id = entry.entry_id
        self._device_uuid = normalize_device_uuid(uuid)
        self._attr_translation_key = "refresh_profile_select"
        self._attr_unique_id = f"{uuid}_refresh_profile_select"
        self._attr_icon = "mdi:speedometer-medium"
        self._attr_options = list(REFRESH_PROFILE_SELECT_OPTIONS)

    def _get_prefs(self) -> dict:
        return self._hass.data[DOMAIN][self._entry_id].setdefault(
            "prefs",
            {"back_targets": {}, "screen_size_by_uuid": {}, "refresh_profile_by_uuid": {}},
        )

    def _get_store(self) -> Optional[Store]:
        return self._hass.data[DOMAIN][self._entry_id].get("prefs_store")

    @property
    def current_option(self) -> str | None:
        prefs = self._get_prefs()
        raw = (prefs.get("refresh_profile_by_uuid") or {}).get(self._device_uuid)
        profile = str(raw or "eco").strip().lower()
        if profile not in REFRESH_PROFILE_SELECT_OPTIONS:
            return "eco"
        return profile

    async def async_select_option(self, option: str) -> None:
        if option not in REFRESH_PROFILE_SELECT_OPTIONS:
            _LOGGER.error("Unknown refresh profile option: %s", option)
            return
        prefs = self._get_prefs()
        prefs.setdefault("refresh_profile_by_uuid", {})[self._device_uuid] = option
        store = self._get_store()
        if store:
            await store.async_save(prefs)
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        api.set_device_refresh_profile(self.uuid, option)
        apply_api_cache_ttls_for_profile_map(api, prefs.get("refresh_profile_by_uuid"))
        _apply_runtime_tuning_for_single_tablet(
            self.hass,
            self._entry_id,
            self.uuid,
            option,
        )
        device_data = self.coordinator.data.get(self.uuid, {}) or {}
        device_name = str(device_data.get("Config", {}).get("Name", "")).strip() or self.uuid
        n_title, n_body = _refresh_profile_notification(self.hass, self._device_uuid, device_name, option)
        async_create(
            self.hass,
            n_body,
            title=n_title,
            notification_id=f"visionect_refresh_profile_{self._device_uuid}",
        )
        self.async_write_ha_state()


class VisionectRotationSelect(VisionectEntity, SelectEntity):
    """Select entity to change the display rotation of a Visionect device."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "rotation_select"
        self._attr_unique_id = f"{uuid}_rotation_select"
        self._attr_icon = "mdi:screen-rotation"
        self._attr_options = ROTATION_OPTIONS

    @property
    def current_option(self) -> str | None:
        device_data = self.coordinator.data.get(self.uuid, {})
        # Rotacja jest przechowywana w Config.DisplayRotation jako int 0-3
        rotation = device_data.get("Config", {}).get("DisplayRotation")
        if rotation is None:
            return None
        return DISPLAY_ROTATIONS.get(str(rotation))

    async def async_select_option(self, option: str) -> None:
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        rotation_num = ROTATION_TO_API.get(option)
        if rotation_num is None:
            _LOGGER.error(f"Unknown rotation option: {option}")
            return

        _LOGGER.info(f"Setting rotation for {self.uuid} to '{option}' (value: {rotation_num})")
        if await api.async_set_display_rotation(self.uuid, rotation_num):
            _LOGGER.info(f"Rotation for {self.uuid} changed successfully.")
            if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["Config"]["DisplayRotation"] = int(rotation_num)
                self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to change rotation for {self.uuid}.")
        await self.coordinator.async_request_refresh()


class VisionectPeriodicSleepSelect(VisionectEntity, SelectEntity):
    """Select entity to change the periodic sleep mode."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "periodic_sleep_select"
        self._attr_name = "Sleep Mode"  # Fallback
        self._attr_unique_id = f"{uuid}_periodic_sleep_select"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_options = SLEEP_PERIODIC_OPTIONS

    @property
    def current_option(self) -> str | None:
        device_data = self.coordinator.data.get(self.uuid, {})
        opts = device_data.get("Options", {})
        
        # If schedule is 0, Sleep Mode is virtually Disabled
        try:
            sched_val = int(float(str(opts.get("SleepSchedule")).replace(',', '.')))
        except (ValueError, TypeError):
            sched_val = -1

        if sched_val == 0:
            return "Disabled"
            
        val = opts.get("PeriodicSleep")
        if val is None:
            return None
        # Map API value back to option name
        for name, api_val in SLEEP_PERIODIC_TO_API.items():
            if str(val).lower() == str(api_val).lower():
                return name
        return None

    async def async_select_option(self, option: str) -> None:
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        val = SLEEP_PERIODIC_TO_API.get(option)
        if val is None:
            return

        options_to_set = {"PeriodicSleep": val}
        # No longer disabling Push mode here to allow both modes simultaneously


        _LOGGER.info(f"Setting PeriodicSleep for {self.uuid} to {option} ({val})")
        if await api.async_set_device_options(self.uuid, options_to_set):
            if self.uuid in self.coordinator.data and "Options" in self.coordinator.data[self.uuid]:
                for k, v in options_to_set.items():
                    self.coordinator.data[self.uuid]["Options"][k] = v
                self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class VisionectPushModeSelect(VisionectEntity, SelectEntity):
    """Select entity to toggle Push mode."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "push_mode_select"
        self._attr_name = "Push Mode"  # Fallback
        self._attr_unique_id = f"{uuid}_push_mode_select"
        self._attr_icon = "mdi:cloud-upload-outline"
        self._attr_options = PUSH_MODE_OPTIONS

    @property
    def current_option(self) -> str | None:
        device_data = self.coordinator.data.get(self.uuid, {})
        val = device_data.get("Options", {}).get("Push")
        if val is None:
            return None
        for name, api_val in PUSH_MODE_TO_API.items():
            if str(val).lower() == str(api_val).lower():
                return name
        return None

    async def async_select_option(self, option: str) -> None:
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        val = PUSH_MODE_TO_API.get(option)
        if val is None:
            return

        options_to_set = {"Push": val}
        # No longer disabling PeriodicSleep here to allow both modes simultaneously


        _LOGGER.info(f"Setting Push mode for {self.uuid} to {option} ({val})")
        if await api.async_set_device_options(self.uuid, options_to_set):
            if self.uuid in self.coordinator.data and "Options" in self.coordinator.data[self.uuid]:
                for k, v in options_to_set.items():
                    self.coordinator.data[self.uuid]["Options"][k] = v
                self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class VisionectSleepScheduleSelect(VisionectEntity, SelectEntity):
    """Select entity for sleep schedule in minutes (0 = Always Online, >0 = cyclic sleep)."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "sleep_schedule_select"
        self._attr_name = "Cykliczny harmonogram uśpienia (minuty)"
        self._attr_unique_id = f"{uuid}_sleep_schedule_select"
        self._attr_icon = "mdi:sleep"
        self._attr_options = SLEEP_SCHEDULE_OPTIONS

    @property
    def current_option(self) -> str | None:
        """Return current sleep schedule based on SleepSchedule value."""
        device_data = self.coordinator.data.get(self.uuid, {})
        opts = device_data.get("Options", {})
        
        try:
            sched_val = int(float(str(opts.get("SleepSchedule", "0")).replace(',', '.')))
        except (ValueError, TypeError):
            sched_val = 0
        
        # Map API value back to option name
        for name, api_val in SLEEP_SCHEDULE_TO_API.items():
            if sched_val == int(api_val):
                return name
        return "0 min (push mode)"

    async def async_select_option(self, option: str) -> None:
        """Handle sleep schedule selection."""
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        minutes = SLEEP_SCHEDULE_TO_API.get(option, "0")
        
        if minutes is None:
            return
        
        minutes_int = int(minutes)
        
        # Przygotuj opcje do ustawienia
        if minutes_int == 0:
            # 0 minut = PUSH MODE (zalecane dla baterii): tablet śpi i wybudza się na push.
            options_to_set = {
                "SleepSchedule": "0",
                "PeriodicSleep": "false",
                "Push": "true"
            }
            _LOGGER.info(f"Setting sleep schedule for {self.uuid} to PUSH MODE (0 min + Push=true)")
        else:
            # >0 minut = cykliczne spanie (Periodic Sleep)
            options_to_set = {
                "SleepSchedule": str(minutes_int),
                "PeriodicSleep": "true",
                "Push": "false"  # Wyłączamy Push - tablet budzi się tylko cyklicznie
            }
            _LOGGER.info(f"Setting sleep schedule for {self.uuid} to {minutes_int} minutes (cyclic sleep)")
        
        if await api.async_set_device_options(self.uuid, options_to_set):
            if self.uuid in self.coordinator.data and "Options" in self.coordinator.data[self.uuid]:
                for k, v in options_to_set.items():
                    self.coordinator.data[self.uuid]["Options"][k] = v
                self.async_write_ha_state()
        await self.coordinator.async_request_refresh()