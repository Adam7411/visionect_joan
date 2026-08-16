"""Battery-aware session URL push for Visionect Joan services."""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .const import DOMAIN
from .profile_tuning import normalize_device_uuid, normalize_refresh_profile

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

ATTR_WAKE_TABLET = "wake_tablet"
REFRESH_PROFILE_ALERT = "alert"

PushResult = str  # success | failure | skipped_unchanged | skipped_guard


def resolve_service_force_wake(
    entry_data: dict,
    device_uuid: str,
    call_data: dict | None,
    *,
    intentional_wake: bool = False,
) -> bool:
    """True only when profile/user explicitly allows bypassing battery guard."""
    if intentional_wake:
        return True
    if call_data and call_data.get(ATTR_WAKE_TABLET):
        return True
    prefs = entry_data.get("prefs") or {}
    profile_map = prefs.get("refresh_profile_by_uuid") or {}
    nu = normalize_device_uuid(device_uuid)
    profile = normalize_refresh_profile(profile_map.get(nu) or "eco")
    return profile == REFRESH_PROFILE_ALERT


def get_configured_url_from_coordinator(coordinator, device_uuid: str) -> str:
    """Read last known session URL from coordinator (no extra VSS call)."""
    if coordinator is None or not getattr(coordinator, "data", None):
        return ""
    data = coordinator.data or {}
    nu = normalize_device_uuid(device_uuid)
    row = data.get(device_uuid) or data.get(nu) or {}
    cfg = row.get("Config") if isinstance(row, dict) else {}
    if not isinstance(cfg, dict):
        return ""
    return str(cfg.get("Url") or "").strip()


def urls_equivalent(api: VisionectAPI, url_a: str, url_b: str) -> bool:
    """Compare URLs ignoring ?cb= cache-buster query params."""
    if not url_a or not url_b:
        return False
    norm = api._normalize_url_for_battery_guard  # noqa: SLF001 — shared with VisionectAPI guard
    return norm(url_a) == norm(url_b)


async def async_push_url_from_service(
    api: VisionectAPI,
    coordinator,
    entry_data: dict,
    device_uuid: str,
    url: str,
    call_data: dict | None = None,
    *,
    intentional_wake: bool = False,
) -> tuple[PushResult, bool]:
    """Push URL to VSS session respecting eco battery guard.

    Returns (result, skipped_wake). skipped_wake is True when tablet was not updated.
    """
    if not url:
        return "failure", False

    current = get_configured_url_from_coordinator(coordinator, device_uuid)
    if current and urls_equivalent(api, current, url):
        _LOGGER.debug(
            "Battery push skipped for %s: URL unchanged (no VSS PUT).",
            normalize_device_uuid(device_uuid),
        )
        return "skipped_unchanged", True

    metrics_before = api.get_battery_guard_metrics()
    force = resolve_service_force_wake(
        entry_data, device_uuid, call_data, intentional_wake=intentional_wake
    )
    ok = await api.async_set_device_url(device_uuid, url, force=force)
    if ok:
        return "success", False

    metrics_after = api.get_battery_guard_metrics()
    if (
        not force
        and metrics_after.get("url_write_skip_guard", 0)
        > metrics_before.get("url_write_skip_guard", 0)
    ):
        _LOGGER.debug(
            "Battery guard blocked URL push for %s (profile allows retry later).",
            normalize_device_uuid(device_uuid),
        )
        return "skipped_guard", True

    return "failure", False


def event_status_from_push_result(result: PushResult) -> str:
    """Map internal push result to legacy automation status field."""
    if result in ("success", "skipped_unchanged", "skipped_guard"):
        return "success"
    return "failure"


def fire_command_result(
    hass: HomeAssistant,
    device_uuid: str,
    service_name: str,
    result: PushResult,
    *,
    skipped_wake: bool = False,
) -> None:
    """Fire visionect_joan_command_result with optional skipped_wake hint."""
    from .const import EVENT_COMMAND_RESULT

    payload: dict[str, Any] = {
        "uuid": device_uuid,
        "service": service_name,
        "status": event_status_from_push_result(result),
        "push_result": result,
    }
    if skipped_wake or result in ("skipped_unchanged", "skipped_guard"):
        payload["skipped_wake"] = True
    hass.bus.async_fire(EVENT_COMMAND_RESULT, payload)
