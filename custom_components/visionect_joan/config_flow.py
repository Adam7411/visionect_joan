import logging
from typing import Any, Dict, List, Tuple

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

from .api import VisionectAPI
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_VIEWS,
    CONF_VIEW_NAME,
    CONF_VIEW_URL,
    CONF_CLEANUP_MAX_AGE,
    CONF_CLEANUP_INTERVAL,
    CONF_TABLET_LANGUAGE,
)

_LOGGER = logging.getLogger(__name__)


class VisionectJoanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Visionect Joan server."""
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VisionectJoanOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Initial step: server credentials."""
        errors = {}
        if user_input is not None:
            # Make this flow unique per host so we don't duplicate entries
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                api = VisionectAPI(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input.get(CONF_USERNAME),
                    user_input.get(CONF_PASSWORD),
                    user_input.get(CONF_API_KEY),
                    user_input.get(CONF_API_SECRET),
                )

                if await api.async_test_authentication():
                    devices = await api.async_get_all_devices()
                    device_count = len(devices) if devices else 0

                    host_ip = (
                        user_input[CONF_HOST]
                        .replace("http://", "")
                        .replace("https://", "")
                        .split(":")[0]
                    )
                    title = f"Visionect Joan ({host_ip})"
                    if device_count > 0:
                        title += f" - {device_count} devices"

                    return self.async_create_entry(title=title, data=user_input)

                errors["base"] = "auth_failed"
            except Exception as ex:
                _LOGGER.error("Error during setup: %s", str(ex))
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
                vol.Optional(CONF_API_KEY): str,
                vol.Optional(CONF_API_SECRET): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class VisionectJoanOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow: add/remove/edit predefined views used by selectors."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # Do NOT assign to self.config_entry (deprecated in HA >= 2025.12)
        self._entry = config_entry
        self._views: List[Dict[str, str]] = self._ensure_views_list(
            config_entry.options.get(CONF_VIEWS, [])
        )
        self._edit_index: int | None = None

    def _ensure_views_list(self, raw) -> List[Dict[str, str]]:
        """Return a list of dicts [{'name','url'}], regardless of legacy format."""
        views: List[Dict[str, str]] = []
        if isinstance(raw, list):
            for item in raw:
                # accept dict-like entries only
                name = str(item.get("name", "")).strip()
                url = str(item.get("url", "")).strip()
                if name and url:
                    views.append({"name": name, "url": url})
        elif isinstance(raw, str):
            # legacy "Name: URL" per line format
            for line in raw.strip().splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, url = line.split(":", 1)
                name, url = name.strip(), url.strip()
                if name and url:
                    views.append({"name": name, "url": url})
        return views

    def _labels_map(self) -> Tuple[List[str], Dict[str, int]]:
        """Build display labels list and map back to indices, ensuring uniqueness."""
        labels: List[str] = []
        label_to_index: Dict[str, int] = {}

        counts: Dict[str, int] = {}
        bases: List[str] = []
        for idx, v in enumerate(self._views):
            base = (v.get("name") or "").strip() or f"View {idx+1}"
            bases.append(base)
            counts[base] = counts.get(base, 0) + 1

        for idx, base in enumerate(bases):
            label = base if counts[base] == 1 else f"{base} ({idx+1})"
            # ensure label uniqueness
            while label in label_to_index:
                label = f"{label}*"
            labels.append(label)
            label_to_index[label] = idx

        return labels, label_to_index

    def _save(self) -> config_entries.FlowResult:
        data = {**self._entry.options}
        data[CONF_VIEWS] = self._views
        return self.async_create_entry(title="", data=data)

    async def async_step_init(self, user_input=None):
        return await self.async_step_menu()

    async def async_step_menu(self, user_input=None):
        """Main Menu: Choose between Views management or General Settings."""
        return self.async_show_menu(
            step_id="menu",
            menu_options={
                "views_menu": "Views",  # <--- To przeniesie do podmenu widoków
                "settings": "General Settings (Cache cleanup)", # <--- To przeniesie do ustawień (z poprzedniego kroku)
            },
        )

    async def async_step_views_menu(self, user_input=None):
        """Sub-menu: Add / Remove / Edit views."""
        return self.async_show_menu(
            step_id="views_menu",
            menu_options={
                "add_view": "Add view",
                "delete_view": "Remove view",
                "edit_view": "Edit view",
            },
        )

    async def async_step_add_view(self, user_input=None):
        """Add a single view (Name + URL)."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            name = str(user_input.get(CONF_VIEW_NAME, "")).strip()
            url = str(user_input.get(CONF_VIEW_URL, "")).strip()
            if not name or not url:
                errors["base"] = "invalid_data"
            elif any(v["name"] == name for v in self._views):
                errors["base"] = "name_exists"
            else:
                self._views.append({"name": name, "url": url})
                return self._save()

        schema = vol.Schema(
            {
                vol.Required(CONF_VIEW_NAME): str,
                vol.Required(CONF_VIEW_URL): str,
            }
        )
        return self.async_show_form(step_id="add_view", data_schema=schema, errors=errors)

    async def async_step_delete_view(self, user_input=None):
        """Remove a view from the list (select by name/label)."""
        if not self._views:
            return await self.async_step_views_menu()

        labels, label_to_index = self._labels_map()

        if user_input is not None:
            selected_label = user_input.get("view_to_delete")
            if isinstance(selected_label, str) and selected_label in label_to_index:
                index = label_to_index[selected_label]
                if 0 <= index < len(self._views):
                    self._views.pop(index)
                    return self._save()
            # invalid selection -> back to menu
            return await self.async_step_views_menu()

        schema = vol.Schema({vol.Required("view_to_delete"): vol.In(labels)})
        return self.async_show_form(step_id="delete_view", data_schema=schema)

    async def async_step_edit_view(self, user_input=None):
        """Step 1: Select which view to edit."""
        if not self._views:
            return await self.async_step_views_menu()

        labels, label_to_index = self._labels_map()

        if user_input is not None:
            selected_label = user_input.get("view_to_edit")
            if isinstance(selected_label, str) and selected_label in label_to_index:
                self._edit_index = label_to_index[selected_label]
                return await self.async_step_edit_view_form()
            # invalid selection -> back to menu
            return await self.async_step_views_menu()

        schema = vol.Schema({vol.Required("view_to_edit"): vol.In(labels)})
        return self.async_show_form(step_id="edit_view", data_schema=schema)

    async def async_step_edit_view_form(self, user_input=None):
        """Step 2: Edit selected view (Name + URL) with defaults prefilled."""
        if self._edit_index is None or not (0 <= self._edit_index < len(self._views)):
            # safety: go back if index lost
            return await self.async_step_views_menu()

        current = self._views[self._edit_index]
        errors: Dict[str, str] = {}

        if user_input is not None:
            new_name = str(user_input.get("new_view_name", "")).strip()
            new_url = str(user_input.get("new_view_url", "")).strip()
            if not new_name or not new_url:
                errors["base"] = "invalid_data"
            elif any(v["name"] == new_name and i != self._edit_index for i, v in enumerate(self._views)):
                errors["base"] = "name_exists"
            else:
                self._views[self._edit_index] = {"name": new_name, "url": new_url}
                self._edit_index = None
                return self._save()

        schema = vol.Schema(
            {
                vol.Required("new_view_name", default=current.get("name", "")): str,
                vol.Required("new_view_url", default=current.get("url", "")): str,
            }
        )
        return self.async_show_form(step_id="edit_view_form", data_schema=schema, errors=errors)

    async def async_step_settings(self, user_input=None):
        """Step: Configure general settings (cleanup intervals)."""
        if user_input is not None:
            # Pobieramy obecne opcje i nadpisujemy nowymi wartościami
            new_options = {**self._entry.options, **user_input}
            return self.async_create_entry(title="", data=new_options)

        # Wartości domyślne (jeśli nie ustawione, to 24h i 6h)
        current_age = self._entry.options.get(CONF_CLEANUP_MAX_AGE, 24)
        current_interval = self._entry.options.get(CONF_CLEANUP_INTERVAL, 6)

        schema = vol.Schema(
            {
                vol.Required(CONF_CLEANUP_MAX_AGE, default=current_age): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(CONF_CLEANUP_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Optional(CONF_TABLET_LANGUAGE, default=self._entry.options.get(CONF_TABLET_LANGUAGE, "auto")): vol.In(
                    ["auto", "en", "pl"]
                ),
            }
        )

        return self.async_show_form(
            step_id="settings", 
            data_schema=schema, 
            description_placeholders={
                "cleanup_max_age_label": "Max file age (hours)",
                "cleanup_interval_label": "Cleanup interval (hours)"
            }
        )