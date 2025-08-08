# custom_components/visionect_joan/api.py
import logging
import ipaddress
import functools
from typing import Optional, Dict, List
import json

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
        
        # Web controller zostanie zainicjalizowany przy pierwszym użyciu
        self._web_controller = None

    @property
    def web_controller(self):
        """Lazy initialization of web controller to avoid circular import."""
        if self._web_controller is None:
            from .web_controller import VisionectWebController
            self._web_controller = VisionectWebController(self.hass, self.base_url, self.username, self.password)
        return self._web_controller

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
        # Pobierz podstawowe dane urządzenia
        device_data = await self._request("get", API_DEVICE_DETAIL.format(uuid=uuid))
        if not device_data or not isinstance(device_data, dict):
            return None
            
        # Pobierz dane sesji (zawierające URL)
        session_data = await self.async_get_session_data(uuid)
        
        # Scala dane
        if session_data:
            if "Config" not in device_data:
                device_data["Config"] = {}
            if "Backend" in session_data and "Fields" in session_data["Backend"]:
                device_data["Config"]["Url"] = session_data["Backend"]["Fields"].get("url", "")
                device_data["Config"]["ReloadTimeout"] = session_data["Backend"]["Fields"].get("ReloadTimeout", "0")
        
        # Dodaj informację o rotacji z Displays
        if "Displays" in device_data and len(device_data["Displays"]) > 0:
            rotation = device_data["Displays"][0].get("Rotation", 0)
            if "Config" not in device_data:
                device_data["Config"] = {}
            device_data["Config"]["DisplayRotation"] = rotation
        
        # Standardowe przetwarzanie danych
        if "Status" not in device_data:
            device_data["Status"] = {}
        if "Config" not in device_data:
            device_data["Config"] = {}
            
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
            for session in sessions:
                if session.get("Uuid") == uuid:
                    return session
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

    async def async_force_refresh(self, uuid: str) -> bool:
        return await self._post_command(API_REFRESH, uuid, "Wymuszenie odświeżenia")

    async def async_clear_screen(self, uuid: str) -> bool:
        return await self._post_command(API_CLEAR, uuid, "Czyszczenie ekranu")

    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        """Ustawia URL urządzenia przez API."""
        _LOGGER.info(f"Ustawianie URL dla {uuid}: {url}")
        
        # Pobierz aktualne dane sesji
        session_data = await self.async_get_session_data(uuid)
        if not session_data:
            _LOGGER.error(f"Nie można pobrać danych sesji dla urządzenia {uuid}")
            return False
            
        # Zaktualizuj URL w danych sesji
        if "Backend" not in session_data:
            session_data["Backend"] = {"Name": "HTML", "Fields": {}}
        if "Fields" not in session_data["Backend"]:
            session_data["Backend"]["Fields"] = {}
            
        session_data["Backend"]["Fields"]["url"] = url
        
        # Wyślij zaktualizowane dane
        endpoint = f"/api/session/{uuid}"
        response = await self._request("put", endpoint, json=session_data)
        if response is not None:
            _LOGGER.info(f"URL urządzenia {uuid} zmieniony przez API na: {url}")
            return True
        else:
            _LOGGER.error(f"Nie udało się zmienić URL urządzenia {uuid} przez API")
            return False

    async def async_set_display_rotation(self, uuid: str, display_rotation: str) -> bool:
        """Ustawia rotację ekranu urządzenia Joan przez API."""
        _LOGGER.info(f"Ustawianie rotacji ekranu dla {uuid}: {display_rotation} ({DISPLAY_ROTATIONS.get(display_rotation, 'Nieznana')})")
        
        try:
            # Pobierz wszystkie urządzenia (API oczekuje tablicy)
            all_devices = await self._request("get", API_DEVICES)
            if not all_devices or not isinstance(all_devices, list):
                _LOGGER.error("Nie można pobrać listy wszystkich urządzeń")
                return False
            
            # Znajdź docelowe urządzenie w liście
            target_device = None
            target_index = -1
            for i, device in enumerate(all_devices):
                if device.get("Uuid") == uuid:
                    target_device = device.copy()  # Skopiuj dane urządzenia
                    target_index = i
                    break
            
            if not target_device:
                _LOGGER.error(f"Nie znaleziono urządzenia {uuid} w liście urządzeń")
                return False
            
            # Sprawdź czy urządzenie ma sekcję Displays
            if "Displays" not in target_device or not target_device["Displays"]:
                _LOGGER.error(f"Urządzenie {uuid} nie ma sekcji Displays")
                return False
            
            # Zaktualizuj rotację w pierwszym (głównym) displayu
            old_rotation = target_device["Displays"][0].get("Rotation", 0)
            target_device["Displays"][0]["Rotation"] = int(display_rotation)
            
            _LOGGER.info(f"Zmiana rotacji z {old_rotation} na {display_rotation} dla urządzenia {uuid}")
            
            # Zaktualizuj urządzenie w liście wszystkich urządzeń
            all_devices[target_index] = target_device
            
            _LOGGER.debug(f"Wysyłanie tablicy {len(all_devices)} urządzeń do API")
            
            # Wyślij całą zaktualizowaną tablicę urządzeń przez API
            def _put_devices_data():
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                
                url = f"{self.base_url}/api/device/"
                response = self.session.put(
                    url, 
                    json=all_devices,  # Wyślij całą tablicę urządzeń
                    headers=headers,
                    timeout=30
                )
                return response
            
            response = await self.hass.async_add_executor_job(_put_devices_data)
            
            if response.status_code in [200, 204]:
                _LOGGER.info(f"Rotacja ekranu urządzenia {uuid} zmieniona na: {DISPLAY_ROTATIONS.get(display_rotation, display_rotation)} przez API")
                return True
            else:
                _LOGGER.error(f"Błąd API przy zmianie rotacji: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Wyjątek podczas zmiany rotacji przez API: {e}")
            return False