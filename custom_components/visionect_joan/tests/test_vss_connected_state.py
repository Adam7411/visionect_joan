"""VSS State=charging/sleeping must count as connected, not offline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.const import (  # noqa: E402
    is_vss_device_connected,
)


def test_connected_states() -> None:
    assert is_vss_device_connected("online")
    assert is_vss_device_connected("ONLINE")
    assert is_vss_device_connected("charging")
    assert is_vss_device_connected("sleeping")
    assert is_vss_device_connected("1")
    assert is_vss_device_connected("2")


def test_offline_and_empty() -> None:
    assert not is_vss_device_connected("offline")
    assert not is_vss_device_connected("")
    assert not is_vss_device_connected(None)
    assert not is_vss_device_connected("connection error")
