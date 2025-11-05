# File: custom_components/visionect_joan/api.py
import logging
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

from .const import (
    IP_UNKNOWN, BATTERY_VOLTAGE_DIVIDER, API_PING, API_DEVICES,
    API_DEVICE_DETAIL, API_REBOOT, API_RESTART_SESSION,
    API_SESSION, API_SESSION_DETAIL, DISPLAY_ROTATIONS, SUPPORTED_IMAGE_FORMATS,
    MAX_RETRY_ATTEMPTS, NETWORK_RETRY_DELAY, API_CLEAR_WEB_CACHE,
    API_REBOOT_BATCH, API_RESTART_SESSION_BATCH,
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

        # Compatibility: remember whether the server prefers trailing slash for endpoints.
        # None = unknown, True = prefer slash, False = prefer no slash
        self._prefer_trailing_slash: Optional[bool] = None

    def _build_hmac_headers(self, method: str, endpoint: str, has_json: bool = False, json_body: str = None) -> dict:
        """Build headers with HMAC authentication according to Visionect API spec."""
        content_type = "application/json"
        date_hdr = wsgiref.handlers.format_date_time(time.time())
        
        content_sha256 = ""
        if has_json and json_body is not None:
            h = hashlib.sha256()
            h.update(json_body.encode("utf-8"))
            content_sha256 = h.hexdigest()

        # RequestPath must match the endpoint exactly (no scheme/host)
        signature_base = f"{method.upper()}\n{content_sha256}\n{content_type}\n{date_hdr}\n{endpoint}"
        h = hmac.new(self.api_secret.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha256)
        auth = f"{self.api_key}:{base64.b64encode(h.digest()).decode('ascii').strip()}"

        headers = {
            "Date": date_hdr,
            "Content-Type": content_type,
            "Authorization": auth,
        }
        
        # If we included content SHA in the signature, also include the header (spec requirement)
        if has_json and json_body is not None:
            headers["Content-Sha256"] = content_sha256

        return headers

    def _toggle_endpoint_slash(self, endpoint: str) -> str:
        return endpoint[:-1] if endpoint.endswith("/") else endpoint + "/"

    def _normalize_endpoint(self, endpoint: str) -> str:
        if self._prefer_trailing_slash is None:
            return endpoint
        if self._prefer_trailing_slash:
            return endpoint if endpoint.endswith("/") else endpoint + "/"
        return endpoint[:-1] if endpoint.endswith("/") else endpoint

    def _execute_request(self, method, endpoint, silent=False, **kwargs):
        """Executes a synchronous HTTP request with improved error handling and exponential backoff."""
        endpoint_eff = self._normalize_endpoint(endpoint)
        url = f"{self.base_url}{endpoint_eff}"
        headers = kwargs.pop("headers", {}) or {}
        retry_count = 0
        
        # Apply HMAC auth if configured
        if self.authenticated_by == "api_key_hmac" and self.api_key and self.api_secret:
            # Ensure we sign EXACTLY the same JSON we send
            json_body = None
            has_json = False
            if "json" in kwargs:
                # Serialize once and send as raw data
                try:
                    payload = kwargs.pop("json")
                except Exception:
                    payload = None
                json_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                kwargs["data"] = json_body
                has_json = True

            hmac_headers = self._build_hmac_headers(
                method, endpoint_eff, has_json=has_json, json_body=json_body
            )
            self.session.auth = None
            headers = {**hmac_headers, **headers}

            # Do not follow redirects for HMAC-signed requests (redirect changes path -> signature mismatch)
            kwargs.setdefault("allow_redirects", False)
        
        while retry_count < MAX_RETRY_ATTEMPTS:
            try:
                response = self.session.request(method, url, timeout=15, headers=headers, **kwargs)
                status = response.status_code

                # Success
                if 200 <= status < 300:
                    # Remember preference for trailing slash if unknown
                    if self._prefer_trailing_slash is None:
                        self._prefer_trailing_slash = endpoint_eff.endswith("/")
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return response.json()
                    if 'image/' in content_type:
                        return response.content
                    return response.text

                # If 301/302/307/308/404 -> attempt fallback with toggled slash
                if status in (301, 302, 307, 308, 404):
                    ep_alt = self._toggle_endpoint_slash(endpoint_eff)
                    try:
                        # Need to recompute headers for new endpoint if HMAC in use
                        local_headers = headers
                        local_kwargs = dict(kwargs)
                        if self.authenticated_by == "api_key_hmac" and self.api_key and self.api_secret:
                            json_body_local = local_kwargs.get("data")
                            local_hmac_headers = self._build_hmac_headers(method, ep_alt, has_json=(json_body_local is not None), json_body=json_body_local)
                            local_headers = {**local_hmac_headers}
                            local_kwargs.setdefault("allow_redirects", False)
                        resp2 = self.session.request(method, f"{self.base_url}{ep_alt}", timeout=15, headers=local_headers, **local_kwargs)
                        if 200 <= resp2.status_code < 300:
                            self._prefer_trailing_slash = ep_alt.endswith("/")
                            content_type = resp2.headers.get('Content-Type', '')
                            if 'application/json' in content_type:
                                return resp2.json()
                            if 'image/' in content_type:
                                return resp2.content
                            return resp2.text
                    except Exception as e_alt:
                        if not silent:
                            _LOGGER.warning(f"Slash fallback failed for {ep_alt}: {e_alt}")

                # Client errors: do not retry
                if 400 <= status < 500:
                    if not silent:
                        _LOGGER.error(f"HTTP {status} from {url}: {response.text[:300]}")
                    return None

                # Server errors: retry with backoff
                retry_count += 1
                if not silent:
                    _LOGGER.warning(f"HTTP {status} from {url} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS})")
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    if not silent:
                        _LOGGER.error(f"Failed after {MAX_RETRY_ATTEMPTS} attempts to {url}")
                    return None
                sleep_s = min(2 ** (retry_count - 1), 60) + random.uniform(0, 1)
                time.sleep(sleep_s)
            except (ConnectionError, Timeout) as e:
                retry_count += 1
                if not silent:
                    _LOGGER.warning(
                        f"{e.__class__.__name__} to {url} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}"
                    )
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    if not silent:
                        _LOGGER.error(f"Failed to connect to {url} after {MAX_RETRY_ATTEMPTS} attempts")
                    return None
                # Exponential backoff with jitter
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
        # Parse URL and check file extension without query parameters
        path = urlparse(url).path.lower()
        return any(path.endswith(f'.{fmt}') for fmt in SUPPORTED_IMAGE_FORMATS)

    async def async_test_authentication(self) -> bool:
        """Tests authentication by trying different methods."""
        # Try HMAC authentication first if API keys are provided
        if self.api_key and self.api_secret:
            _LOGGER.debug("Testing HMAC authentication with API keys...")
            prev_mode = self.authenticated_by
            self.authenticated_by = "api_key_hmac"
            if await self._request("get", API_PING, silent=True) is not None:
                _LOGGER.info("HMAC authentication successful.")
                return True
            self.authenticated_by = prev_mode
            
            # If HMAC fails, try BasicAuth as fallback
            _LOGGER.debug("HMAC didn't work, trying BasicAuth with API keys...")
            self.session.auth = HTTPBasicAuth(self.api_key, self.api_secret)
            if await self._request("get", API_PING, silent=True) is not None:
                self.authenticated_by = "api_key"
                _LOGGER.info("API key authentication successful with BasicAuth.")
                return True
            self.session.auth = None

        # Try username/password with session cookies as last resort
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

        if "BatteryVoltage" in device_data["Status"]:
            try:
                device_data["Status"]["BatteryVoltage"] = float(device_data["Status"]["BatteryVoltage"]) / BATTERY_VOLTAGE_DIVIDER
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
        """Reboots a list of devices in a single API call."""
        return await self._post_batch_command(API_REBOOT_BATCH, uuids, "Reboot devices")

    async def async_restart_sessions_batch(self, uuids: list[str]) -> bool:
        """Restarts sessions for a list of devices in a single API call."""
        return await self._post_batch_command(API_RESTART_SESSION_BATCH, uuids, "Restart sessions")

    async def async_clear_webkit_cache(self, uuids: list[str]) -> bool:
        """Clears the webkit cache for the specified session UUIDs."""
        return await self._post_batch_command(API_CLEAR_WEB_CACHE, uuids, "Clear Web Cache")
        
    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        """Sets the device URL via the API, forcing a constant session type and long lifetime."""
        _LOGGER.debug(f"Fetching session data for {uuid} to change URL.")
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error(f"Could not fetch session data for device {uuid}")
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        
        # Use Name according to Visionect API docs
        session_data["Backend"]["Name"] = "HTML"  
        session_data["Backend"]["Fields"]["url"] = url
        session_data["Backend"]["Fields"]["ReloadTimeout"] = "86400"
        
        endpoint = f"/api/session/{uuid}"
        response = await self._request("put", endpoint, json=session_data)
        if response is not None:
            _LOGGER.info(f"Device URL for {uuid} changed to: {url}")
            return True
        _LOGGER.error(f"Failed to change device URL for {uuid} via API")
        return False

    async def async_set_display_rotation(self, uuid: str, display_rotation: str) -> bool:
        """Sets the device's screen rotation by sending a minimal payload."""
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if not (device_data and "Displays" in device_data and device_data["Displays"]):
            _LOGGER.error(f"Could not fetch or parse display data for device {uuid} to update rotation.")
            return False

        device_data["Displays"][0]["Rotation"] = int(display_rotation)
        payload = device_data

        response = await self._request("put", API_DEVICE_DETAIL.format(uuid=uuid), json=payload)
        if response is not None:
            _LOGGER.info(f"Screen rotation for {uuid} set to {display_rotation}.")
            return True
        _LOGGER.error(f"API error while changing rotation for {uuid}.")
        return False

    async def async_set_reload_timeout(self, uuid: str, timeout_seconds: str) -> bool:
        """Sets the refresh interval (ReloadTimeout) for the device session."""
        _LOGGER.debug(f"Fetching session data for {uuid} to change ReloadTimeout.")
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error(f"Could not fetch session data for device {uuid}")
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        
        session_data["Backend"]["Fields"]["ReloadTimeout"] = timeout_seconds

        endpoint = f"/api/session/{uuid}"
        response = await self._request("put", endpoint, json=session_data)
        if response is not None:
            _LOGGER.info(f"ReloadTimeout for {uuid} changed to: {timeout_seconds}s")
            return True
        _LOGGER.error(f"Failed to change ReloadTimeout for {uuid} via API")
        return False
        
    async def async_set_session_options(self, uuid: str, encoding: str = None, dithering: str = None) -> bool:
        """Sets session options like encoding (bit depth) and dithering."""
        _LOGGER.debug(f"Fetching session data for {uuid} to change options.")
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error(f"Could not fetch session data for device {uuid}")
            return False

        if "Options" not in session_data:
            session_data["Options"] = {}

        if encoding is not None:
            session_data["Options"]["DefaultEncoding"] = encoding
            _LOGGER.info(f"Setting DefaultEncoding to '{encoding}' for {uuid}.")
        if dithering is not None:
            session_data["Options"]["DefaultDithering"] = dithering
            _LOGGER.info(f"Setting DefaultDithering to '{dithering}' for {uuid}.")
            
        endpoint = f"/api/session/{uuid}"
        response = await self._request("put", endpoint, json=session_data)
        if response is not None:
            _LOGGER.info(f"Session options for {uuid} updated successfully.")
            return True
        _LOGGER.error(f"Failed to change session options for {uuid} via API")
        return False

    async def async_set_device_option(self, uuid: str, option_key: str, value: Any) -> bool:
        """Sets a generic device option by sending the full device object."""
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if not device_data:
            _LOGGER.error(f"Could not fetch device data for {uuid} to update option.")
            return False

        if "Options" not in device_data:
            device_data["Options"] = {}
        device_data["Options"][option_key] = value
        payload = device_data

        response = await self._request("put", API_DEVICE_DETAIL.format(uuid=uuid), json=payload)
        if response is not None:
            _LOGGER.info(f"Option '{option_key}' for {uuid} was successfully changed to '{value}'.")
            return True
        _LOGGER.error(f"API error while changing option '{option_key}' for {uuid}.")
        return False

    async def async_set_device_name(self, uuid: str, name: str) -> bool:
        """Sets a new name for the device."""
        return await self.async_set_device_option(uuid, "Name", name)

    async def async_get_device_screenshot(self, uuid: str) -> bytes | None:
        """Fetches the device screenshot as binary data."""
        endpoint = f"/api/live/device/{uuid}/image.png"
        return await self._request("get", endpoint)