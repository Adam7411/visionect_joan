import logging
import asyncio
import ipaddress
import functools
import time
import json
import base64
import hmac
import hashlib
import wsgiref.handlers
import random
from typing import Optional, Dict, List, Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, RequestException, Timeout
from homeassistant.components import persistent_notification

from .const import (
    IP_UNKNOWN, BATTERY_VOLTAGE_DIVIDER, API_PING, API_DEVICES,
    API_DEVICE_DETAIL, API_REBOOT, API_RESTART_SESSION,
    API_SESSION, API_SESSION_DETAIL, DISPLAY_ROTATIONS, SUPPORTED_IMAGE_FORMATS,
    MAX_RETRY_ATTEMPTS, NETWORK_RETRY_DELAY, API_CLEAR_WEB_CACHE,
    API_REBOOT_BATCH, API_RESTART_SESSION_BATCH, API_ORPHANS,
    API_TCLV_LIST, API_TCLV_PARAM, TCLV_SLEEP_MODE_ID, API_SCREENSHOT,
    API_DEVICE_STATUS, HEARTBEAT_INTERVAL_BY_PROFILE,
)

_LOGGER = logging.getLogger(__name__)

class VisionectAPI:
    """Class for communicating with the Visionect API using requests."""

    def __init__(self, hass, api_url: str, username: str = None, password: str = None,
                 api_key: str = None, api_secret: str = None):
        """Initialize the API."""
        self.hass = hass
        self.session = requests.Session()

        # Normalize base URL and ensure default Visionect port 8081 if missing
        url = (api_url or "").strip()
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        parsed = urlparse(url)

        scheme = parsed.scheme or "http"
        host = parsed.hostname or ""
        port = parsed.port  # None if not specified

        # Default port: local VSS uses 8081 on HTTP; HTTPS (cloud / reverse proxy) uses 443.
        if port is None:
            port = 443 if scheme == "https" else 8081

        # IPv6 host formatting
        if ":" in host and not host.startswith("["):
            host_fmt = f"[{host}]"
        else:
            host_fmt = host

        if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
            self.base_url = f"{scheme}://{host_fmt}".rstrip("/")
        else:
            self.base_url = f"{scheme}://{host_fmt}:{port}".rstrip("/")

        self.username = username
        self.password = password
        self.api_key = api_key
        self.api_secret = api_secret
        self.authenticated_by = None

        # Cache for session data to reduce API calls (session data rarely changes)
        self._session_cache = {}
        self._session_cache_ttl = 300  # 5 minutes cache TTL

        # Cache for device list and orphans (rarely change)
        self._devices_cache = None
        self._devices_cache_time = 0
        self._devices_cache_ttl = 60  # 1 minute cache for device list
        self._orphans_cache: dict[bool, dict[str, str]] = {}
        self._orphans_cache_time: dict[bool, float] = {}
        self._orphans_cache_ttl = 60  # 1 minute cache for orphans
        # Recently written session URLs (avoid repeated writes that do not change content)
        self._recent_session_url_write: dict[str, tuple[str, float]] = {}
        self._session_url_min_interval_s = 15.0
        # Battery guard: minimum spacing between different URL writes per device.
        # This protects e-ink tablets from excessive refresh churn caused by frequent automations.
        self._session_url_change_guard_s = 60.0
        self._device_refresh_profile: dict[str, str] = {}
        self._battery_guard_metrics: dict[str, int] = {
            "url_write_attempts": 0,
            "url_write_put_success": 0,
            "url_write_skip_duplicate": 0,
            "url_write_skip_guard": 0,
            "url_write_skip_unchanged": 0,
        }
        # Screenshot preview throttling (HA camera): reduce VSS /device/.../cached.png churn.
        self._screenshot_last_mono: dict[str, float] = {}
        self._screenshot_last_bytes: dict[str, bytes] = {}
        # While enabling cyclic sleep, block watchdog auto-disable of Sleep Manager
        # (race: SM on → sync turns it off before PUT SleepSchedule → VSS HTTP 500).
        self._sleep_manager_hold_until: float = 0.0

    def sleep_manager_hold_active(self) -> bool:
        """True while cyclic-sleep setup must keep Sleep Manager on."""
        return time.monotonic() < float(self._sleep_manager_hold_until or 0.0)

    def begin_sleep_manager_hold(self, seconds: float = 60.0) -> None:
        """Protect Sleep Manager from auto-disable for a short window."""
        try:
            sec = max(5.0, float(seconds))
        except (TypeError, ValueError):
            sec = 60.0
        self._sleep_manager_hold_until = time.monotonic() + sec

    def set_battery_guard_interval(self, seconds: int | float) -> None:
        """Update minimum spacing between different URL writes per device."""
        try:
            sec = float(seconds)
        except (TypeError, ValueError):
            sec = 60.0
        self._session_url_change_guard_s = max(5.0, sec)

    def set_cache_ttls(
        self,
        *,
        session_cache_ttl_s: int | float | None = None,
        devices_cache_ttl_s: int | float | None = None,
        orphans_cache_ttl_s: int | float | None = None,
    ) -> None:
        """Update API cache TTL values at runtime."""
        if session_cache_ttl_s is not None:
            try:
                self._session_cache_ttl = max(60, int(float(session_cache_ttl_s)))
            except (TypeError, ValueError):
                pass
        if devices_cache_ttl_s is not None:
            try:
                self._devices_cache_ttl = max(15, int(float(devices_cache_ttl_s)))
            except (TypeError, ValueError):
                pass
        if orphans_cache_ttl_s is not None:
            try:
                self._orphans_cache_ttl = max(15, int(float(orphans_cache_ttl_s)))
            except (TypeError, ValueError):
                pass

    def get_battery_guard_metrics(self) -> dict[str, int]:
        """Return copy of URL write guard metrics."""
        return dict(self._battery_guard_metrics)

    def set_device_refresh_profile(self, uuid: str, profile: str) -> None:
        """Set per-device adaptive refresh profile used by URL write guard."""
        nu = self._normalize_uuid(uuid)
        p = str(profile or "eco").strip().lower()
        if p not in {"eco", "normal", "alert"}:
            p = "eco"
        self._device_refresh_profile[nu] = p

    def set_device_refresh_profiles(self, mapping: dict[str, str] | None) -> None:
        """Bulk-set per-device refresh profiles."""
        self._device_refresh_profile = {}
        if not isinstance(mapping, dict):
            return
        for uuid, profile in mapping.items():
            self.set_device_refresh_profile(str(uuid), str(profile))

    def _device_guard_interval(self, uuid: str) -> float:
        """Resolve effective URL-change guard interval for a device profile."""
        nu = self._normalize_uuid(uuid)
        profile = self._device_refresh_profile.get(nu, "eco")
        base = float(self._session_url_change_guard_s)
        if profile == "eco":
            return max(base, 120.0)
        if profile == "alert":
            return max(5.0, min(base, 10.0))
        return base

    @staticmethod
    def _normalize_url_for_battery_guard(url: str) -> str:
        """Ignore ?cb= cache-busters when deciding if URL changed (saves e-ink refreshes)."""
        raw = str(url or "").strip()
        if not raw or raw.startswith("data:"):
            return raw
        try:
            parsed = urlparse(raw)
            if parsed.scheme not in {"http", "https"}:
                return raw
            query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() != "cb"]
            rebuilt = urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path or "", "", urlencode(query), "")
            )
            return rebuilt.rstrip("/")
        except Exception:
            return raw

    def _build_hmac_headers(self, method: str, endpoint: str) -> dict:
        """Build headers with HMAC authentication according to Visionect API spec (Simplified)."""
        content_type = "application/json"
        date_hdr = wsgiref.handlers.format_date_time(time.time())
        
        # Upewniamy się, że endpoint dla HMAC zaczyna się od /
        hmac_endpoint = endpoint if endpoint.startswith("/") else "/" + endpoint
        
        # Simplified HMAC: Content-Sha256 is optional and can be omitted for stability
        signature_base = f"{method.upper()}\n\n{content_type}\n{date_hdr}\n{hmac_endpoint}"
        h = hmac.new(self.api_secret.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha256)
        auth = f"{self.api_key}:{base64.b64encode(h.digest()).decode('ascii').strip()}"

        return {
            "Date": date_hdr,
            "Content-Type": content_type,
            "Authorization": auth,
        }

    def _execute_request(self, method, endpoint, silent=False, **kwargs):
        """Executes a synchronous HTTP request with improved error handling and exponential backoff."""
        headers = kwargs.pop("headers", {}) or {}
        retry_count = 0

        # Upewniamy się tylko, że ścieżka zaczyna się od ukośnika
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        # Apply HMAC auth if configured
        if self.authenticated_by == "api_key_hmac" and self.api_key and self.api_secret:
            json_body = None
            if "json" in kwargs:
                try:
                    payload = kwargs.pop("json")
                except Exception:
                    payload = None
                json_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                kwargs["data"] = json_body

            hmac_headers = self._build_hmac_headers(method, endpoint)
            self.session.auth = None
            self.session.cookies.clear()
            headers = {**hmac_headers, **headers}

            # Do not follow redirects for HMAC-signed requests
            kwargs.setdefault("allow_redirects", False)

        url = f"{self.base_url}{endpoint}"
        
        while retry_count < MAX_RETRY_ATTEMPTS:
            try:
                response = self.session.request(method, url, timeout=15, headers=headers, **kwargs)
                
                # Uważamy 3xx jako błąd autoryzacji
                if 300 <= response.status_code < 400:
                    location = response.headers.get("Location", "unknown")
                    if not silent:
                        _LOGGER.warning(
                            f"Got redirect {response.status_code} from {url} to {location} – likely auth failure"
                        )
                    return None
                    
                if response.status_code >= 400:
                    error_msg = (response.text or "").strip()[:500]
                    if not silent:
                        _LOGGER.error(
                            "HTTP Error %s from %s: %s",
                            response.status_code,
                            url,
                            error_msg or "(empty body)",
                        )
                    elif response.status_code == 400:
                        _LOGGER.debug(
                            "HTTP 400 from %s: %s",
                            url,
                            error_msg or "(empty body)",
                        )
                response.raise_for_status()
                
                if response.status_code == 204:
                    return True
                
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return response.json()
                if 'image/' in content_type:
                    return response.content
                return response.text
                
            except (ConnectionError, Timeout) as e:
                retry_count += 1
                if not silent:
                    _LOGGER.warning(f"{e.__class__.__name__} to {url} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    if not silent:
                        _LOGGER.error(f"Failed to connect to {url} after {MAX_RETRY_ATTEMPTS} attempts")
                    return None
                sleep_s = min(2 ** (retry_count - 1), 60) + random.uniform(0, 1)
                time.sleep(sleep_s)
            except RequestException as e:
                if not silent:
                    _LOGGER.error(f"Request error to {url}: {e}")
                return None
        
        return None

    async def _request(self, method, endpoint, silent=False, **kwargs):
        """Asynchronous wrapper for _execute_request."""
        try:
            func = functools.partial(self._execute_request, method, endpoint, silent=silent, **kwargs)
            return await self.hass.async_add_executor_job(func)
        except Exception as e:
            if not silent:
                _LOGGER.error(f"Unexpected error in async request: {e}")
            return None

    def validate_image_url(self, url: str) -> bool:
        """Checks if the URL contains a supported image format."""
        if not url:
            return False
        path = urlparse(url).path.lower()
        return any(path.endswith(f'.{fmt}') for fmt in SUPPORTED_IMAGE_FORMATS)

    async def async_test_authentication(self) -> bool:
        """Tests authentication by trying different methods."""
        if self.api_key and self.api_secret:
            _LOGGER.debug("Testing HMAC authentication with API keys...")
            prev_mode = self.authenticated_by
            self.authenticated_by = "api_key_hmac"
            if await self._request("get", API_PING, silent=True) is not None:
                _LOGGER.info("HMAC authentication successful.")
                return True
            self.authenticated_by = prev_mode
            
            _LOGGER.debug("HMAC didn't work, trying BasicAuth with API keys...")
            self.session.auth = HTTPBasicAuth(self.api_key, self.api_secret)
            if await self._request("get", API_PING, silent=True) is not None:
                self.authenticated_by = "api_key"
                _LOGGER.info("API key authentication successful with BasicAuth.")
                return True
            self.session.auth = None

        if self.username and self.password:
            _LOGGER.debug("Testing authentication with username and password...")
            login_url = f"{self.base_url}/login"
            data = {'username': self.username, 'password': self.password}
            try:
                def _login():
                    response = self.session.post(login_url, data=data, allow_redirects=False, timeout=10)
                    return response.status_code in [200, 302]

                if await self.hass.async_add_executor_job(_login):
                    self.authenticated_by = "credentials"
                    _LOGGER.info("Login credential authentication successful.")
                    return True
                else:
                    _LOGGER.error("Login error, server did not accept credentials.")
            except Exception as e:
                _LOGGER.error(f"Communication error during login: {e}")

        _LOGGER.error("Authentication failed with all available methods.")
        return False

    async def async_get_device_data(self, uuid: str, fetch_session: bool = True) -> Optional[Dict]:
        """Fetches detailed device data and merges it with session data.

        Args:
            uuid: Device UUID
            fetch_session: Whether to fetch session data (default True). Set to False for status-only updates.
        """
        normalized_uuid = self._normalize_uuid(uuid)
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=normalized_uuid))
        if not device_data or not isinstance(device_data, dict):
            return None

        if "Config" not in device_data: device_data["Config"] = {}
        if "Status" not in device_data: device_data["Status"] = {}

        device_data["SessionOptions"] = {}

        # Only fetch session data if requested (session data rarely changes)
        if fetch_session:
            session_data = await self._get_cached_session_data(normalized_uuid)

            if session_data:
                if "Backend" in session_data and "Fields" in session_data["Backend"]:
                    device_data["Config"]["Url"] = session_data["Backend"]["Fields"].get("url", "")
                    device_data["Config"]["ReloadTimeout"] = session_data["Backend"]["Fields"].get("ReloadTimeout", "0")

                if "Options" in session_data:
                    device_data["SessionOptions"] = session_data.get("Options", {})

        if "Displays" in device_data and device_data["Displays"]:
            device_data["Config"]["DisplayRotation"] = device_data["Displays"][0].get("Rotation")

        ip = device_data["Status"].get("IPAddress", "").strip()
        if not ip or ip.lower() in ["unknown", "none", ""]:
            device_data["Status"]["IPAddress"] = IP_UNKNOWN
        else:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                device_data["Status"]["IPAddress"] = IP_UNKNOWN

        if "BatteryVoltage" in device_data["Status"] or "ExternalBattery" in device_data["Status"]:
            try:
                raw_voltage = device_data["Status"].get("BatteryVoltage") or device_data["Status"].get("ExternalBattery")
                device_data["Status"]["BatteryVoltage"] = float(raw_voltage) / BATTERY_VOLTAGE_DIVIDER
            except (ValueError, TypeError):
                device_data["Status"]["BatteryVoltage"] = None

        return device_data

    async def async_get_session_data(self, uuid: str) -> Optional[Dict]:
        """Fetches device session data using the detailed session endpoint."""
        return await self._get_cached_session_data(self._normalize_uuid(uuid))

    async def _get_cached_session_data(self, uuid: str) -> Optional[Dict]:
        """Fetches device session data with caching to reduce API calls."""
        normalized_uuid = self._normalize_uuid(uuid)
        current_time = time.time()

        # Check cache
        if normalized_uuid in self._session_cache:
            cached_data, cached_time = self._session_cache[normalized_uuid]
            if current_time - cached_time < self._session_cache_ttl:
                _LOGGER.debug("Using cached session data for %s", normalized_uuid)
                return cached_data

        # Fetch fresh data
        session_data = await self._request("get", API_SESSION_DETAIL.format(uuid=normalized_uuid))

        # Update cache
        if session_data and isinstance(session_data, dict):
            self._session_cache[normalized_uuid] = (session_data, current_time)
            # Clean old cache entries periodically
            if len(self._session_cache) > 50:
                self._clean_session_cache(current_time)

        return session_data

    def _clean_session_cache(self, current_time: float) -> None:
        """Remove expired entries from session cache."""
        expired_keys = [
            uuid for uuid, (_, cached_time) in self._session_cache.items()
            if current_time - cached_time >= self._session_cache_ttl
        ]
        for key in expired_keys:
            del self._session_cache[key]
        if expired_keys:
            _LOGGER.debug("Cleaned %d expired session cache entries", len(expired_keys))

    def _invalidate_session_cache(self, uuid: str) -> None:
        """Invalidate cache entry for a specific device after session modification."""
        normalized_uuid = self._normalize_uuid(uuid)
        if normalized_uuid in self._session_cache:
            del self._session_cache[normalized_uuid]
            _LOGGER.debug("Invalidated session cache for %s", normalized_uuid)

    async def async_get_all_devices(self) -> Optional[List[Dict]]:
        """Fetches all devices with caching to reduce API calls."""
        current_time = time.time()

        # Check cache
        if self._devices_cache is not None and (current_time - self._devices_cache_time) < self._devices_cache_ttl:
            _LOGGER.debug("Using cached device list")
            return self._devices_cache

        # Fetch fresh data
        devices = await self._request("get", API_DEVICES)

        # Update cache
        if devices is not None:
            self._devices_cache = devices
            self._devices_cache_time = current_time

        return devices

    def _invalidate_devices_cache(self) -> None:
        """Invalidate device list cache after device modification."""
        self._devices_cache = None
        _LOGGER.debug("Invalidated device list cache")

    async def _post_command(self, endpoint_template: str, uuid: str, command_name: str, silent: bool = False) -> bool:
        normalized_uuid = self._normalize_uuid(uuid)
        response = await self._request("post", endpoint_template.format(uuid=normalized_uuid), silent=silent)
        # 204 No Content returns True (success), None indicates failure
        if response is True or (response is not None and response != ""):
            _LOGGER.info(f"Command '{command_name}' for {normalized_uuid} executed successfully.")
            return True
        return False
        
    async def _post_batch_command(self, endpoint: str, uuids: list[str], command_name: str) -> bool:
        """Posts a command to a batch endpoint with a list of UUIDs."""
        if not uuids:
            return True
        response = await self._request("post", endpoint, json=uuids)
        # 204 No Content returns True (success), None indicates failure
        if response is True or (response is not None and response != ""):
            _LOGGER.info(f"Batch command '{command_name}' for {len(uuids)} devices executed successfully.")
            return True
        _LOGGER.error(f"Failed to execute batch command '{command_name}' for UUIDs: {uuids}")
        return False

    async def async_reboot_device(self, uuid: str) -> bool:
        result = await self._post_command(API_REBOOT, uuid, "Reboot device")
        if result:
            self._invalidate_devices_cache()
        return result

    async def async_restart_session(self, uuid: str, silent: bool = False) -> bool:
        normalized_uuid = self._normalize_uuid(uuid)
        restarted = await self._post_command(API_RESTART_SESSION, normalized_uuid, "Restart session", silent=silent)
        if restarted:
            return True

        # VSS sometimes returns 500 on restart for offline devices even when
        # session config is already valid and saved. Treat as soft success if
        # session exists, to avoid false-negative errors.
        session_data = await self.async_get_session_data(normalized_uuid)
        if session_data:
            _LOGGER.warning(
                "Session restart returned an error for %s, but session exists. "
                "Treating as soft success (device may be offline).",
                normalized_uuid,
            )
            return True
        return False
        
    async def async_reboot_devices_batch(self, uuids: list[str]) -> bool:
        result = await self._post_batch_command(API_REBOOT_BATCH, uuids, "Reboot devices")
        if result:
            self._invalidate_devices_cache()
        return result

    async def async_restart_sessions_batch(self, uuids: list[str]) -> bool:
        """Restart sessions in batch with graceful fallback for missing sessions."""
        if not uuids:
            return True

        # VSS may return 500 "no session found" for batch endpoint.
        # Try batch first silently; then fallback to per-session restart.
        batch_resp = await self._request("post", API_RESTART_SESSION_BATCH, silent=True, json=uuids)
        if batch_resp is True or (batch_resp is not None and batch_resp != ""):
            _LOGGER.info(f"Batch command 'Restart sessions' for {len(uuids)} devices executed successfully.")
            return True

        _LOGGER.debug(
            "Batch restart sessions failed (likely missing sessions). Falling back to per-device restart for %d devices.",
            len(uuids),
        )

        succeeded = 0
        failed: list[str] = []
        for uuid in uuids:
            if await self.async_restart_session(uuid, silent=True):
                succeeded += 1
            else:
                failed.append(uuid)

        if failed:
            _LOGGER.debug("Could not restart session for %d device(s): %s", len(failed), failed)

        if succeeded:
            _LOGGER.info("Restarted sessions for %d/%d device(s) using fallback.", succeeded, len(uuids))
            return True
        return False

    async def async_check_health(self) -> bool:
        """Sprawdź czy VSS (Visionect Software Suite) odpowiada.
        
        Używane do wykrycia kiedy VSS wstanie po restarcie HA.
        Zwraca True jeśli VSS jest dostępny, False w przeciwnym razie.
        """
        try:
            # Użyj prostego endpointu - lista urządzeń
            response = await self._request("get", "/api/device/", silent=True)
            # Jeśli dostaliśmy odpowiedź (nawet pustą listę), VSS działa
            return response is not None
        except Exception as e:
            _LOGGER.debug(f"VSS health check failed: {e}")
            return False

    async def async_clear_webkit_cache(self, uuids: list[str]) -> bool:
        return await self._post_batch_command(API_CLEAR_WEB_CACHE, uuids, "Clear Web Cache")
        
    async def async_set_device_url(
        self,
        uuid: str,
        url: str,
        guard_seconds_override: float | None = None,
        *,
        force: bool = False,
    ) -> bool:
        normalized_uuid = self._normalize_uuid(uuid)
        if not self._is_valid_session_url(url):
            _LOGGER.error("Invalid session URL for %s: %s", normalized_uuid, url)
            return False
        self._battery_guard_metrics["url_write_attempts"] += 1

        now_m = time.monotonic()
        recent = self._recent_session_url_write.get(normalized_uuid)
        guard_interval_s = (
            max(5.0, float(guard_seconds_override))
            if guard_seconds_override is not None
            else self._device_guard_interval(normalized_uuid)
        )
        bypass_guard = "setSleep(" in url
        url_norm = self._normalize_url_for_battery_guard(url)
        url_exact = str(url or "").strip()
        profile = str(self._device_refresh_profile.get(normalized_uuid, "eco")).strip().lower()
        eco_aggressive_cb = profile == "eco"
        if recent:
            recent_url, recent_ts = recent
            recent_norm = self._normalize_url_for_battery_guard(recent_url)
            recent_exact = str(recent_url or "").strip()
            # Exact same string (incl. ?cb=) within min interval — always skip.
            # Without force: same path (cb ignored) is duplicate.
            # Eco: always ignore ?cb= (even with force) and use longer window —
            # stops automation chatter that only bumps cache-busters.
            if eco_aggressive_cb:
                same_for_duplicate = url_norm == recent_norm
                dup_window_s = max(self._session_url_min_interval_s, guard_interval_s)
            else:
                same_for_duplicate = (
                    url_exact == recent_exact
                    if force
                    else url_norm == recent_norm
                )
                dup_window_s = self._session_url_min_interval_s
            if same_for_duplicate and (now_m - recent_ts) < dup_window_s:
                self._battery_guard_metrics["url_write_skip_duplicate"] += 1
                _LOGGER.debug(
                    "Skipping duplicate URL write for %s (%.1fs since last write, eco=%s).",
                    normalized_uuid,
                    now_m - recent_ts,
                    eco_aggressive_cb,
                )
                return True
            if (
                not force
                and not bypass_guard
                and url_norm != recent_norm
                and (now_m - recent_ts) < guard_interval_s
            ):
                self._battery_guard_metrics["url_write_skip_guard"] += 1
                _LOGGER.info(
                    "Battery guard: skipping rapid URL change for %s (%.1fs < %.0fs).",
                    normalized_uuid,
                    now_m - recent_ts,
                    guard_interval_s,
                )
                return False

        _LOGGER.debug(f"Fetching session data for {normalized_uuid} to change URL.")
        session_data = await self.async_get_session_data(normalized_uuid)
        if not session_data:
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}

        # VSS requires exact casing: Backend.Name='HTML' and Fields.url lowercase.
        session_data["Backend"]["Name"] = "HTML"
        current_url = str(session_data["Backend"]["Fields"].get("url", "")).strip()
        # Eco: always ignore ?cb= (same page → skip PUT).
        # Other profiles + force/wake_tablet: ?cb= must differ so WebKit reloads.
        already_set = (
            self._normalize_url_for_battery_guard(current_url) == url_norm
            if eco_aggressive_cb or not force
            else current_url == url_exact
        )
        if already_set:
            self._battery_guard_metrics["url_write_skip_unchanged"] += 1
            _LOGGER.debug("Session URL for %s already set, skipping PUT.", normalized_uuid)
            self._recent_session_url_write[normalized_uuid] = (url, now_m)
            return True

        session_data["Backend"]["Fields"]["url"] = url
        session_data["Backend"]["Fields"].pop("Url", None)
        session_data["Backend"]["Fields"]["ReloadTimeout"] = "604800"  # 7 dni - mniej problemów przy restarcie HA

        put_body = self._session_payload_for_put(session_data, normalized_uuid)
        response = await self._request(
            "put", API_SESSION_DETAIL.format(uuid=normalized_uuid), json=put_body
        )
        if response is None:
            return False

        # Invalidate cache after successful modification
        self._invalidate_session_cache(normalized_uuid)

        verified = await self._verify_session_configuration(
            normalized_uuid,
            expected_url=url,
            expected_reload_timeout="604800",
            expected_backend_name="HTML",
        )
        if verified:
            self._battery_guard_metrics["url_write_put_success"] += 1
            self._recent_session_url_write[normalized_uuid] = (url, now_m)
        return verified

    async def async_set_display_rotation(self, uuid: str, display_rotation: str) -> bool:
        nu = self._normalize_uuid(uuid)
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=nu))
        if not (device_data and "Displays" in device_data and device_data["Displays"]):
            return False

        try:
            rotation_value = int(display_rotation)
        except (TypeError, ValueError):
            _LOGGER.error("Invalid display rotation value for %s: %s", nu, display_rotation)
            return False

        if rotation_value not in (0, 1, 2, 3):
            _LOGGER.error("Display rotation out of range for %s: %s", nu, rotation_value)
            return False

        # Visionect API stores screen orientation in Displays[].Rotation.
        for display in device_data.get("Displays", []):
            if isinstance(display, dict):
                display["Rotation"] = rotation_value

        response = await self._request(
            "put", API_DEVICE_DETAIL.format(uuid=nu), json=self._device_payload_for_put(device_data, nu)
        )
        if response is not None:
            return True
        return False

    async def async_set_reload_timeout(self, uuid: str, timeout_seconds: str) -> bool:
        normalized_uuid = self._normalize_uuid(uuid)
        session_data = await self.async_get_session_data(normalized_uuid)
        if not session_data:
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        if not session_data["Backend"].get("Name"):
            session_data["Backend"]["Name"] = "HTML"

        session_data["Backend"]["Fields"]["ReloadTimeout"] = timeout_seconds

        put_body = self._session_payload_for_put(session_data, normalized_uuid)
        response = await self._request(
            "put", API_SESSION_DETAIL.format(uuid=normalized_uuid), json=put_body
        )
        if response is None:
            return False

        # Invalidate cache after successful modification
        self._invalidate_session_cache(normalized_uuid)

        return await self._verify_session_configuration(
            normalized_uuid,
            expected_reload_timeout=str(timeout_seconds),
            expected_backend_name=session_data["Backend"].get("Name"),
        )

    async def async_set_session_options(self, uuid: str, encoding: str = None, dithering: str = None) -> bool:
        normalized_uuid = self._normalize_uuid(uuid)
        session_data = await self.async_get_session_data(normalized_uuid)
        if not session_data:
            return False

        if "Options" not in session_data:
            session_data["Options"] = {}

        if encoding is not None:
            session_data["Options"]["DefaultEncoding"] = encoding
        if dithering is not None:
            session_data["Options"]["DefaultDithering"] = dithering

        put_body = self._session_payload_for_put(session_data, normalized_uuid)
        response = await self._request(
            "put", API_SESSION_DETAIL.format(uuid=normalized_uuid), json=put_body
        )
        if response is not None:
            # Invalidate cache after successful modification
            self._invalidate_session_cache(normalized_uuid)
            return True
        return False

    def _normalize_uuid(self, uuid: str) -> str:
        """Normalize UUID to lowercase as expected by VSS endpoints."""
        return (uuid or "").strip().lower()

    _SESSION_OPTION_KEYS = (
        "DefaultDithering",
        "DefaultEncoding",
        "Beautify",
        "ChangesAutodetect",
        "ResourceLimits",
    )
    _SESSION_FIELD_KEYS = ("url", "ReloadTimeout", "RenderTimeout")

    def _session_payload_for_put(self, session_data: dict, uuid: str) -> dict:
        """Build minimal session JSON accepted by VSS PUT (avoids 400 from extra GET fields)."""
        nu = self._normalize_uuid(uuid)
        backend = session_data.get("Backend") if isinstance(session_data.get("Backend"), dict) else {}
        fields_in = backend.get("Fields") if isinstance(backend.get("Fields"), dict) else {}
        fields_out: dict[str, str] = {}
        url_val = fields_in.get("url")
        if url_val is None:
            url_val = fields_in.get("Url")
        if url_val is not None:
            fields_out["url"] = str(url_val)
        for key in self._SESSION_FIELD_KEYS:
            if key == "url":
                continue
            if key in fields_in and fields_in[key] not in (None, ""):
                fields_out[key] = str(fields_in[key])

        options_in = session_data.get("Options") if isinstance(session_data.get("Options"), dict) else {}
        options_out: dict[str, Any] = {}
        for key in self._SESSION_OPTION_KEYS:
            if key in options_in and options_in[key] not in (None, ""):
                val = options_in[key]
                if key in ("DefaultDithering", "DefaultEncoding"):
                    options_out[key] = str(val)
                else:
                    options_out[key] = val
        if not options_out:
            options_out = {"DefaultDithering": "none", "DefaultEncoding": "4"}

        return {
            "Uuid": nu,
            "Options": options_out,
            "Backend": {
                "Name": str(backend.get("Name") or "HTML"),
                "Fields": fields_out,
            },
        }

    @staticmethod
    def _device_payload_for_put(device_data: dict, uuid: str) -> dict:
        """Writable subset for PUT /api/device/{uuid} (VSS rejects echo of Status/State)."""
        nu = (uuid or "").strip().lower()
        opts = dict(device_data.get("Options") or {})
        for ro_key in ("Firmware", "ScheduledWakeup"):
            opts.pop(ro_key, None)
        displays: list[dict] = []
        for disp in device_data.get("Displays") or []:
            if not isinstance(disp, dict):
                continue
            row = {k: disp[k] for k in ("Id", "Width", "Height", "X", "Y", "Rotation") if k in disp}
            if row:
                displays.append(row)
        payload: dict[str, Any] = {
            "Uuid": nu,
            "SessionId": str(device_data.get("SessionId") or nu),
            "Options": opts,
        }
        if displays:
            payload["Displays"] = displays
        return payload

    def _is_valid_session_url(self, url: str) -> bool:
        """Validate session URL format required by VSS HTML backend."""
        if not url:
            return False
        parsed = urlparse(url.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    async def _verify_session_configuration(
        self,
        uuid: str,
        expected_url: str | None = None,
        expected_reload_timeout: str | None = None,
        expected_backend_name: str | None = None,
    ) -> bool:
        """Verify session config was really persisted by VSS after PUT."""
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error("Session verification failed for %s: no session data returned.", uuid)
            return False

        backend = session_data.get("Backend", {})
        fields = backend.get("Fields", {})

        if expected_backend_name and backend.get("Name") != expected_backend_name:
            _LOGGER.error(
                "Session verification failed for %s: Backend.Name is '%s' (expected '%s').",
                uuid,
                backend.get("Name"),
                expected_backend_name,
            )
            return False

        if expected_url is not None and fields.get("url") != expected_url:
            _LOGGER.error(
                "Session verification failed for %s: Fields.url mismatch ('%s' != '%s').",
                uuid,
                fields.get("url"),
                expected_url,
            )
            return False

        if expected_reload_timeout is not None and str(fields.get("ReloadTimeout")) != str(expected_reload_timeout):
            _LOGGER.error(
                "Session verification failed for %s: ReloadTimeout mismatch ('%s' != '%s').",
                uuid,
                fields.get("ReloadTimeout"),
                expected_reload_timeout,
            )
            return False

        return True

    async def async_autofix_session_consistency(
        self,
        uuid: str,
        *,
        validate_url: bool = True,
        default_reload_timeout: str = "604800",
    ) -> dict[str, Any]:
        """Try to auto-fix common VSS session consistency problems."""
        normalized_uuid = self._normalize_uuid(uuid)
        session_data = await self.async_get_session_data(normalized_uuid)
        if not isinstance(session_data, dict):
            return {"ok": False, "changed": False, "reason": "session_unavailable"}

        backend = session_data.setdefault("Backend", {})
        fields = backend.setdefault("Fields", {})
        changed = False
        fix_notes: list[str] = []

        if backend.get("Name") != "HTML":
            backend["Name"] = "HTML"
            changed = True
            fix_notes.append("Set Backend.Name to HTML")

        url_lc = fields.get("url")
        url_uc = fields.get("Url")
        if not url_lc and url_uc:
            fields["url"] = url_uc
            fields.pop("Url", None)
            url_lc = fields.get("url")
            changed = True
            fix_notes.append("Migrated Fields.Url -> Fields.url")

        if fields.get("ReloadTimeout") in (None, ""):
            fields["ReloadTimeout"] = str(default_reload_timeout)
            changed = True
            fix_notes.append(f"Set ReloadTimeout to {default_reload_timeout}")

        if validate_url and isinstance(url_lc, str) and url_lc:
            if not self._is_valid_session_url(url_lc) and not url_lc.startswith("data:text/html,"):
                return {
                    "ok": False,
                    "changed": False,
                    "reason": "invalid_url_format",
                    "url": url_lc,
                    "fix_notes": fix_notes,
                }

        if not changed:
            return {"ok": True, "changed": False, "reason": "no_changes_needed", "fix_notes": fix_notes}

        put_body = self._session_payload_for_put(session_data, normalized_uuid)
        response = await self._request(
            "put", API_SESSION_DETAIL.format(uuid=normalized_uuid), json=put_body
        )
        if response is None:
            return {"ok": False, "changed": True, "reason": "put_failed", "fix_notes": fix_notes}

        verify_ok = await self._verify_session_configuration(
            normalized_uuid,
            expected_url=fields.get("url"),
            expected_reload_timeout=str(fields.get("ReloadTimeout")),
            expected_backend_name=backend.get("Name"),
        )
        return {
            "ok": bool(verify_ok),
            "changed": True,
            "reason": "fixed_and_verified" if verify_ok else "fixed_but_verify_failed",
            "fix_notes": fix_notes,
        }

    @staticmethod
    def device_uses_cyclic_sleep(details: dict | None) -> bool:
        """True when device Options.SleepSchedule is > 0 minutes."""
        if not isinstance(details, dict):
            return False
        opts = details.get("Options") or {}
        sched = str(opts.get("SleepSchedule", "0")).strip()
        try:
            return int(float(sched.replace(",", "."))) > 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _normalize_features_list(raw) -> list[str]:
        if isinstance(raw, str):
            return [f.strip() for f in raw.split(",") if f.strip()]
        if isinstance(raw, list):
            return [str(f).strip() for f in raw if str(f).strip()]
        return []

    @staticmethod
    def _features_from_config(config: dict) -> tuple[list[str], tuple[str, ...]]:
        """Return (features, path) for VSS Features across schema variants.

        Observed layouts:
        - top-level ``Features`` (VSS 3 / Management Interface Global → Features)
        - ``Global.Features``
        """
        candidates: tuple[tuple[str, ...], ...] = (
            ("Features",),
            ("Global", "Features"),
        )
        for path in candidates:
            node: Any = config
            for key in path[:-1]:
                if not isinstance(node, dict):
                    node = None
                    break
                node = node.get(key)
            if not isinstance(node, dict):
                continue
            if path[-1] not in node:
                continue
            return VisionectAPI._normalize_features_list(node.get(path[-1])), path
        # Prefer creating top-level Features (matches Sleep Manager UI / our PUT history).
        return [], ("Features",)

    @staticmethod
    def _set_features_on_config(
        config: dict, features: list[str], path: tuple[str, ...]
    ) -> None:
        node: Any = config
        for key in path[:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = {}
                node[key] = child
            node = child
        node[path[-1]] = features

    @staticmethod
    def default_url_from_config(config: dict | None) -> str | None:
        """Read HTML Default URL from GET /api/config (schema varies by VSS version).

        Paths (docs + libpyvss):
        - Engine.Backend.HTML.DefaultFields.url  (libpyvss)
        - Okular.Defaults.Backend.Fields.url
        - Okular.Defaults.URI                   (api.visionect.com example)
        """
        if not isinstance(config, dict):
            return None
        engine = (
            (((config.get("Engine") or {}).get("Backend") or {}).get("HTML") or {})
            .get("DefaultFields")
            or {}
        )
        if isinstance(engine, dict):
            url = engine.get("url") or engine.get("URI")
            if url:
                return str(url).strip() or None
        okular = config.get("Okular") if isinstance(config.get("Okular"), dict) else {}
        defaults = okular.get("Defaults") if isinstance(okular.get("Defaults"), dict) else {}
        backend = defaults.get("Backend") if isinstance(defaults.get("Backend"), dict) else {}
        fields = backend.get("Fields") if isinstance(backend.get("Fields"), dict) else {}
        for candidate in (
            fields.get("url"),
            defaults.get("URI"),
            defaults.get("url"),
            okular.get("DefaultURL"),
        ):
            if candidate:
                return str(candidate).strip() or None
        return None

    @staticmethod
    def _apply_default_url_to_config(config: dict, url: str) -> bool:
        """Write Default URL into the first matching schema path; create libpyvss path if none."""
        url = str(url).strip()
        if not url:
            return False
        # Prefer mutating an existing schema so we do not invent nested keys VSS rejects.
        engine_html = (
            ((config.get("Engine") or {}).get("Backend") or {}).get("HTML")
            if isinstance(config.get("Engine"), dict)
            else None
        )
        if isinstance(engine_html, dict):
            fields = engine_html.get("DefaultFields")
            if not isinstance(fields, dict):
                fields = {}
                engine_html["DefaultFields"] = fields
            if fields.get("url") != url:
                fields["url"] = url
                return True
            return False

        okular = config.get("Okular")
        if isinstance(okular, dict):
            defaults = okular.get("Defaults")
            if not isinstance(defaults, dict):
                defaults = {}
                okular["Defaults"] = defaults
            backend = defaults.get("Backend")
            if isinstance(backend, dict):
                fields = backend.get("Fields")
                if not isinstance(fields, dict):
                    fields = {}
                    backend["Fields"] = fields
                if fields.get("url") != url:
                    fields["url"] = url
                    return True
                return False
            if "URI" in defaults or "url" in defaults:
                key = "URI" if "URI" in defaults else "url"
                if defaults.get(key) != url:
                    defaults[key] = url
                    return True
                return False
            defaults["URI"] = url
            return True

        # Fallback: create Engine… path used by libpyvss.
        config.setdefault("Engine", {}).setdefault("Backend", {}).setdefault(
            "HTML", {}
        ).setdefault("DefaultFields", {})["url"] = url
        return True

    @staticmethod
    def sleep_manager_enabled_from_config(config: dict | None) -> bool:
        """True when VSS Global Features include SleepManager (or legacy flag)."""
        if not isinstance(config, dict):
            return False
        if config.get("SleepManager") is True:
            return True
        global_cfg = config.get("Global")
        if isinstance(global_cfg, dict) and global_cfg.get("SleepManager") is True:
            return True
        features, _path = VisionectAPI._features_from_config(config)
        return any(f == "SleepManager" for f in features)

    @staticmethod
    def _config_dig(config: dict, *paths: tuple[str, ...]) -> Any:
        """Return first non-empty value found at one of the dotted-style paths."""
        for path in paths:
            node: Any = config
            ok = True
            for key in path:
                if not isinstance(node, dict) or key not in node:
                    ok = False
                    break
                node = node[key]
            if ok and node not in (None, ""):
                return node
        return None

    @staticmethod
    def summarize_hub_from_config(config: dict | None) -> dict[str, Any]:
        """Safe diagnostic fields from GET /api/config (api.visionect.com + libpyvss)."""
        if not isinstance(config, dict):
            return {}
        features, _path = VisionectAPI._features_from_config(config)
        dig = VisionectAPI._config_dig
        max_sessions = dig(
            config,
            ("Okular", "MaxSessions"),
            ("Engine", "MaxSessions"),
            ("Engine", "Okular", "MaxSessions"),
        )
        webkit_limit = dig(
            config,
            ("Okular", "WebkitSessionMemoryLimit"),
            ("Okular", "WebkitRSSLimit"),
            ("Engine", "WebkitSessionMemoryLimit"),
            ("Engine", "WebkitRSSLimit"),
        )
        page_caching = dig(
            config,
            ("Okular", "PageCaching"),
            ("Engine", "PageCaching"),
        )
        render_timeout = dig(
            config,
            ("Okular", "RenderTimeout"),
            ("Engine", "RenderTimeout"),
        )
        out: dict[str, Any] = {
            "deployment_name": dig(config, ("Global", "DeploymentName")),
            "timezone": dig(config, ("Global", "Timezone")),
            "master_host": dig(config, ("Global", "MasterHost")),
            "device_state_polling_min": dig(config, ("Global", "DeviceStatePolling")),
            "packet_timeout": dig(config, ("Global", "PacketTimeout")),
            "expose_polling": dig(config, ("Global", "ExposePolling")),
            "auto_updater": dig(config, ("Global", "AutoUpdater")),
            "features": list(features),
            "max_sessions": max_sessions,
            "webkit_memory_limit_mib": webkit_limit,
            "page_caching": page_caching,
            "render_timeout_ms": render_timeout,
            "default_url": VisionectAPI.default_url_from_config(config),
            "sleep_manager": VisionectAPI.sleep_manager_enabled_from_config(config),
        }
        return {k: v for k, v in out.items() if v is not None}

    @staticmethod
    def count_devices_by_state(devices: list | None) -> dict[str, int]:
        """Count devices by VSS State (PRTG Joan sensor + our recovery vocabulary)."""
        total = online = sleeping = charging = offline = 0
        flashing = sending = receiving = unavailable = updating = other = 0
        for device in devices or []:
            if not isinstance(device, dict):
                continue
            total += 1
            state = str(device.get("State") or "").strip().lower()
            if state in ("online", "1"):
                online += 1
            elif state in ("sleeping", "2"):
                sleeping += 1
            elif state == "charging":
                charging += 1
            elif state in ("flashing", "flashing complete"):
                flashing += 1
            elif state == "sending":
                sending += 1
            elif state == "receiving":
                receiving += 1
            elif state == "unavailable":
                unavailable += 1
            elif state == "updating":
                updating += 1
            elif state in ("offline", "0", ""):
                offline += 1
            else:
                other += 1
                offline += 1
        # Linked to VSS (not offline) — same idea as is_vss_device_connected + mid-transfer.
        connected = (
            online + sleeping + charging + flashing + sending + receiving + updating
        )
        return {
            "total": total,
            "online": online,
            "sleeping": sleeping,
            "charging": charging,
            "flashing": flashing,
            "sending": sending,
            "receiving": receiving,
            "updating": updating,
            "unavailable": unavailable,
            "offline": offline,
            "other": other,
            "connected": connected,
        }

    @staticmethod
    def summarize_device_fleet(devices: list | None) -> dict[str, Any]:
        """Firmware / revision rollup across GET /api/device (hub diagnostics)."""
        firmwares: dict[str, int] = {}
        revisions: dict[str, int] = {}
        requested: dict[str, int] = {}
        for device in devices or []:
            if not isinstance(device, dict):
                continue
            opts = device.get("Options") if isinstance(device.get("Options"), dict) else {}
            fw = str(opts.get("Firmware") or "").strip()
            rev = str(opts.get("Revision") or "").strip()
            req = str(opts.get("RequestedFirmware") or "").strip()
            if fw and fw.lower() not in ("n/a", "unknown", "-"):
                firmwares[fw] = firmwares.get(fw, 0) + 1
            if rev and rev.lower() not in ("n/a", "unknown", "-"):
                revisions[rev] = revisions.get(rev, 0) + 1
            if req and req.lower() not in ("n/a", "unknown", "-", ""):
                requested[req] = requested.get(req, 0) + 1
        return {
            "firmware_versions": firmwares,
            "hardware_revisions": revisions,
            "requested_firmware": requested,
            "firmware_unique": len(firmwares),
            "pending_firmware_flash": sum(requested.values()),
        }

    @staticmethod
    def summarize_server_status(status: dict | None) -> dict[str, Any]:
        """Flatten useful keys from GET /api/status/ (schema varies by VSS build)."""
        if not isinstance(status, dict):
            return {}
        # Keep only scalar / short values — avoid dumping huge nested blobs into attributes.
        out: dict[str, Any] = {}
        for key, value in status.items():
            if isinstance(value, (str, int, float, bool)):
                out[str(key)] = value
            elif isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    if isinstance(sub_val, (str, int, float, bool)):
                        out[f"{key}.{sub_key}"] = sub_val
        return out

    async def async_get_server_config(self) -> dict | None:
        """GET /api/config/ — full VSS server configuration."""
        config = await self._request("get", "/api/config/", silent=True)
        return config if isinstance(config, dict) else None

    async def async_get_server_status(self) -> dict | None:
        """GET /api/status/ — server runtime status (libpyvss get_status)."""
        status = await self._request("get", "/api/status/", silent=True)
        return status if isinstance(status, dict) else None

    async def async_get_session_list(self) -> list | None:
        """GET /api/session/ — all WebKit sessions."""
        data = await self._request("get", "/api/session/", silent=True)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Some builds wrap the list.
            for key in ("Sessions", "sessions", "Data", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
        return None

    async def async_get_default_url(self) -> str | None:
        """Return VSS HTML Backend Default URL, or None if missing/unreachable."""
        config = await self.async_get_server_config()
        if config is None:
            return None
        return self.default_url_from_config(config)

    async def async_set_default_url(self, url: str) -> bool:
        """PUT Default URL into VSS config (HTML Backend / Engine schema).

        Official docs: GET+PUT /api/config. libpyvss uses
        Engine.Backend.HTML.DefaultFields.url; older docs use Okular.Defaults.URI.
        """
        config = await self.async_get_server_config()
        if not config:
            _LOGGER.error("Could not fetch VSS config to set Default URL.")
            return False
        if not self._apply_default_url_to_config(config, url):
            _LOGGER.debug("VSS Default URL already set to %s", url)
            return True
        resp = await self._request("put", "/api/config/", json=config, silent=True)
        if resp is not None:
            _LOGGER.info("VSS Default URL updated via /api/config.")
            return True
        _LOGGER.error("Failed to PUT VSS Default URL via /api/config.")
        return False

    async def async_is_sleep_manager_enabled(self) -> bool | None:
        """Return Sleep Manager state from GET /api/config/, or None if unreachable."""
        config = await self.async_get_server_config()
        if config is None:
            return None
        return self.sleep_manager_enabled_from_config(config)

    async def async_toggle_sleep_manager(self, enable: bool) -> bool:
        """Enable or disable the global VSS SleepManager feature."""
        # Endpoint /api/config/ requires trailing slash on this VSS build.
        # Docs: sleeping devices cannot be woken remotely while Sleep Manager is on.
        config = await self.async_get_server_config()
        if not config:
            _LOGGER.error("Could not fetch VSS config to toggle SleepManager.")
            return False

        features, path = self._features_from_config(config)
        modified = False

        if enable:
            if "SleepManager" not in features:
                features.append("SleepManager")
                modified = True
        else:
            if "SleepManager" in features:
                features = [f for f in features if f != "SleepManager"]
                modified = True

        for flag_holder in (config, config.get("Global") if isinstance(config.get("Global"), dict) else None):
            if isinstance(flag_holder, dict) and "SleepManager" in flag_holder:
                if flag_holder["SleepManager"] != enable:
                    flag_holder["SleepManager"] = enable
                    modified = True

        if modified:
            self._set_features_on_config(config, features, path)
            resp = await self._request("put", "/api/config/", json=config, silent=True)
            if resp is not None:
                _LOGGER.info(
                    "Global VSS SleepManager has been %s.",
                    "ENABLED" if enable else "DISABLED",
                )
                return True
            _LOGGER.error("Failed to update global VSS config for SleepManager.")
            return False
        return True

    async def async_set_device_option(self, uuid: str, option: str, value: Any) -> bool:
        """Set a single device option (convenience wrapper)."""
        return await self.async_set_device_options(uuid, {option: value})

    async def async_set_device_options(self, uuid: str, options: dict[str, Any]) -> bool:
        """Update device options by fetching full device, merging options, then PUT (clean payload)."""
        nu = self._normalize_uuid(uuid)
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=nu))
        if not device_data:
            _LOGGER.error(f"Could not fetch device data for {nu} to update options.")
            return False

        if "Options" not in device_data:
            device_data["Options"] = {}

        send_tclv = None
        target_sleep_manager = None
        # Read before merge: the loop below overwrites Options, so a later
        # read would see the new schedule and skip the wakeup from cyclic sleep.
        previous_sleep_schedule = str(
            (device_data.get("Options") or {}).get("SleepSchedule", "0")
        )

        for key, value in options.items():
            if value == "disabled":
                device_data["Options"][key] = "false"
            else:
                device_data["Options"][key] = str(value)

        # Logika zarządzania zasilaniem i wymuszaniem stanu ONLINE
        if "SleepSchedule" in options or "PeriodicSleep" in options or "Push" in options:
            sched = device_data["Options"].get("SleepSchedule")
            period = device_data["Options"].get("PeriodicSleep")
            push_val = device_data["Options"].get("Push")
            
            # NOWA LOGIKA: Rozróżnij 3 tryby:
            # 1. Push Mode: SleepSchedule=0 + Push=true (drzemie, budzi na komendy)
            # 2. Always Online: SleepSchedule=0 + Push=false (nigdy nie śpi)
            # 3. Periodic Sleep: SleepSchedule>0 (cykliczne spanie)
            
            is_push_mode = str(sched) == "0" and str(push_val).lower() == "true"
            is_always_online = str(sched) == "0" and str(push_val).lower() != "true"
            
            if is_always_online or is_push_mode:
                # Always Online is the house default: touch + live data, no sleep.
                # Push Mode is treated the same — VSS Sleep Manager is global and
                # would put *all* tablets to sleep (docs: cannot wake remotely).
                _LOGGER.info(
                    "Enforcing ALWAYS ONLINE for %s (SleepSchedule=0, Push=false, SleepManager off).",
                    nu,
                )
                device_data["Options"]["SleepSchedule"] = "0"
                device_data["Options"]["PeriodicSleep"] = "false"
                device_data["Options"]["Push"] = "false"
                send_tclv = "0"
                target_sleep_manager = False
            else:
                # Optional cyclic sleep — only when user picks >0 minutes.
                _LOGGER.info("Enforcing optional Periodic Sleep for %s", nu)
                device_data["Options"]["PeriodicSleep"] = "true"
                device_data["Options"]["Push"] = "false"
                send_tclv = "1"
                target_sleep_manager = True

        # Leaving cyclic sleep → Always Online.
        # VSS ScheduleSleep requires Sleep Manager ON even to *clear* SleepSchedule.
        # Order: clear schedule (SM on) → disable SM → reboot/wake.
        needs_wakeup = False
        if "SleepSchedule" in options:
            new_sched = str(options.get("SleepSchedule", ""))
            old_sched = previous_sleep_schedule
            try:
                old_sched_i = int(float(str(old_sched).replace(",", ".")))
            except (TypeError, ValueError):
                old_sched_i = 0
            if new_sched == "0" and old_sched_i > 0:
                needs_wakeup = True
                _LOGGER.info(
                    "Transitioning %s from %smin sleep to Always Online — clear schedule, then reboot.",
                    nu,
                    old_sched,
                )

        if needs_wakeup:
            device_data["Options"]["SleepSchedule"] = "0"
            device_data["Options"]["PeriodicSleep"] = "false"
            device_data["Options"]["Push"] = "false"
            self.begin_sleep_manager_hold(90.0)
            sm_ok = False
            for attempt in range(3):
                await self.async_toggle_sleep_manager(True)
                await asyncio.sleep(1.5)
                cfg = await self.async_get_server_config()
                if self.sleep_manager_enabled_from_config(cfg):
                    sm_ok = True
                    break
                _LOGGER.warning(
                    "Sleep Manager not confirmed on for Always Online clear %s (try %s/3)",
                    nu,
                    attempt + 1,
                )
            if not sm_ok:
                _LOGGER.error(
                    "Cannot clear cyclic sleep for %s — Sleep Manager stayed off in VSS.",
                    nu,
                )
                self._sleep_manager_hold_until = 0.0
                return False

            clear_resp = await self._request(
                "put",
                API_DEVICE_DETAIL.format(uuid=nu),
                json=self._device_payload_for_put(device_data, nu),
            )
            if clear_resp is None:
                _LOGGER.warning(
                    "PUT SleepSchedule=0 failed for %s — retrying once with Sleep Manager on.",
                    nu,
                )
                await self.async_toggle_sleep_manager(True)
                await asyncio.sleep(2)
                clear_resp = await self._request(
                    "put",
                    API_DEVICE_DETAIL.format(uuid=nu),
                    json=self._device_payload_for_put(device_data, nu),
                )
            if clear_resp is None:
                _LOGGER.error("API error while clearing sleep schedule for %s.", nu)
                self._sleep_manager_hold_until = 0.0
                return False

            self._invalidate_devices_cache()
            self._sleep_manager_hold_until = 0.0
            await self.async_toggle_sleep_manager(False)
            await asyncio.sleep(1)

            _LOGGER.info("Rebooting %s to leave Sleep Manager sleep...", nu)
            await self.async_reboot_device(nu)
            await asyncio.sleep(12)
            await self.async_restart_session(nu)
            await asyncio.sleep(5)
            try:
                session_data = await self.async_get_session_data(nu)
                if session_data and "Backend" in session_data:
                    current_url = session_data["Backend"].get("Fields", {}).get("url", "")
                    if current_url:
                        await self.async_set_device_url(nu, current_url)
                        await asyncio.sleep(2)
            except Exception as e:
                _LOGGER.debug("Could not refresh URL for %s: %s", nu, e)

            # Cancel any residual sleep mode via TCLV (SM already off — no remote wake via SM).
            payload = {"Data": [{"Type": TCLV_SLEEP_MODE_ID, "Control": 1, "Value": "0"}]}
            await self._request(
                "post", API_TCLV_PARAM.format(uuid=nu), json=payload, silent=True
            )

            _LOGGER.info("Options for %s updated successfully (Always Online).", nu)
            return True

        # Cyclic sleep needs SleepManager ON *and verified* before PUT SleepSchedule.
        # VSS returns HTTP 500 ScheduleSleep if SleepManager feature is disabled.
        if target_sleep_manager is True:
            self.begin_sleep_manager_hold(90.0)
            sm_ok = False
            for attempt in range(3):
                await self.async_toggle_sleep_manager(True)
                await asyncio.sleep(1.5)
                cfg = await self.async_get_server_config()
                if self.sleep_manager_enabled_from_config(cfg):
                    sm_ok = True
                    break
                _LOGGER.warning(
                    "Sleep Manager not confirmed on for %s (try %s/3)",
                    nu,
                    attempt + 1,
                )
            if not sm_ok:
                _LOGGER.error(
                    "Cannot set cyclic sleep for %s — Sleep Manager stayed off in VSS.",
                    nu,
                )
                self._sleep_manager_hold_until = 0.0
                return False
        elif target_sleep_manager is False:
            self._sleep_manager_hold_until = 0.0
            await self.async_toggle_sleep_manager(False)
            await asyncio.sleep(1)

        response = await self._request(
            "put", API_DEVICE_DETAIL.format(uuid=nu), json=self._device_payload_for_put(device_data, nu)
        )

        # Retry once if VSS rejected ScheduleSleep because SleepManager flipped off mid-flight.
        if response is None and target_sleep_manager is True:
            _LOGGER.warning(
                "PUT SleepSchedule failed for %s — re-enabling Sleep Manager and retrying once.",
                nu,
            )
            self.begin_sleep_manager_hold(90.0)
            await self.async_toggle_sleep_manager(True)
            await asyncio.sleep(2)
            response = await self._request(
                "put",
                API_DEVICE_DETAIL.format(uuid=nu),
                json=self._device_payload_for_put(device_data, nu),
            )

        if response is not None:
            _LOGGER.info("Options for %s updated successfully.", nu)
            self._invalidate_devices_cache()

            if target_sleep_manager is False:
                # Ensure global flag stays off even if a prior path enabled it.
                await asyncio.sleep(1)
                await self.async_toggle_sleep_manager(False)

            if send_tclv == "1":
                async def _send_tclv_task():
                    await asyncio.sleep(2)
                    payload = {"Data": [{"Type": 52, "Control": 1, "Value": send_tclv}]}
                    await self._request("post", API_TCLV_PARAM.format(uuid=nu), json=payload, silent=True)

                if self.hass:
                    self.hass.loop.create_task(_send_tclv_task())

            return True

        _LOGGER.error("API error while changing options for %s.", nu)
        if target_sleep_manager is True:
            self._sleep_manager_hold_until = 0.0
        return False

    async def async_set_device_name(self, uuid: str, name: str) -> bool:
        """Sets a new name for the device."""
        return await self.async_set_device_option(uuid, "Name", name)

    async def async_wake_device(self, uuid: str) -> bool:
        """Wake device: TCLV sleep cancel + session restart (VSS / Okular)."""
        nu = self._normalize_uuid(uuid)
        payload = {"Data": [{"Type": TCLV_SLEEP_MODE_ID, "Control": 1, "Value": "0"}]}
        tclv_ok = await self._request(
            "post", API_TCLV_PARAM.format(uuid=nu), json=payload, silent=True
        ) is not None
        restart_ok = await self.async_restart_session(nu, silent=True)
        if tclv_ok or restart_ok:
            _LOGGER.info("Wake commands sent for %s (tclv=%s, restart=%s).", nu, tclv_ok, restart_ok)
            return True
        return False

    async def async_get_tclv_list(self, uuid: str) -> list[dict] | None:
        """Return TCLV descriptors for a device."""
        nu = self._normalize_uuid(uuid)
        data = await self._request("get", API_TCLV_LIST.format(uuid=nu))
        if isinstance(data, list):
            return data
        return None

    async def async_get_tclv_values(self, uuid: str, type_ids: list[int]) -> dict[int, str]:
        """Read TCLV values for given type IDs."""
        if not type_ids:
            return {}
        nu = self._normalize_uuid(uuid)
        payload_with_value = {"Data": [{"Type": int(tid), "Control": 0, "Value": ""} for tid in type_ids]}
        payload_no_value = {"Data": [{"Type": int(tid), "Control": 0} for tid in type_ids]}

        # Some VSS/firmware variants are picky about payload shape.
        # Try batched read first (with and without Value field).
        resp = await self._request("post", API_TCLV_PARAM.format(uuid=nu), json=payload_with_value, silent=True)
        if resp is None:
            resp = await self._request("post", API_TCLV_PARAM.format(uuid=nu), json=payload_no_value, silent=True)
        out: dict[int, str] = {}
        
        def _collect_rows(node, bucket: list[dict]):
            """Recursively collect rows that look like TCLV entries."""
            if isinstance(node, dict):
                keys = {str(k).lower() for k in node.keys()}
                # VSS often omits Value on readback (empty); Type+Control still identifies the row.
                if "type" in keys and "control" in keys:
                    bucket.append(node)
                for val in node.values():
                    _collect_rows(val, bucket)
            elif isinstance(node, list):
                for item in node:
                    _collect_rows(item, bucket)

        rows: list[dict] = []
        _collect_rows(resp, rows)

        for row in rows:
            # Support mixed key casing: Type/type, Value/value
            t_raw = row.get("Type", row.get("type"))
            v_raw = row.get("Value", row.get("value", ""))
            try:
                tid = int(t_raw)
            except (TypeError, ValueError):
                continue
            out[tid] = "" if v_raw is None else str(v_raw)

        # Fallback for firmware that does not return all requested values in one response:
        # query missing types one-by-one.
        missing = [int(tid) for tid in type_ids if int(tid) not in out]
        for tid in missing:
            one_payload_with_value = {"Data": [{"Type": int(tid), "Control": 0, "Value": ""}]}
            one_payload_no_value = {"Data": [{"Type": int(tid), "Control": 0}]}
            one_resp = await self._request("post", API_TCLV_PARAM.format(uuid=nu), json=one_payload_with_value, silent=True)
            if one_resp is None:
                one_resp = await self._request("post", API_TCLV_PARAM.format(uuid=nu), json=one_payload_no_value, silent=True)
            one_rows: list[dict] = []
            _collect_rows(one_resp, one_rows)
            for row in one_rows:
                t_raw = row.get("Type", row.get("type"))
                v_raw = row.get("Value", row.get("value", ""))
                try:
                    row_tid = int(t_raw)
                except (TypeError, ValueError):
                    continue
                if row_tid == tid:
                    out[row_tid] = "" if v_raw is None else str(v_raw)
        return out

    async def async_set_tclv_values(self, uuid: str, values_by_type: dict[int, str]) -> bool:
        """Write TCLV values for given type IDs."""
        if not values_by_type:
            return True
        nu = self._normalize_uuid(uuid)
        payload = {
            "Data": [
                {"Type": int(tid), "Control": 1, "Value": str(val)}
                for tid, val in values_by_type.items()
            ]
        }
        resp = await self._request("post", API_TCLV_PARAM.format(uuid=nu), json=payload)
        return resp is not None

    def _resolve_heartbeat_tclv_id(self, tclv_list: list[dict] | None) -> int | None:
        """Find Heart beat interval TCLV type ID by name (firmware IDs vary)."""
        for item in tclv_list or []:
            try:
                tid = int(item.get("ID"))
            except (TypeError, ValueError):
                continue
            name = str(item.get("Name", "")).strip().upper()
            if not name:
                continue
            if "HEART" in name and "BEAT" in name:
                return tid
            if name in {"HEARTBEAT", "HEART_BEAT"}:
                return tid
        return None

    async def async_apply_heartbeat_for_profile(self, uuid: str, profile: str) -> bool:
        """Set device heartbeat interval from adaptive refresh profile (eco/normal/alert)."""
        p = str(profile or "eco").strip().lower()
        if p not in HEARTBEAT_INTERVAL_BY_PROFILE:
            p = "eco"
        value = HEARTBEAT_INTERVAL_BY_PROFILE[p]
        tclv_list = await self.async_get_tclv_list(uuid)
        tid = self._resolve_heartbeat_tclv_id(tclv_list)
        if tid is None:
            _LOGGER.debug(
                "No Heart beat TCLV field for %s — skip profile heartbeat tune (%ss).",
                self._normalize_uuid(uuid),
                value,
            )
            return False
        ok = await self.async_set_tclv_values(uuid, {tid: value})
        if ok:
            _LOGGER.info(
                "Heartbeat TCLV type %s set to %ss for %s (profile=%s).",
                tid,
                value,
                self._normalize_uuid(uuid),
                p,
            )
        return ok

    def _screenshot_min_interval_s(self, uuid_norm: str) -> float:
        """Minimum seconds between live screenshot GETs; stricter in eco for battery."""
        p = str(self._device_refresh_profile.get(uuid_norm, "normal")).strip().lower()
        if p == "eco":
            return 30.0
        if p == "alert":
            return 6.0
        return 12.0

    async def async_get_device_screenshot(self, uuid: str) -> bytes | None:
        """Fetches the device screenshot as binary data, gracefully handling 500 errors from VSS."""
        try:
            nu = self._normalize_uuid(uuid)
            now_m = time.monotonic()
            min_gap = self._screenshot_min_interval_s(nu)
            last_m = self._screenshot_last_mono.get(nu, 0.0)
            if now_m - last_m < min_gap:
                cached = self._screenshot_last_bytes.get(nu)
                if cached:
                    return cached
                return None
            data = await self._request("get", API_SCREENSHOT.format(uuid=nu), silent=True)
            if data:
                self._screenshot_last_bytes[nu] = data
                self._screenshot_last_mono[nu] = time.monotonic()
            return data
        except Exception as e:
            _LOGGER.debug(f"Could not fetch screenshot for {uuid}: {e}")
            return self._screenshot_last_bytes.get(self._normalize_uuid(uuid))

    async def async_get_device_status_history(
        self, 
        uuid: str, 
        from_timestamp: int = None, 
        to_timestamp: int = None,
        group: bool = False
    ) -> list[dict] | None:
        """Fetches historical device status data from /api/devicestatus endpoint.
        
        Args:
            uuid: Device UUID
            from_timestamp: UNIX timestamp start (optional, defaults to 24h ago)
            to_timestamp: UNIX timestamp end (optional, defaults to now)
            group: If True, data is grouped by time intervals
            
        Returns:
            List of status records with Battery, RSSI, Temperature, etc.
            or None on error.
        """
        try:
            now_ts = int(time.time())
            if to_timestamp is None:
                to_timestamp = now_ts
            if from_timestamp is None:
                from_timestamp = now_ts - 86400

            params = [
                f"from={from_timestamp}",
                f"to={to_timestamp}",
            ]
            if group:
                params.append("group=true")
            
            query_string = "?" + "&".join(params) if params else ""
            nu = self._normalize_uuid(uuid)
            endpoint = f"{API_DEVICE_STATUS.format(uuid=nu)}{query_string}"
            
            response = await self._request("get", endpoint, silent=True)
            
            if isinstance(response, list):
                return response
            elif isinstance(response, dict):
                # Sometimes API returns dict with single key
                return [response] if response else []
            return None
            
        except Exception as e:
            _LOGGER.error(
                "Failed to fetch device status history for %s: %s",
                self._normalize_uuid(uuid or ""),
                e,
            )
            return None

    @staticmethod
    def summarize_device_status_history(records: list | None) -> dict[str, Any]:
        """Min/max/last for Battery, RSSI, Temperature from /api/devicestatus rows."""
        out: dict[str, Any] = {
            "samples": 0,
            "battery_min": None,
            "battery_max": None,
            "battery_last": None,
            "rssi_min": None,
            "rssi_max": None,
            "rssi_last": None,
            "temperature_min": None,
            "temperature_max": None,
            "temperature_last": None,
        }
        if not isinstance(records, list) or not records:
            return out

        def _nums(key: str) -> list[float]:
            vals: list[float] = []
            for row in records:
                if not isinstance(row, dict):
                    continue
                # Rows may nest under Status or be flat.
                status = row.get("Status") if isinstance(row.get("Status"), dict) else row
                raw = status.get(key) if isinstance(status, dict) else None
                if raw is None or raw == "":
                    continue
                try:
                    vals.append(float(str(raw).replace(",", ".")))
                except (TypeError, ValueError):
                    continue
            return vals

        out["samples"] = len(records)
        for key, prefix in (
            ("Battery", "battery"),
            ("RSSI", "rssi"),
            ("Temperature", "temperature"),
        ):
            vals = _nums(key)
            if not vals:
                continue
            out[f"{prefix}_min"] = min(vals)
            out[f"{prefix}_max"] = max(vals)
            out[f"{prefix}_last"] = vals[-1]
        return out

    async def async_get_device_status_summary(
        self, uuid: str, *, hours: int = 24
    ) -> dict[str, Any] | None:
        """Fetch last N hours of status history and return min/max summary."""
        hours = max(1, min(int(hours), 168))
        now_ts = int(time.time())
        records = await self.async_get_device_status_history(
            uuid,
            from_timestamp=now_ts - hours * 3600,
            to_timestamp=now_ts,
            group=False,
        )
        if records is None:
            return None
        summary = self.summarize_device_status_history(records)
        summary["hours"] = hours
        summary["uuid"] = self._normalize_uuid(uuid)
        return summary

    def _normalize_orphans_response(self, response) -> dict[str, str]:
        """Normalize /api/orphans payload to {lowercase_uuid: error_message}."""
        if isinstance(response, dict):
            return {
                self._normalize_uuid(str(k)): str(v)
                for k, v in response.items()
                if k and str(k).strip()
            }
        if isinstance(response, list):
            return {
                self._normalize_uuid(str(uuid)): "unknown_issue"
                for uuid in response
                if uuid and str(uuid).strip()
            }
        return {}

    def invalidate_orphans_cache(self) -> None:
        """Drop cached /api/orphans responses (e.g. before manual health check)."""
        self._orphans_cache.clear()
        self._orphans_cache_time.clear()

    def orphan_error_for_uuid(self, orphans: dict[str, str] | None, uuid: str) -> str | None:
        """Return orphan error message for a device UUID, if any."""
        if not orphans:
            return None
        return orphans.get(self._normalize_uuid(uuid))

    async def async_get_orphans(
        self,
        *,
        force: bool = False,
        include_deferred: bool = False,
    ) -> dict[str, str]:
        """Fetch problematic sessions/devices from GET /api/orphans.

        include_deferred=False (default): only real problems — used for Health Status.
        include_deferred=True: also deferred (online without session yet) per VSS API.
        """
        current_time = time.time()
        cache_key = bool(include_deferred)

        if (
            not force
            and cache_key in self._orphans_cache
            and (current_time - self._orphans_cache_time.get(cache_key, 0)) < self._orphans_cache_ttl
        ):
            _LOGGER.debug("Using cached orphans list (include_deferred=%s)", include_deferred)
            return self._orphans_cache[cache_key]

        # Default (health): GET /api/orphans — real problems only.
        # include_deferred=True adds ?all=true (online devices without session yet).
        endpoint = f"{API_ORPHANS}?all=true" if include_deferred else API_ORPHANS

        try:
            response = await self._request("get", endpoint, silent=True)
            orphans_dict = self._normalize_orphans_response(response)
            self._orphans_cache[cache_key] = orphans_dict
            self._orphans_cache_time[cache_key] = current_time
            return orphans_dict
        except Exception as e:
            _LOGGER.error(f"Failed to fetch orphans: {e}")
            return {}