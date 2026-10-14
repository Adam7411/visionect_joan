"""Tests for offline HA notification timing."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.__init__ import (  # noqa: PLC2701
    _notify_offline_if_needed,
    _offline_duration_hours,
)


def test_offline_duration_hours_floor() -> None:
    assert _offline_duration_hours(timedelta(hours=3, minutes=59)) == 3
    assert _offline_duration_hours(timedelta(hours=4, minutes=1)) == 4
    assert _offline_duration_hours(timedelta(hours=8, minutes=30)) == 8


def test_offline_notify_updates_when_hours_increase() -> None:
    hass = MagicMock()
    guard_state: dict = {
        "last_seen": {
            "uuid-1": datetime.now(timezone.utc) - timedelta(hours=9, minutes=10),
        },
        "offline_notified_hours": { "uuid-1": 4 },
    }
    created_messages: list[str] = []

    def _capture(_hass, message, **kwargs):
        created_messages.append(message)

    import custom_components.visionect_joan.__init__ as mod

    mod.async_create_persistent_notification = _capture  # type: ignore[attr-defined]

    _notify_offline_if_needed(
        hass,
        guard_state,
        "uuid-1",
        "Joan test",
        is_online=False,
        enabled=True,
        threshold_hours=4,
    )

    assert created_messages
    assert "9" in created_messages[-1]
    assert guard_state["offline_notified_hours"]["uuid-1"] == 9


def test_offline_notify_skips_when_hours_unchanged() -> None:
    hass = MagicMock()
    guard_state: dict = {
        "last_seen": {
            "uuid-1": datetime.now(timezone.utc) - timedelta(hours=5, minutes=20),
        },
        "offline_notified_hours": {"uuid-1": 5},
    }
    calls = []

    import custom_components.visionect_joan.__init__ as mod

    mod.async_create_persistent_notification = lambda *a, **k: calls.append(1)  # type: ignore[attr-defined]

    _notify_offline_if_needed(
        hass,
        guard_state,
        "uuid-1",
        "Joan test",
        is_online=False,
        enabled=True,
        threshold_hours=4,
    )

    assert calls == []
    assert guard_state["offline_notified_hours"]["uuid-1"] == 5


def test_offline_notify_dismisses_when_back_online() -> None:
    hass = MagicMock()
    guard_state: dict = {
        "last_seen": {"uuid-1": datetime.now(timezone.utc)},
        "offline_notified_hours": {"uuid-1": 8},
    }
    dismissed: list[str] = []

    import custom_components.visionect_joan.__init__ as mod

    mod.async_dismiss_persistent_notification = lambda _h, _id: dismissed.append(_id)  # type: ignore[attr-defined]

    _notify_offline_if_needed(
        hass,
        guard_state,
        "uuid-1",
        "Joan test",
        is_online=True,
        enabled=True,
        threshold_hours=4,
    )

    assert dismissed == ["visionect_offline_uuid-1"]
    assert "uuid-1" not in guard_state["offline_notified_hours"]
