import logging
import ipaddress
import functools
import time
from typing import Optional, Dict, List

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, RequestException, Timeout

from .const import (
    IP_UNKNOWN, BATTERY_VOLTAGE_DIVIDER, API_PING, API_DEVICES,
    API_DEVICE_DETAIL, API_REBOOT, API_RESTART_SESSION,
    API_SESSION, DISPLAY_ROTATIONS, SUPPORTED_IMAGE_FORMATS,
    MAX_RETRY_ATTEMPTS, NETWORK_RETRY_DELAY
)

_LOGGER = logging.getLogger(__name__)

class VisionectAPI:
    """Class for communicating with the Visionect API using requests."""

    def __init__(self, hass, api_url: str, username: str = None, password: str = None,
                 api_key: str = None, api_secret: str = None):
        """Initialize the API."""
        self.hass = hass
        self.session = requests.Session()

        url = api_url.strip()
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        self.base_url = url.rstrip('/')

        self.username = username
        self.password = password
        self.api_key = api_key
        self.api_secret = api_secret
        self.authenticated_by = None

    def _execute_request(self, method, endpoint, silent=False, **kwargs):
        """Executes a synchronous HTTP request with improved error handling and short backoff."""
        url = f"{self.base_url}{endpoint}"
        retry_count = 0
        backoff = min(max(int(NETWORK_RETRY_DELAY), 1), 3)  # use 1-3s, not 60s
        
        while retry_count < MAX_RETRY_ATTEMPTS:
            try:
                response = self.session.request(method, url, timeout=15, **kwargs)
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return response.json()
                if 'image/' in content_type:
                    return response.content
                return response.text
            except ConnectionError as e:
                retry_count += 1
                if not silent:
                    _LOGGER.warning(f"Connection error to {url} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    if not silent:
                        _LOGGER.error(f"Failed to connect to {url} after {MAX_RETRY_ATTEMPTS} attempts")
                    return None
                time.sleep(backoff)
            except Timeout as e:
                retry_count += 1
                if not silent:
                    _LOGGER.warning(f"Timeout error to {url} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    if not silent:
                        _LOGGER.error(f"Timeout connecting to {url} after {MAX_RETRY_ATTEMPTS} attempts")
                    return None
                time.sleep(backoff)
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
        url_lower = url.lower()
        return any(url_lower.endswith(f'.{fmt}') for fmt in SUPPORTED_IMAGE_FORMATS)

    async def async_test_authentication(self) -> bool:
        """Tests authentication by trying different methods."""
        if self.api_key and self.api_secret:
            _LOGGER.debug("Testing authentication with API keys...")
            self.session.auth = HTTPBasicAuth(self.api_key, self.api_secret)
            if await self._request("get", API_PING, silent=True) is not None:
                self.authenticated_by = "api_key"
                _LOGGER.info("API key authentication successful.")
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

        if session_data and "Backend" in session_data and "Fields" in session_data["Backend"]:
            device_data["Config"]["Url"] = session_data["Backend"]["Fields"].get("url", "")
            device_data["Config"]["ReloadTimeout"] = session_data["Backend"]["Fields"].get("ReloadTimeout", "0")

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
        """Fetches device session data."""
        sessions = await self._request("get", API_SESSION)
        if sessions and isinstance(sessions, list):
            return next((s for s in sessions if s.get("Uuid") == uuid), None)
        return None

    async def async_get_all_devices(self) -> Optional[List[Dict]]:
        return await self._request("get", API_DEVICES)

    async def _post_command(self, endpoint_template: str, uuid: str, command_name: str) -> bool:
        response = await self._request("post", endpoint_template.format(uuid=uuid))
        if response is not None:
            _LOGGER.info(f"Command '{command_name}' for {uuid} executed successfully.")
            return True
        return False

    async def async_reboot_device(self, uuid: str) -> bool:
        return await self._post_command(API_REBOOT, uuid, "Reboot device")

    async def async_restart_session(self, uuid: str) -> bool:
        return await self._post_command(API_RESTART_SESSION, uuid, "Restart session")

    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        """Sets the device URL via the API, forcing a constant session type and long lifetime."""
        _LOGGER.debug(f"Fetching session data for {uuid} to change URL.")
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error(f"Could not fetch session data for device {uuid}")
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        
        session_data["Backend"]["Type"] = "Web"
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
        """Sets the device's screen rotation via the API (PUT method on the entire device list)."""
        all_devices = await self.async_get_all_devices()
        if not all_devices:
            _LOGGER.error("Could not fetch device list to update rotation.")
            return False

        target_index = -1
        for i, device in enumerate(all_devices):
            if device.get("Uuid") == uuid:
                target_index = i
                break

        if target_index == -1:
            _LOGGER.error(f"Device {uuid} not found in the list to update.")
            return False

        target_device = all_devices[target_index]
        if "Displays" not in target_device or not target_device.get("Displays"):
            _LOGGER.error(f"Device {uuid} does not have a 'Displays' structure in API data.")
            return False

        target_device["Displays"][0]["Rotation"] = int(display_rotation)
        all_devices[target_index] = target_device

        response = await self._request("put", API_DEVICES, json=all_devices)
        if response is not None:
            _LOGGER.info(f"Screen rotation for {uuid} set to {display_rotation}.")
            return True
        _LOGGER.error(f"API error while changing rotation for {uuid}.")
        return False

    async def async_set_reload_timeout(self, uuid: str, timeout_seconds: str) -> bool:
        """Sets the refresh interval (ReloadTimeout) for the device session according to Visionect documentation."""
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

    async def async_set_device_name(self, uuid: str, name: str) -> bool:
        """Sets a new name for the device."""
        all_devices = await self.async_get_all_devices()
        if not all_devices:
            _LOGGER.error("Could not fetch device list to update the name.")
            return False

        target_device = next((d for d in all_devices if d.get("Uuid") == uuid), None)

        if not target_device:
            _LOGGER.error(f"Device {uuid} not found in the list to update.")
            return False

        if "Options" not in target_device:
            target_device["Options"] = {}
        target_device["Options"]["Name"] = name

        response = await self._request("put", API_DEVICES, json=all_devices)
        if response is not None:
            _LOGGER.info(f"Name for {uuid} was successfully changed to '{name}'.")
            return True
        _LOGGER.error(f"API error while changing name for {uuid}.")
        return False

    # <-- ADDED NEW FUNCTION -->
    async def async_get_device_screenshot(self, uuid: str) -> bytes | None:
        """Fetches the device screenshot as binary data."""
        endpoint = f"/api/live/device/{uuid}/image.png"
        return await self._request("get", endpoint)