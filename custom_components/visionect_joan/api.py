# custom_components/visionect_joan/api.py
import logging
import ipaddress
import functools
from typing import Optional, Dict, List

import requests
from requests.auth import HTTPBasicAuth

from .const import (
    IP_UNKNOWN, BATTERY_VOLTAGE_DIVIDER, API_PING, API_DEVICES,
    API_DEVICE_DETAIL, API_REBOOT, API_RESTART_SESSION, API_REFRESH, API_CLEAR,
    API_SESSION, DISPLAY_ROTATIONS
)

_LOGGER = logging.getLogger(__name__)

class VisionectAPI:
    """Klasa do komunikacji z API Visionect przy użyciu requests."""

    def __init__(self, hass, api_url: str, username: str = None, password: str = None,
                 api_key: str = None, api_secret: str = None):
        """Inicjalizacja API."""
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
        """Wykonywanie synchronicznego żądania HTTP."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            if response.content and 'application/json' in response.headers.get('Content-Type', ''):
                return response.json()
            return response.text
        except requests.RequestException as e:
            if not silent:
                _LOGGER.error(f"Błąd komunikacji z API {url}: {e}")
            return None

    async def _request(self, method, endpoint, silent=False, **kwargs):
        """Asynchroniczny wrapper dla _execute_request."""
        func = functools.partial(self._execute_request, method, endpoint, silent=silent, **kwargs)
        return await self.hass.async_add_executor_job(func)

    async def async_test_authentication(self) -> bool:
        """Testuje autentykację, próbując różnych metod."""
        if self.api_key and self.api_secret:
            _LOGGER.debug("Testowanie autentykacji za pomocą kluczy API...")
            self.session.auth = HTTPBasicAuth(self.api_key, self.api_secret)
            if await self._request("get", API_PING, silent=True) is not None:
                self.authenticated_by = "api_key"
                _LOGGER.info("Autentykacja kluczami API pomyślna.")
                return True
            self.session.auth = None

        if self.username and self.password:
            _LOGGER.debug("Testowanie autentykacji za pomocą nazwy użytkownika i hasła...")
            login_url = f"{self.base_url}/login"
            data = {'username': self.username, 'password': self.password}
            try:
                def _login():
                    response = self.session.post(login_url, data=data, allow_redirects=False, timeout=10)
                    return response.status_code in [200, 302]

                if await self.hass.async_add_executor_job(_login):
                    self.authenticated_by = "credentials"
                    _LOGGER.info("Autentykacja danymi logowania pomyślna.")
                    return True
                else:
                    _LOGGER.error("Błąd logowania, serwer nie zaakceptował danych logowania.")
            except Exception as e:
                _LOGGER.error(f"Błąd komunikacji podczas logowania: {e}")

        _LOGGER.error("Autentykacja nie powiodła się żadną z dostępnych metod.")
        return False

    async def async_get_device_data(self, uuid: str) -> Optional[Dict]:
        """Pobiera szczegółowe dane urządzenia i scala je z danymi sesji."""
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
        """Pobiera dane sesji urządzenia."""
        sessions = await self._request("get", API_SESSION)
        if sessions and isinstance(sessions, list):
            return next((s for s in sessions if s.get("Uuid") == uuid), None)
        return None

    async def async_get_all_devices(self) -> Optional[List[Dict]]:
        return await self._request("get", API_DEVICES)

    async def _post_command(self, endpoint_template: str, uuid: str, command_name: str) -> bool:
        response = await self._request("post", endpoint_template.format(uuid=uuid))
        if response is not None:
            _LOGGER.info(f"Komenda '{command_name}' dla {uuid} wykonana pomyślnie.")
            return True
        return False

    async def async_reboot_device(self, uuid: str) -> bool:
        return await self._post_command(API_REBOOT, uuid, "Restart urządzenia")

    async def async_restart_session(self, uuid: str) -> bool:
        return await self._post_command(API_RESTART_SESSION, uuid, "Restart sesji")

    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        """Ustawia URL urządzenia przez API (metoda PUT na pojedynczej sesji)."""
        _LOGGER.debug(f"Pobieranie danych sesji dla {uuid} w celu zmiany URL.")
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error(f"Nie można pobrać danych sesji dla urządzenia {uuid}")
            return False

        if "Backend" not in session_data: session_data["Backend"] = {}
        if "Fields" not in session_data["Backend"]: session_data["Backend"]["Fields"] = {}
        session_data["Backend"]["Fields"]["url"] = url

        endpoint = f"/api/session/{uuid}"
        response = await self._request("put", endpoint, json=session_data)
        if response is not None:
            _LOGGER.info(f"URL urządzenia {uuid} zmieniony na: {url}")
            return True
        _LOGGER.error(f"Nie udało się zmienić URL urządzenia {uuid} przez API")
        return False

    async def async_set_display_rotation(self, uuid: str, display_rotation: str) -> bool:
        """Ustawia rotację ekranu urządzenia przez API (metoda PUT na całej liście urządzeń)."""
        all_devices = await self.async_get_all_devices()
        if not all_devices:
            _LOGGER.error("Nie można pobrać listy urządzeń do aktualizacji rotacji.")
            return False

        target_index = -1
        for i, device in enumerate(all_devices):
            if device.get("Uuid") == uuid:
                target_index = i
                break

        if target_index == -1:
            _LOGGER.error(f"Nie znaleziono urządzenia {uuid} na liście do aktualizacji.")
            return False

        target_device = all_devices[target_index]
        if "Displays" not in target_device or not target_device.get("Displays"):
            _LOGGER.error(f"Urządzenie {uuid} nie ma struktury 'Displays' w danych API.")
            return False

        target_device["Displays"][0]["Rotation"] = int(display_rotation)
        all_devices[target_index] = target_device

        response = await self._request("put", API_DEVICES, json=all_devices)
        if response is not None:
            _LOGGER.info(f"Rotacja ekranu dla {uuid} ustawiona na {display_rotation}.")
            return True
        _LOGGER.error(f"Błąd API przy zmianie rotacji dla {uuid}.")
        return False