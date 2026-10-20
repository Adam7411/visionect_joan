"""Eco-aware session recovery: skip batch restart when AppDaemon URL is already OK."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from .profile_tuning import normalize_device_uuid, normalize_refresh_profile
from .url_push import get_configured_url_from_coordinator, urls_equivalent

if TYPE_CHECKING:
    from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

# First monotonic timestamp when OrphanError was observed per device (HA process lifetime).
_orphan_first_seen_mono: dict[str, float] = {}
# Orphan flags older than this are treated as stale cache artifacts (skip restart).
_STALE_ORPHAN_AGE_SEC = 300.0


def _orphan_age_sec(uuid_norm: str, *, has_orphan: bool) -> float | None:
    """Track how long OrphanError has been continuously present; clear when gone."""
    if not has_orphan:
        _orphan_first_seen_mono.pop(uuid_norm, None)
        return None
    now = time.monotonic()
    first = _orphan_first_seen_mono.get(uuid_norm)
    if first is None:
        _orphan_first_seen_mono[uuid_norm] = now
        return 0.0
    return now - first


def filter_recovery_uuids_eco(
    uuids: list[str],
    coordinator,
    entry_data: dict[str, Any],
    api: VisionectAPI,
    *,
    probe_ok: bool,
    force_reload: bool = False,
) -> tuple[list[str], list[str]]:
    """Split UUIDs into (restart, skipped) for post-reboot recovery.

    When the AppDaemon probe succeeded, Eco-profile tablets that are online with
    the expected session URL and no orphan flag do not need a session restart
    (avoids unnecessary e-ink wakeups).

    Fresh OrphanError still forces restart; orphan flags seen continuously for
    more than 5 minutes are treated as stale and skipped (fewer false wakeups).

    ``force_reload`` (HostRebootSafetyNet after cold HA start): session URL can
    still match while WebKit shows Connection refused — never Eco-skip then.
    """
    if not uuids:
        return [], []
    if force_reload or not probe_ok:
        return list(uuids), []

    prefs = entry_data.get("prefs") or {}
    profile_map = prefs.get("refresh_profile_by_uuid") or {}
    data = coordinator.data if coordinator and getattr(coordinator, "data", None) else {}

    restart: list[str] = []
    skipped: list[str] = []

    for uuid_val in uuids:
        nu = normalize_device_uuid(uuid_val)
        profile = normalize_refresh_profile(profile_map.get(nu) or profile_map.get(uuid_val))
        if profile in {"alert", "normal"}:
            restart.append(uuid_val)
            continue

        row = data.get(uuid_val) or data.get(nu) or {}
        has_orphan = bool(row.get("OrphanError"))
        orphan_age = _orphan_age_sec(nu, has_orphan=has_orphan)
        if has_orphan:
            if orphan_age is not None and orphan_age > _STALE_ORPHAN_AGE_SEC:
                _LOGGER.info(
                    "%s: Stale orphan flag (%.0fs old), skipping session restart",
                    uuid_val,
                    orphan_age,
                )
                skipped.append(uuid_val)
                continue
            restart.append(uuid_val)
            continue

        expected = resolve_expected_dashboard_url(entry_data, uuid_val)
        current = get_configured_url_from_coordinator(coordinator, uuid_val)
        if expected and current and urls_equivalent(api, current, expected):
            skipped.append(uuid_val)
            continue

        restart.append(uuid_val)

    return restart, skipped


def resolve_expected_dashboard_url(entry_data: dict[str, Any], device_uuid: str) -> str:
    """Expected AppDaemon / main dashboard URL for a tablet."""
    prefs = entry_data.get("prefs") or {}
    nu = normalize_device_uuid(device_uuid)
    view_targets = prefs.get("view_targets_by_uuid") or {}
    for key in (nu, device_uuid, str(device_uuid).strip()):
        target = view_targets.get(key)
        if target and str(target).strip():
            return str(target).strip()
    main = entry_data.get("main_menu_url") or ""
    return str(main).strip()
