# custom_components/visionect_joan/api.py
import logging
import ipaddress
import functools
from typing import Optional, Dict, List

import requests
from requests.auth import HTTPBasicAuth

from .const import (
    IP_UNKNOWN, BATTERY_VOLTAGE_DIVIDER, API_PING, API_DEVICES,
    API_DEVICE_DETAIL, API_RESTART_SESSION,
    MIN_REFRESH_INTERVAL, MAX_REFRESH_INTERVAL
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
        data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if data and isinstance(data, dict):
            if "Status" not in data: data["Status"] = {}
            if "Config" not in data: data["Config"] = {}
            ip = data["Status"].get("IPAddress", "").strip()
            if not ip or ip.lower() in ["unknown", "none", ""]:
                data["Status"]["IPAddress"] = IP_UNKNOWN
            else:
                try: ipaddress.ip_address(ip)
                except ValueError: data["Status"]["IPAddress"] = IP_UNKNOWN
            if "BatteryVoltage" in data["Status"]:
                try: data["Status"]["BatteryVoltage"] = float(data["Status"]["BatteryVoltage"]) / BATTERY_VOLTAGE_DIVIDER
                except (ValueError, TypeError): data["Status"]["BatteryVoltage"] = None
        return data

    async def async_get_all_devices(self) -> Optional[List[Dict]]:
        return await self._request("get", API_DEVICES)

    async def _post_command(self, endpoint_template: str, uuid: str, command_name: str) -> bool:
        response = await self._request("post", endpoint_template.format(uuid=uuid))
        if response is not None:
            _LOGGER.info(f"Komenda '{command_name}' dla {uuid} wykonana pomyślnie.")
            return True
        return False

    async def async_restart_session(self, uuid: str) -> bool:
        return await self._post_command(API_RESTART_SESSION, uuid, "Restart sesji")

    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        """Ustawia URL urządzenia z dodatkowymi parametrami dla e-ink."""
        endpoint = API_DEVICE_DETAIL.format(uuid=uuid)
        current_config = await self._request("get", endpoint)
        if not current_config:
            _LOGGER.error(f"Nie można pobrać konfiguracji dla urządzenia {uuid}")
            return False
        
        if "Config" not in current_config:
            current_config["Config"] = {}
        
        current_config["Config"]["Url"] = url
        current_config["Config"]["UseServerSideRendering"] = True
        current_config["Config"]["AutoReload"] = True
        current_config["Config"]["AutoReloadInterval"] = 300
        
        if "DisplaySettings" not in current_config["Config"]:
            current_config["Config"]["DisplaySettings"] = {}
        
        current_config["Config"]["DisplaySettings"]["Dithering"] = True
        current_config["Config"]["DisplaySettings"]["Contrast"] = 1.0
        
        response = await self._request("put", endpoint, json=current_config)
        if response is not None:
            _LOGGER.info(f"URL urządzenia {uuid} zmieniony na: {url}")
            return True
        else:
            _LOGGER.error(f"Nie udało się zmienić URL urządzenia {uuid}")
            return False

    async def async_set_device_config(self, uuid: str, config_updates: dict) -> bool:
        """Ustawia dowolne parametry konfiguracji urządzenia."""
        endpoint = API_DEVICE_DETAIL.format(uuid=uuid)
        current_config = await self._request("get", endpoint)
        if not current_config:
            return False
        
        if "Config" not in current_config:
            current_config["Config"] = {}
        
        current_config["Config"].update(config_updates)
        
        response = await self._request("put", endpoint, json=current_config)
        return response is not None

    async def async_set_device_orientation(self, uuid: str, orientation: str) -> bool:
        """Ustawia orientację ekranu urządzenia."""
        valid_orientations = ["portrait", "landscape", "portrait_flipped", "landscape_flipped"]
        if orientation not in valid_orientations:
            _LOGGER.error(f"Nieprawidłowa orientacja: {orientation}")
            return False
        
        config_updates = {"Orientation": orientation}
        return await self.async_set_device_config(uuid, config_updates)

    async def async_set_refresh_interval(self, uuid: str, interval: int) -> bool:
        """Ustawia interwał odświeżania urządzenia."""
        if interval < MIN_REFRESH_INTERVAL or interval > MAX_REFRESH_INTERVAL:
            _LOGGER.error(f"Nieprawidłowy interwał odświeżania: {interval}")
            return False
        
        config_updates = {"RefreshInterval": interval}
        return await self.async_set_device_config(uuid, config_updates)