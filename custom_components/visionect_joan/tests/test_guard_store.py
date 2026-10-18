"""Tests for guard state persistence helpers."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.guard_store import (  # noqa: PLC2701
    _parse_last_seen,
    _parse_notified_hours,
)


def test_parse_last_seen_iso() -> None:
    raw = {"uuid-1": "2026-08-12T10:00:00+00:00"}
    parsed = _parse_last_seen(raw)
    assert "uuid-1" in parsed
    assert parsed["uuid-1"].tzinfo is not None


def test_parse_notified_hours_int() -> None:
    assert _parse_notified_hours({"uuid-1": 8, "uuid-2": "5"}) == {
        "uuid-1": 8,
        "uuid-2": 5,
    }


def test_parse_last_seen_skips_invalid() -> None:
    assert _parse_last_seen({"bad": "not-a-date"}) == {}


def test_roundtrip_guard_payload_shape() -> None:
    dt = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    iso = dt.isoformat()
    assert _parse_last_seen({"u": iso})["u"] == dt
