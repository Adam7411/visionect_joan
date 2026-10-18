"""Persist offline-guard timestamps across Home Assistant restarts."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
_SAVE_DEBOUNCE_S = 30.0


def _parse_last_seen(raw: dict[str, Any] | None) -> dict[str, datetime]:
    out: dict[str, datetime] = {}
    if not isinstance(raw, dict):
        return out
    for uuid_val, iso in raw.items():
        key = str(uuid_val).strip()
        if not key or not iso:
            continue
        try:
            dt = datetime.fromisoformat(str(iso))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            out[key] = dt
        except (TypeError, ValueError):
            _LOGGER.debug("Skipping invalid persisted last_seen for %s", key)
    return out


def _parse_notified_hours(raw: dict[str, Any] | None) -> dict[str, int]:
    out: dict[str, int] = {}
    if not isinstance(raw, dict):
        return out
    for uuid_val, hours in raw.items():
        key = str(uuid_val).strip()
        if not key:
            continue
        try:
            out[key] = int(hours)
        except (TypeError, ValueError):
            continue
    return out


async def async_load_guard_persist(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Load ``last_seen`` and ``offline_notified_hours`` from disk."""
    store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry_id}_guard.json")
    raw = await store.async_load() or {}
    return {
        "last_seen": _parse_last_seen(raw.get("last_seen")),
        "offline_notified_hours": _parse_notified_hours(raw.get("offline_notified_hours")),
    }


async def async_save_guard_persist(
    hass: HomeAssistant,
    entry_id: str,
    guard_state: dict[str, Any],
) -> None:
    """Write guard timestamps to disk."""
    store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry_id}_guard.json")
    last_seen_raw: dict[str, str] = {}
    for uuid_val, dt in (guard_state.get("last_seen") or {}).items():
        if isinstance(dt, datetime):
            last_seen_raw[str(uuid_val)] = dt.astimezone(timezone.utc).isoformat()
    payload = {
        "last_seen": last_seen_raw,
        "offline_notified_hours": dict(guard_state.get("offline_notified_hours") or {}),
    }
    await store.async_save(payload)


class GuardPersistScheduler:
    """Debounced guard-state persistence (avoid writing every coordinator tick)."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._cancel: asyncio.TimerHandle | None = None
        self._dirty = False

    def mark_dirty(self) -> None:
        self._dirty = True
        if self._cancel is not None:
            return
        loop = self._hass.loop
        self._cancel = loop.call_later(
            _SAVE_DEBOUNCE_S,
            lambda: self._hass.async_create_task(self._async_flush()),
        )

    async def _async_flush(self) -> None:
        self._cancel = None
        if not self._dirty:
            return
        self._dirty = False
        guard_state = self._hass.data.get(DOMAIN, {}).get("guard_state")
        if not isinstance(guard_state, dict):
            return
        try:
            await async_save_guard_persist(self._hass, self._entry_id, guard_state)
        except Exception as err:
            _LOGGER.debug("Guard persist save failed: %s", err)

    async def async_flush_now(self) -> None:
        if self._cancel is not None:
            self._cancel.cancel()
            self._cancel = None
        await self._async_flush()
