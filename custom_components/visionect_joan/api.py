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
from urllib.parse import urlparse

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
    API_TCLV_PARAM, TCLV_SLEEP_MODE_ID, API_SCREENSHOT,
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

        # Add default Visionect Management API port if missing
        if port is None:
            port = 8081

        # IPv6 host formatting
        if ":" in host and not host.startswith("["):
            host_fmt = f"[{host}]"
        else:
            host_fmt = host

        self.base_url = f"{scheme}://{host_fmt}:{port}".rstrip("/")

        self.username = username
        self.password = password
        self.api_key = api_key
        self.api_secret = api_secret
        self.authenticated_by = None

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

        # Upewniamy się tylko, że ścieżka zaczyna się od ukośnika. 
        # NIE dodajemy ukośnika na końcu (trailing slash), bo powoduje to błąd 400 Bad Request!
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
                
                # Traktuj przekierowania 3xx jako błąd autoryzacji
                if 300 <= response.status_code < 400:
                    location = response.headers.get("Location", "unknown")
                    if not silent:
                        _LOGGER.warning(
                            f"Got redirect {response.status_code} from {url} to {location} – likely auth failure"
                        )
                    return None
                    
                if response.status_code >= 400:
                    if not silent:
                        error_msg = response.text
                        _LOGGER.error(f"HTTP Error {response.status_code} from {url}: {error_msg}")
                response.raise_for_status()
                
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

    async def async_get_device_data(self, uuid: str) -> Optional[Dict]:
        """Fetches detailed device data and merges it with session data."""
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if not device_data or not isinstance(device_data, dict):
            return None

        session_data = await self.async_get_session_data(uuid)

        if "Config" not in device_data: device_data["Config"] = {}
        if "Status" not in device_data: device_data["Status"] = {}
        
        device_data["SessionOptions"] = {}

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
        return await self._request("get", API_SESSION_DETAIL.format(uuid=uuid))

    async def async_get_all_devices(self) -> Optional[List[Dict]]:
        return await self._request("get", API_DEVICES)

    async def _post_command(self, endpoint_template: str, uuid: str, command_name: str) -> bool:
        response = await self._request("post", endpoint_template.format(uuid=uuid))
        if response is not None:
            _LOGGER.info(f"Command '{command_name}' for {uuid} executed successfully.")
            return True
        return False
        
    async def _post_batch_command(self, endpoint: str, uuids: list[str], command_name: str) -> bool:
        """Posts a command to a batch endpoint with a list of UUIDs."""
        if not uuids:
            return True
        response = await self._request("post", endpoint, json=uuids)
        if response is not None:
            _LOGGER.info(f"Batch command '{command_name}' for {len(uuids)} devices executed successfully.")
            return True
        _LOGGER.error(f"Failed to execute batch command '{command_name}' for UUIDs: {uuids}")
        return False

    async def async_reboot_device(self, uuid: str) -> bool:
        return await self._post_command(API_REBOOT, uuid, "Reboot device")

    async def async_restart_session(self, uuid: str) -> bool:
        return await self._post_command(API_RESTART_SESSION, uuid, "Restart session")
        
    async def async_reboot_devices_batch(self, uuids: list[str]) -> bool:
        return await self._post_batch_command(API_REBOOT_BATCH, uuids, "Reboot devices")

    async def async_restart_sessions_batch(self, uuids: list[str]) -> bool:
        return await self._post_batch_command(API_RESTART_SESSION_BATCH, uuids, "Restart sessions")

    async def async_clear_webkit_cache(self, uuids: list[str]) -> bool:
        return await self._post_batch_command(API_CLEAR_WEB_CACHE, uuids, "Clear Web Cache")
        
    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        _LOGGER.debug(f"Fetching session data for {uuid} to change URL.")
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        
        session_data["Backend"]["Name"] = "HTML"  
        session_data["Backend"]["Fields"]["url"] = url
        session_data["Backend"]["Fields"]["ReloadTimeout"] = "86400"
        
        response = await self._request("put", API_SESSION_DETAIL.format(uuid=uuid), json=session_data)
        if response is not None:
            return True
        return False

    async def async_set_display_rotation(self, uuid: str, display_rotation: str) -> bool:
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if not (device_data and "Displays" in device_data and device_data["Displays"]):
            return False

        response = await self._request("put", API_DEVICE_DETAIL.format(uuid=uuid), json=device_data)
        if response is not None:
            return True
        return False

    async def async_set_reload_timeout(self, uuid: str, timeout_seconds: str) -> bool:
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        
        session_data["Backend"]["Fields"]["ReloadTimeout"] = timeout_seconds

        response = await self._request("put", API_SESSION_DETAIL.format(uuid=uuid), json=session_data)
        if response is not None:
            return True
        return False
        
    async def async_set_session_options(self, uuid: str, encoding: str = None, dithering: str = None) -> bool:
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            return False

        if "Options" not in session_data:
            session_data["Options"] = {}

        if encoding is not None:
            session_data["Options"]["DefaultEncoding"] = encoding
        if dithering is not None:
            session_data["Options"]["DefaultDithering"] = dithering
            
        response = await self._request("put", API_SESSION_DETAIL.format(uuid=uuid), json=session_data)
        if response is not None:
            return True
        return False

    async def async_toggle_sleep_manager(self, enable: bool) -> bool:
        """Włącza lub wyłącza (globalnie) funkcję SleepManager w ustawieniach VSS."""
        # KRYTYCZNE: Endpoint /api/config/ WYMAGA ukośnika na końcu dla poprawnego działania
        config = await self._request("get", "/api/config/", silent=True)
        if not config:
            _LOGGER.error("Could not fetch VSS config to toggle SleepManager.")
            return False
            
        features = config.get("Features", [])
        if not isinstance(features, list):
             if isinstance(features, str):
                 features = [f.strip() for f in features.split(",") if f.strip()]
             else:
                 features = []
            
        modified = False
        
        # 1. Handle Features list
        if enable:
            if "SleepManager" not in features:
                features.append("SleepManager")
                modified = True
        else:
            if "SleepManager" in features:
                features = [f for f in features if f != "SleepManager"]
                modified = True
        
        # 2. Handle top-level SleepManager flag (if exists in some VSS versions)
        if "SleepManager" in config:
            if config["SleepManager"] != enable:
                config["SleepManager"] = enable
                modified = True
            
        if modified:
            config["Features"] = features
            # KRYTYCZNE: Endpoint /api/config/ WYMAGA ukośnika na końcu dla poprawnego działania
            resp = await self._request("put", "/api/config/", json=config, silent=True)
            if resp is not None:
                _LOGGER.info(f"Global VSS SleepManager has been {'ENABLED' if enable else 'DISABLED'}.")
                return True
            else:
                _LOGGER.error(f"Failed to update global VSS config for SleepManager.")
                return False
        return True

    async def async_set_device_option(self, uuid: str, option: str, value: Any) -> bool:
        """Set a single device option (convenience wrapper)."""
        return await self.async_set_device_options(uuid, {option: value})

    async def async_set_device_options(self, uuid: str, options: dict[str, Any]) -> bool:
        """Update device options by fetching full device, merging options, then PUT (clean payload)."""
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if not device_data:
            _LOGGER.error(f"Could not fetch device data for {uuid} to update options.")
            return False

        if "Options" not in device_data:
            device_data["Options"] = {}

        send_tclv = None
        target_sleep_manager = None

        for key, value in options.items():
            if value == "disabled":
                device_data["Options"][key] = "false"
            else:
                device_data["Options"][key] = str(value)

        # Logika zarządzania zasilaniem i wymuszaniem stanu ONLINE
        if "SleepSchedule" in options or "PeriodicSleep" in options:
            sched = device_data["Options"].get("SleepSchedule")
            period = device_data["Options"].get("PeriodicSleep")

            if str(sched) == "0" or str(period).lower() in ["disabled", "false", "0", "none"]:
                _LOGGER.info(f"Enforcing Always Online mode for {uuid}. Disabling SleepManager.")
                device_data["Options"]["SleepSchedule"] = "0"
                # Krytyczna poprawka - PeriodicSleep musi byc false/0
                device_data["Options"]["PeriodicSleep"] = "false" 
                device_data["Options"]["Push"] = "true"
                send_tclv = "0"
                target_sleep_manager = False # Wyłączamy go globalnie
            else:
                _LOGGER.info(f"Enforcing Periodic Sleep mode for {uuid}")
                device_data["Options"]["PeriodicSleep"] = "true"
                device_data["Options"]["Push"] = "false"
                send_tclv = "1"
                target_sleep_manager = True

        # Jeśli chcemy włączyć uśpienie, musimy najpierw włączyć globalnego SleepManagera (inaczej VSS zwróci błąd 500)
        if target_sleep_manager is True:
            await self.async_toggle_sleep_manager(True)
            await asyncio.sleep(1)

        response = await self._request("put", API_DEVICE_DETAIL.format(uuid=uuid), json=device_data)
        
        if response is not None:
            _LOGGER.info(f"Options for {uuid} updated successfully.")
            
            # Jeśli wyłączyliśmy uśpienie (Always Online), to globalnego managera wyłączamy PO aktualizacji urządzenia
            if target_sleep_manager is False:
                await asyncio.sleep(1)
                await self.async_toggle_sleep_manager(False)
            
            if send_tclv is not None:
                async def _send_tclv_task():
                    await asyncio.sleep(2)
                    payload = {"Data": [{"Type": 52, "Control": 1, "Value": send_tclv}]}
                    await self._request("post", API_TCLV_PARAM.format(uuid=uuid), json=payload, silent=True)
                
                if self.hass:
                    self.hass.loop.create_task(_send_tclv_task())
            
            return True
        
        _LOGGER.error(f"API error while changing options for {uuid}.")
        return False

    async def async_set_device_name(self, uuid: str, name: str) -> bool:
        """Sets a new name for the device."""
        return await self.async_set_device_option(uuid, "Name", name)

    async def async_get_device_screenshot(self, uuid: str) -> bytes | None:
        """Fetches the device screenshot as binary data, gracefully handling 500 errors from VSS."""
        try:
            return await self._request("get", API_SCREENSHOT.format(uuid=uuid), silent=True)
        except Exception as e:
            _LOGGER.debug(f"Could not fetch screenshot for {uuid}: {e}")
            return None

    async def async_get_orphans(self) -> dict[str, str]:
        """Fetches list of problematic sessions/devices from /api/orphans endpoint."""
        try:
            response = await self._request("get", f"{API_ORPHANS}?all=true", silent=True)
            if response and isinstance(response, dict):
                 return response
            elif response and isinstance(response, list):
                 return {uuid: "unknown_issue" for uuid in response}
            return {}
        except Exception as e:
            _LOGGER.error(f"Failed to fetch orphans: {e}")
            return {}