"""Home Assistant Repairs for Visionect Joan (VSS health, orphan sessions)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

DOMAIN = "visionect_joan"


def _vss_offline_issue_id(entry_id: str) -> str:
    return f"vss_offline_{entry_id}"


def _device_orphan_issue_id(entry_id: str, device_uuid: str) -> str:
    return f"device_orphan_{entry_id}_{device_uuid.lower()}"


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
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="device_orphan",
            translation_placeholders={
                "device": device_name or device_uuid,
                "error": str(orphan_error),
            },
        )
        return
    ir.async_delete_issue(hass, DOMAIN, issue_id)
