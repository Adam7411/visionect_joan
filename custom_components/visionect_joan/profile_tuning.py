"""Eco / Normal / Alert: shared Visionect HTTP cache TTLs (one API client per config entry).

Dominance matches per-tablet behavior: if any tablet is ``alert``, caches stay fresh;
if none are ``alert`` but any is ``normal``, use normal TTLs; only when all configured
profiles are ``eco`` do we relax caches to reduce HA↔VSS traffic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import VisionectAPI

_PROFILES = frozenset({"eco", "normal", "alert"})


def normalize_refresh_profile(value: str | None) -> str:
    p = str(value or "normal").strip().lower()
    return p if p in _PROFILES else "normal"


def global_refresh_profile_from_map(profile_by_uuid: dict | None) -> str:
    """Pick the strictest profile across tablets (alert > normal > eco)."""
    if not isinstance(profile_by_uuid, dict) or not profile_by_uuid:
        return "normal"
    normalized = {normalize_refresh_profile(v) for v in profile_by_uuid.values()}
    if "alert" in normalized:
        return "alert"
    if "normal" in normalized:
        return "normal"
    return "eco"


def apply_api_cache_ttls_for_profile_map(
    api: VisionectAPI,
    profile_by_uuid: dict | None,
) -> None:
    """Tune in-memory REST cache TTLs on the shared ``VisionectAPI`` instance."""
    gp = global_refresh_profile_from_map(profile_by_uuid)
    if gp == "eco":
        api.set_cache_ttls(
            session_cache_ttl_s=900,
            devices_cache_ttl_s=300,
            orphans_cache_ttl_s=300,
        )
    elif gp == "alert":
        api.set_cache_ttls(
            session_cache_ttl_s=180,
            devices_cache_ttl_s=45,
            orphans_cache_ttl_s=45,
        )
    else:
        api.set_cache_ttls(
            session_cache_ttl_s=300,
            devices_cache_ttl_s=60,
            orphans_cache_ttl_s=60,
        )


def normalize_device_uuid(uuid: str | None) -> str:
    """Lowercase device UUID for prefs maps (one entry per physical tablet)."""
    return str(uuid or "").strip().lower()


_PREFS_UUID_MAP_KEYS = (
    "back_targets",
    "view_targets_by_uuid",
    "screen_size_by_uuid",
    "refresh_profile_by_uuid",
    "safe_last_applied_by_uuid",
)


def normalize_prefs_uuid_maps(prefs: dict | None) -> dict:
    """Re-key per-tablet preference dicts with normalized UUIDs."""
    if not isinstance(prefs, dict):
        return {}
    out = dict(prefs)
    for map_key in _PREFS_UUID_MAP_KEYS:
        raw = out.get(map_key)
        if not isinstance(raw, dict):
            continue
        merged: dict[str, object] = {}
        for k, v in raw.items():
            nu = normalize_device_uuid(str(k))
            if nu:
                merged[nu] = v
        out[map_key] = merged
    return out
