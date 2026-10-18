"""Unit tests for VSS Sleep Manager + Default URL config helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.api import VisionectAPI  # noqa: E402


def test_sleep_manager_enabled_from_features() -> None:
    assert VisionectAPI.sleep_manager_enabled_from_config(
        {"Features": ["SleepManager"]}
    )
    assert VisionectAPI.sleep_manager_enabled_from_config(
        {"Features": ["Foo", "SleepManager", "Bar"]}
    )
    assert VisionectAPI.sleep_manager_enabled_from_config(
        {"Global": {"Features": ["SleepManager"]}}
    )
    assert not VisionectAPI.sleep_manager_enabled_from_config({"Features": []})
    assert not VisionectAPI.sleep_manager_enabled_from_config({"Features": ["Other"]})


def test_sleep_manager_enabled_legacy_flag() -> None:
    assert VisionectAPI.sleep_manager_enabled_from_config({"SleepManager": True})
    assert VisionectAPI.sleep_manager_enabled_from_config(
        {"Global": {"SleepManager": True}}
    )
    assert not VisionectAPI.sleep_manager_enabled_from_config({"SleepManager": False})


def test_sleep_manager_enabled_none_or_empty() -> None:
    assert not VisionectAPI.sleep_manager_enabled_from_config(None)
    assert not VisionectAPI.sleep_manager_enabled_from_config({})


def test_device_uses_cyclic_sleep() -> None:
    assert VisionectAPI.device_uses_cyclic_sleep({"Options": {"SleepSchedule": "15"}})
    assert VisionectAPI.device_uses_cyclic_sleep({"Options": {"SleepSchedule": "30.0"}})
    assert not VisionectAPI.device_uses_cyclic_sleep({"Options": {"SleepSchedule": "0"}})
    assert not VisionectAPI.device_uses_cyclic_sleep({"Options": {}})
    assert not VisionectAPI.device_uses_cyclic_sleep(None)


def test_default_url_from_libpyvss_path() -> None:
    cfg = {
        "Engine": {
            "Backend": {"HTML": {"DefaultFields": {"url": "http://ha.local/joan"}}}
        }
    }
    assert VisionectAPI.default_url_from_config(cfg) == "http://ha.local/joan"


def test_default_url_from_okular_uri() -> None:
    cfg = {"Okular": {"Defaults": {"URI": "http://example/default"}}}
    assert VisionectAPI.default_url_from_config(cfg) == "http://example/default"


def test_default_url_from_okular_backend_fields() -> None:
    cfg = {
        "Okular": {
            "Defaults": {"Backend": {"Fields": {"url": "http://fields/url"}}}
        }
    }
    assert VisionectAPI.default_url_from_config(cfg) == "http://fields/url"


def test_apply_default_url_mutates_existing_engine() -> None:
    cfg = {"Engine": {"Backend": {"HTML": {"DefaultFields": {"url": "old"}}}}}
    assert VisionectAPI._apply_default_url_to_config(cfg, "http://new")
    assert (
        cfg["Engine"]["Backend"]["HTML"]["DefaultFields"]["url"] == "http://new"
    )


def test_features_path_prefers_top_level() -> None:
    features, path = VisionectAPI._features_from_config(
        {"Features": ["SleepManager"], "Global": {"Features": []}}
    )
    assert features == ["SleepManager"]
    assert path == ("Features",)


def test_summarize_device_status_history() -> None:
    rows = [
        {"Battery": "80", "RSSI": "-50", "Temperature": "22"},
        {"Status": {"Battery": "70", "RSSI": "-60", "Temperature": "24"}},
    ]
    s = VisionectAPI.summarize_device_status_history(rows)
    assert s["samples"] == 2
    assert s["battery_min"] == 70
    assert s["battery_max"] == 80
    assert s["rssi_min"] == -60
    assert s["temperature_max"] == 24


def test_summarize_hub_from_config() -> None:
    cfg = {
        "Global": {
            "DeploymentName": "Home",
            "Timezone": "Europe/Warsaw",
            "DeviceStatePolling": 15,
            "MasterHost": "127.0.0.1",
        },
        "Okular": {"MaxSessions": 100, "WebkitSessionMemoryLimit": 120, "PageCaching": False},
        "Features": ["SleepManager"],
        "Engine": {
            "Backend": {"HTML": {"DefaultFields": {"url": "http://ha/local"}}}
        },
    }
    hub = VisionectAPI.summarize_hub_from_config(cfg)
    assert hub["deployment_name"] == "Home"
    assert hub["timezone"] == "Europe/Warsaw"
    assert hub["max_sessions"] == 100
    assert hub["webkit_memory_limit_mib"] == 120
    assert hub["sleep_manager"] is True
    assert hub["default_url"] == "http://ha/local"
    assert "SleepManager" in hub["features"]


def test_count_devices_by_state() -> None:
    devices = [
        {"State": "online"},
        {"State": "sleeping"},
        {"State": "charging"},
        {"State": "offline"},
        {"State": "1"},
        {"State": "sending"},
        {"State": "flashing"},
    ]
    c = VisionectAPI.count_devices_by_state(devices)
    assert c["total"] == 7
    assert c["online"] == 2
    assert c["sleeping"] == 1
    assert c["charging"] == 1
    assert c["offline"] == 1
    assert c["sending"] == 1
    assert c["flashing"] == 1
    assert c["connected"] == 6


def test_summarize_device_fleet() -> None:
    devices = [
        {"Options": {"Firmware": "1.2", "Revision": "Joan6", "RequestedFirmware": ""}},
        {"Options": {"Firmware": "1.2", "Revision": "Joan6"}},
        {"Options": {"Firmware": "1.3", "Revision": "Joan13", "RequestedFirmware": "1.4"}},
    ]
    f = VisionectAPI.summarize_device_fleet(devices)
    assert f["firmware_unique"] == 2
    assert f["firmware_versions"]["1.2"] == 2
    assert f["pending_firmware_flash"] == 1
    assert f["hardware_revisions"]["Joan6"] == 2


def test_summarize_server_status_flattens_scalars() -> None:
    s = VisionectAPI.summarize_server_status(
        {"Version": "7.6.5", "Nested": {"A": 1, "B": {"skip": True}}}
    )
    assert s["Version"] == "7.6.5"
    assert s["Nested.A"] == 1
    assert "Nested.B" not in s
