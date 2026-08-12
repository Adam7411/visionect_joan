"""Tests for battery-aware URL push helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from custom_components.visionect_joan.url_push import (
    ATTR_WAKE_TABLET,
    async_push_url_from_service,
    get_configured_url_from_coordinator,
    resolve_service_force_wake,
    urls_equivalent,
)


class _FakeApi:
    def __init__(self) -> None:
        self._metrics = {
            "url_write_attempts": 0,
            "url_write_put_success": 0,
            "url_write_skip_duplicate": 0,
            "url_write_skip_guard": 0,
            "url_write_skip_unchanged": 0,
        }
        self.put_calls: list[tuple[str, str, bool]] = []

    @staticmethod
    def _normalize_url_for_battery_guard(url: str) -> str:
        from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

        raw = str(url or "").strip()
        if not raw or raw.startswith("data:"):
            return raw
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            return raw
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() != "cb"]
        rebuilt = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path or "", "", urlencode(query), "")
        )
        return rebuilt.rstrip("/")

    def get_battery_guard_metrics(self) -> dict:
        return dict(self._metrics)

    async def async_set_device_url(self, uuid: str, url: str, force: bool = False) -> bool:
        self.put_calls.append((uuid, url, force))
        return True


def test_urls_equivalent_ignores_cb_query() -> None:
    api = _FakeApi()
    a = "http://192.168.1.10:8123/local/visionect_cache/x.html?cb=111"
    b = "http://192.168.1.10:8123/local/visionect_cache/x.html?cb=222"
    assert urls_equivalent(api, a, b) is True


def test_resolve_force_wake_eco_default_false() -> None:
    entry_data = {"prefs": {"refresh_profile_by_uuid": {"abc": "eco"}}}
    assert resolve_service_force_wake(entry_data, "abc", {}) is False


def test_resolve_force_wake_wake_tablet_true() -> None:
    entry_data = {"prefs": {"refresh_profile_by_uuid": {"abc": "eco"}}}
    assert resolve_service_force_wake(entry_data, "abc", {ATTR_WAKE_TABLET: True}) is True


def test_resolve_force_wake_alert_profile() -> None:
    entry_data = {"prefs": {"refresh_profile_by_uuid": {"abc": "alert"}}}
    assert resolve_service_force_wake(entry_data, "abc", {}) is True


def test_push_skips_unchanged_without_vss_put() -> None:
    import asyncio

    async def _run() -> None:
        api = _FakeApi()
        coordinator = MagicMock()
        coordinator.data = {
            "dev-1": {"Config": {"Url": "http://ha/local/a.html?cb=1"}},
        }
        entry_data = {"prefs": {"refresh_profile_by_uuid": {"dev-1": "eco"}}}
        result, skipped = await async_push_url_from_service(
            api,
            coordinator,
            entry_data,
            "dev-1",
            "http://ha/local/a.html?cb=99",
            {},
        )
        assert result == "skipped_unchanged"
        assert skipped is True
        assert api.put_calls == []

    asyncio.run(_run())


def test_push_eco_uses_force_false() -> None:
    import asyncio

    async def _run() -> None:
        api = _FakeApi()
        coordinator = MagicMock()
        coordinator.data = {"dev-1": {"Config": {"Url": "http://ha/old.html"}}}
        entry_data = {"prefs": {"refresh_profile_by_uuid": {"dev-1": "eco"}}}
        result, skipped = await async_push_url_from_service(
            api,
            coordinator,
            entry_data,
            "dev-1",
            "http://ha/new.html",
            {},
        )
        assert result == "success"
        assert skipped is False
        assert api.put_calls == [("dev-1", "http://ha/new.html", False)]

    asyncio.run(_run())


def test_get_configured_url_normalizes_uuid() -> None:
    coordinator = MagicMock()
    coordinator.data = {
        "aa-bb-cc": {"Config": {"Url": "http://ha/view.html"}},
    }
    assert get_configured_url_from_coordinator(coordinator, "AA-BB-CC") == "http://ha/view.html"
