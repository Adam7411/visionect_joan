"""Tests for Eco-aware session recovery filtering."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.recovery_eco import (  # noqa: PLC2701
    filter_recovery_uuids_eco,
    resolve_expected_dashboard_url,
)
from custom_components.visionect_joan.url_push import urls_equivalent  # noqa: PLC2701


class _FakeApi:
    @staticmethod
    def _normalize_url_for_battery_guard(url: str) -> str:
        return url.split("?")[0].rstrip("/")


class _FakeCoordinator:
    def __init__(self, data: dict):
        self.data = data


def test_resolve_expected_dashboard_url_prefers_per_tablet_target() -> None:
    entry_data = {
        "main_menu_url": "http://ha:5050/Dashboard?widget=default",
        "prefs": {
            "view_targets_by_uuid": {
                "uuid-a": "http://ha:5050/Dashboard?widget=salon",
            }
        },
    }
    assert resolve_expected_dashboard_url(entry_data, "uuid-a").endswith("widget=salon")
    assert resolve_expected_dashboard_url(entry_data, "uuid-b").endswith("widget=default")


def test_filter_eco_skips_when_probe_ok_and_url_matches() -> None:
    app_url = "http://192.168.1.10:5050/Dashboard?widget=joan_salon&count=1"
    coordinator = _FakeCoordinator(
        {
            "uuid-a": {
                "Config": {"Url": app_url},
            }
        }
    )
    entry_data = {
        "main_menu_url": app_url,
        "prefs": {"refresh_profile_by_uuid": {"uuid-a": "eco"}},
    }
    restart, skipped = filter_recovery_uuids_eco(
        ["uuid-a"],
        coordinator,
        entry_data,
        _FakeApi(),
        probe_ok=True,
    )
    assert skipped == ["uuid-a"]
    assert restart == []


def test_filter_eco_restarts_on_orphan_or_alert() -> None:
    coordinator = _FakeCoordinator(
        {
            "uuid-a": {
                "Config": {"Url": "http://ha:5050/Dashboard?widget=x"},
                "OrphanError": "session missing",
            },
            "uuid-b": {
                "Config": {"Url": "http://ha:5050/Dashboard?widget=x"},
            },
        }
    )
    entry_data = {
        "main_menu_url": "http://ha:5050/Dashboard?widget=x",
        "prefs": {
            "refresh_profile_by_uuid": {
                "uuid-a": "eco",
                "uuid-b": "alert",
            }
        },
    }
    restart, skipped = filter_recovery_uuids_eco(
        ["uuid-a", "uuid-b"],
        coordinator,
        entry_data,
        _FakeApi(),
        probe_ok=True,
    )
    assert "uuid-a" in restart
    assert "uuid-b" in restart
    assert skipped == []


def test_filter_no_skip_when_probe_failed() -> None:
    coordinator = _FakeCoordinator(
        {"uuid-a": {"Config": {"Url": "http://ha:5050/same"}}}
    )
    entry_data = {
        "main_menu_url": "http://ha:5050/same",
        "prefs": {"refresh_profile_by_uuid": {"uuid-a": "eco"}},
    }
    restart, skipped = filter_recovery_uuids_eco(
        ["uuid-a"],
        coordinator,
        entry_data,
        _FakeApi(),
        probe_ok=False,
    )
    assert restart == ["uuid-a"]
    assert skipped == []


def test_urls_equivalent_ignores_cb() -> None:
    api = _FakeApi()
    assert urls_equivalent(
        api,
        "http://ha/page?cb=1",
        "http://ha/page?cb=2",
    )
