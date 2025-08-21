# custom_components/visionect_joan/api.py
import logging
import ipaddress
import functools
import asyncio
import json
from typing import Optional, Dict, List

import requests
from requests.auth import HTTPBasicAuth

from .const import (
    IP_UNKNOWN, BATTERY_VOLTAGE_DIVIDER, API_PING, API_DEVICES,
    API_DEVICE_DETAIL, API_REBOOT, API_RESTART_SESSION, API_REFRESH, API_CLEAR,
    API_SESSION
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

    async def async_get_all_sessions(self) -> Optional[List[Dict]]:
        """Pobiera wszystkie sesje."""
        return await self._request("get", API_SESSION)

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

    async def async_set_device_url_clean_server(self, uuid: str, url: str) -> bool:
        """
        Ustawia URL urządzenia na CZYSTYM serwerze Visionect.
        Naśladuje dokładnie to co robi manual w przeglądarce po resecie.
        """
        _LOGGER.info(f"🧹 USTAWIENIE URL NA CZYSTYM SERWERZE dla {uuid}")
        _LOGGER.info(f"URL: {url}")
        
        try:
            # KROK 1: Pobierz wszystkie sesje (clean server approach)
            _LOGGER.debug("Pobieranie wszystkich sesji...")
            all_sessions = await self.async_get_all_sessions()
            if not all_sessions or not isinstance(all_sessions, list):
                _LOGGER.error("Nie można pobrać listy sesji")
                return False
            
            _LOGGER.debug(f"Znaleziono {len(all_sessions)} sesji")
            
            # KROK 2: Znajdź sesję dla naszego urządzenia
            target_session = None
            target_index = -1
            for i, session in enumerate(all_sessions):
                if session.get("Uuid") == uuid:
                    target_session = session.copy()  # Skopiuj całą sesję
                    target_index = i
                    break
            
            if not target_session:
                _LOGGER.error(f"Nie znaleziono sesji dla urządzenia {uuid}")
                return False
            
            _LOGGER.debug(f"Znaleziono sesję dla {uuid} na pozycji {target_index}")
            
            # KROK 3: Przygotuj zmianę - TYLKO URL (clean server style)
            original_url = target_session.get("Backend", {}).get("Fields", {}).get("url", "")
            _LOGGER.debug(f"Oryginalny URL: {original_url}")
            
            # Upewnij się że struktura backend istnieje (jak robi clean server)
            if "Backend" not in target_session:
                target_session["Backend"] = {"Name": "HTML", "Fields": {}}
            if "Fields" not in target_session["Backend"]:
                target_session["Backend"]["Fields"] = {}
            
            # NA CZYSTYM SERWERZE: zmień TYLKO URL, pozostaw resztę jak jest
            target_session["Backend"]["Fields"]["url"] = url
            
            # NIE ZMIENIAJ INNYCH USTAWIEŃ! Clean server prawdopodobnie ma prawidłową konfigurację
            _LOGGER.debug("Zmieniam tylko URL, pozostawiam inne ustawienia niezmienione")
            
            # KROK 4: Zaktualizuj sesję w tablicy
            all_sessions[target_index] = target_session
            
            # KROK 5: Wyślij PUT request (dokładnie jak robi web interface)
            _LOGGER.debug("Wysyłanie PUT request na /api/session...")
            
            def _put_sessions():
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                
                url_endpoint = f"{self.base_url}/api/session"
                response = self.session.put(
                    url_endpoint, 
                    json=all_sessions,
                    headers=headers,
                    timeout=30
                )
                return response
            
            response = await self.hass.async_add_executor_job(_put_sessions)
            
            if response.status_code in [200, 204]:
                _LOGGER.info(f"✅ SUKCES: URL zmieniony na czystym serwerze")
                _LOGGER.debug(f"Response status: {response.status_code}")
                
                # KROK 6: Opcjonalna weryfikacja
                await asyncio.sleep(1)
                updated_session = await self.async_get_session_data(uuid)
                if updated_session:
                    saved_url = updated_session.get("Backend", {}).get("Fields", {}).get("url", "")
                    if saved_url == url:
                        _LOGGER.info(f"✅ Weryfikacja: URL poprawnie zapisany")
                    else:
                        _LOGGER.warning(f"⚠️ Weryfikacja: URL może być niepoprawny")
                        _LOGGER.warning(f"   Oczekiwano: {url}")
                        _LOGGER.warning(f"   Otrzymano: {saved_url}")
                
                return True
            else:
                _LOGGER.error(f"❌ Błąd PUT /api/session: {response.status_code}")
                try:
                    _LOGGER.error(f"Response text: {response.text}")
                except:
                    pass
                return False
                
        except Exception as e:
            _LOGGER.error(f"❌ WYJĄTEK podczas ustawiania URL na czystym serwerze: {e}")
            import traceback
            _LOGGER.error(f"Stack trace: {traceback.format_exc()}")
            return False

    # Główne metody - używają nowej implementacji dla czystego serwera
    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        """Główna metoda ustawiania URL - dla czystego serwera."""
        return await self.async_set_device_url_clean_server(uuid, url)

    async def async_set_device_url_enhanced(self, uuid: str, url: str) -> bool:
        """Alias dla kompatybilności."""
        return await self.async_set_device_url_clean_server(uuid, url)

    async def async_set_device_url_like_web_interface(self, uuid: str, url: str) -> bool:
        """Alias dla kompatybilności."""
        return await self.async_set_device_url_clean_server(uuid, url)