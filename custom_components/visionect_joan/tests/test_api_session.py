"""Tests for VSS session PUT payload and battery guard normalization."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.api import VisionectAPI


def _api() -> VisionectAPI:
    return VisionectAPI(MagicMock(), "http://127.0.0.1:8081")


def test_session_payload_for_put_minimal() -> None:
    api = _api()
    session = {
        "Uuid": "abc",
        "Backend": {
            "Name": "HTML",
            "Fields": {
                "url": "http://192.168.1.10:8123/local/x.html",
                "ReloadTimeout": "604800",
                "Status": "should-not-send",
            },
        },
        "Options": {"DefaultDithering": "none", "DefaultEncoding": "4", "Extra": "x"},
        "State": "online",
    }
    body = api._session_payload_for_put(session, "abc")
    assert body["Uuid"] == "abc"
    assert body["Backend"]["Name"] == "HTML"
    assert body["Backend"]["Fields"]["url"] == "http://192.168.1.10:8123/local/x.html"
    assert body["Backend"]["Fields"]["ReloadTimeout"] == "604800"
    assert "State" not in body
    assert "Status" not in body.get("Backend", {}).get("Fields", {})


def test_device_payload_for_put_strips_readonly_options() -> None:
    api = _api()
    device = {
        "Uuid": "abc",
        "SessionId": "abc",
        "Options": {
            "SleepSchedule": "0",
            "Push": "true",
            "Firmware": "n/a",
            "ScheduledWakeup": "2020-01-01",
        },
        "Displays": [{"Id": 0, "Width": 600, "Height": 800, "Rotation": 0}],
        "Status": {"Battery": "80"},
        "State": "online",
    }
    body = api._device_payload_for_put(device, "abc")
    assert "Status" not in body
    assert "State" not in body
    assert "Firmware" not in body["Options"]
    assert "ScheduledWakeup" not in body["Options"]
    assert body["Options"]["Push"] == "true"


def test_normalize_url_for_battery_guard_cb() -> None:
    api = _api()
    a = api._normalize_url_for_battery_guard(
        "http://ha/local/a.html?cb=1&x=1"
    )
    b = api._normalize_url_for_battery_guard(
        "http://ha/local/a.html?x=1&cb=2"
    )
    assert a == b
