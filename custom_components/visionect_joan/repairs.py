"""Home Assistant Repairs for Visionect Joan (VSS health, orphan sessions, Sleep Manager)."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir

DOMAIN = "visionect_joan"
_LOGGER = logging.getLogger(__name__)


def _vss_offline_issue_id(entry_id: str) -> str:
    return f"vss_offline_{entry_id}"


def _device_orphan_issue_id(entry_id: str, device_uuid: str) -> str:
    return f"device_orphan_{entry_id}_{device_uuid.lower()}"


def _sleep_manager_issue_id(entry_id: str) -> str:
    return f"sleep_manager_{entry_id}"


def async_sync_vss_offline_issue(hass: HomeAssistant, entry_id: str, offline: bool) -> None:
    """Create or clear repair when VSS API is unreachable."""
    issue_id = _vss_offline_issue_id(entry_id)
    if offline:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="vss_offline",
            translation_placeholders={"entry_id": entry_id},
        )
        return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def async_sync_device_orphan_issue(
    hass: HomeAssistant,
    entry_id: str,
    device_uuid: str,
    *,
    orphan_error: str | None,
    device_name: str | None = None,
) -> None:
    """Create or clear repair when /api/orphans reports a device problem."""
    issue_id = _device_orphan_issue_id(entry_id, device_uuid)
    if orphan_error:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="device_orphan",
            translation_placeholders={
                "device": device_name or device_uuid,
                "error": str(orphan_error),
            },
            data={"entry_id": entry_id, "device_uuid": device_uuid.lower()},
        )
        return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def async_sync_sleep_manager_issue(
    hass: HomeAssistant,
    entry_id: str,
    enabled: bool,
) -> None:
    """Create or clear repair when VSS global Sleep Manager is enabled."""
    issue_id = _sleep_manager_issue_id(entry_id)
    if enabled:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="sleep_manager_enabled",
            translation_placeholders={},
            data={"entry_id": entry_id},
        )
        return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


class SleepManagerRepairFlow(RepairsFlow):
    """Disable VSS Sleep Manager so tablets can stay Always Online."""

    def __init__(self, entry_id: str) -> None:
        self._entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        if user_input is not None:
            entry_data = (self.hass.data.get(DOMAIN) or {}).get(self._entry_id) or {}
            api = entry_data.get("api")
            ok = False
            if api is not None:
                ok = await api.async_toggle_sleep_manager(False)
                entry_data["vss_sleep_manager_enabled"] = False if ok else True
                coordinator = entry_data.get("coordinator")
                if coordinator is not None:
                    coordinator.async_update_listeners()
            async_sync_sleep_manager_issue(
                self.hass, self._entry_id, enabled=not ok
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
        )


class DeviceOrphanRepairFlow(RepairsFlow):
    """Clear WebKit cache + restart session for a tablet with orphan/session problem."""

    def __init__(self, entry_id: str, device_uuid: str) -> None:
        self._entry_id = entry_id
        self._device_uuid = device_uuid.lower()

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        if user_input is not None:
            entry_data = (self.hass.data.get(DOMAIN) or {}).get(self._entry_id) or {}
            api = entry_data.get("api")
            ok = False
            if api is not None:
                try:
                    api.invalidate_orphans_cache()
                    await api.async_clear_webkit_cache([self._device_uuid])
                    ok = await api.async_restart_session(self._device_uuid, silent=True)
                    orphans = await api.async_get_orphans(include_deferred=True) or {}
                    still = api.orphan_error_for_uuid(orphans, self._device_uuid)
                    async_sync_device_orphan_issue(
                        self.hass,
                        self._entry_id,
                        self._device_uuid,
                        orphan_error=still,
                    )
                    coordinator = entry_data.get("coordinator")
                    if coordinator is not None:
                        await coordinator.async_request_refresh()
                    if not ok:
                        _LOGGER.warning(
                            "Orphan repair: session restart failed for %s",
                            self._device_uuid,
                        )
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning(
                        "Orphan repair failed for %s: %s", self._device_uuid, err
                    )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
) -> RepairsFlow:
    """Create a repair flow for fixable Visionect Joan issues."""
    if issue_id.startswith("sleep_manager_"):
        entry_id = issue_id.replace("sleep_manager_", "", 1)
        return SleepManagerRepairFlow(entry_id)
    if issue_id.startswith("device_orphan_"):
        # Prefer data from issue registry when present.
        registry = ir.async_get(hass)
        issue = registry.async_get_issue(DOMAIN, issue_id)
        data = (issue.data if issue else None) or {}
        entry_id = data.get("entry_id")
        device_uuid = data.get("device_uuid")
        if not entry_id or not device_uuid:
            rest = issue_id[len("device_orphan_") :]
            # entry_id has no hyphens typically; device UUID has hyphens.
            parts = rest.rsplit("_", 1)
            if len(parts) == 2 and "-" in parts[1]:
                entry_id, device_uuid = parts[0], parts[1]
            else:
                return ConfirmRepairFlow()
        return DeviceOrphanRepairFlow(str(entry_id), str(device_uuid))
    return ConfirmRepairFlow()
