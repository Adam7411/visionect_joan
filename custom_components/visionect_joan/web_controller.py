# custom_components/visionect_joan/web_controller.py
import logging
import asyncio
import functools
from typing import Optional
import aiohttp
import json

_LOGGER = logging.getLogger(__name__)

from .const import DISPLAY_ROTATIONS

class VisionectWebController:
    """Klasa do kontrolowania interfejsu webowego Visionect przez HTTP API."""

    def __init__(self, hass, base_url: str, username: str = None, password: str = None):
        """Inicjalizacja kontrolera web."""
        self.hass = hass
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self._session = None
        self._authenticated = False

    async def _get_session(self):
        """Pobiera lub tworzy session HTTP."""
        if self._session is None or self._session.closed:
            # Konfiguruj autoryzację jeśli mamy dane logowania
            auth = None
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; VisionectJoanController/1.0)',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en,de;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
                
            connector = aiohttp.TCPConnector(
                verify_ssl=False,
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30
            )
            
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60, connect=30),
                connector=connector,
                auth=auth,
                headers=headers,
                cookie_jar=aiohttp.CookieJar()
            )
            self._authenticated = False
            
        return self._session

    async def _cleanup_session(self):
        """Zamyka session HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._authenticated = False

    async def _authenticate(self, session):
        """Uwierzytelnia sesję."""
        if self._authenticated:
            return True
            
        if not (self.username and self.password):
            _LOGGER.debug("Brak danych logowania - sprawdzam dostęp bez autoryzacji")
            return True
        
        try:
            # Próba logowania formularzem
            login_url = f"{self.base_url}/login"
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            async with session.post(login_url, data=login_data, allow_redirects=True) as response:
                if response.status in [200, 302]:
                    # Sprawdź czy mamy ciasteczka autoryzacyjne
                    cookies = session.cookie_jar.filter_cookies(self.base_url)
                    if cookies:
                        _LOGGER.debug("Logowanie pomyślne - otrzymano ciasteczka")
                        self._authenticated = True
                        return True
                    else:
                        _LOGGER.warning("Logowanie bez ciasteczek")
                        return True
                else:
                    _LOGGER.error(f"Błąd logowania: {response.status}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"Błąd podczas uwierzytelniania: {e}")
            return False

    async def set_display_rotation_via_http(self, uuid: str, display_rotation: str) -> bool:
        """Ustawia rotację ekranu przez bezpośrednie API HTTP."""
        session = await self._get_session()
        
        try:
            # Uwierzytelnij sesję
            if not await self._authenticate(session):
                _LOGGER.error("Nie udało się uwierzytelnić sesji HTTP")
                return False
            
            # Pobierz wszystkie urządzenia (API oczekuje tablicy)
            devices_url = f"{self.base_url}/api/device/"
            _LOGGER.debug(f"Pobieranie wszystkich urządzeń: {devices_url}")
            
            async with session.get(devices_url) as response:
                if response.status != 200:
                    _LOGGER.error(f"Nie można pobrać listy urządzeń: {response.status}")
                    return False
                
                all_devices = await response.json()
                
            if not isinstance(all_devices, list):
                _LOGGER.error("API nie zwróciło tablicy urządzeń")
                return False
                
            _LOGGER.debug(f"Pobrano {len(all_devices)} urządzeń")
            
            # Znajdź docelowe urządzenie w liście
            target_device = None
            target_index = -1
            for i, device in enumerate(all_devices):
                if device.get("Uuid") == uuid:
                    target_device = device
                    target_index = i
                    break
            
            if not target_device:
                _LOGGER.error(f"Nie znaleziono urządzenia {uuid} w liście urządzeń")
                return False
            
            # Sprawdź czy urządzenie ma sekcję Displays
            if "Displays" not in target_device or not target_device["Displays"]:
                _LOGGER.error(f"Urządzenie {uuid} nie ma sekcji Displays")
                return False
            
            # Zaktualizuj rotację w pierwszym displayu
            old_rotation = target_device["Displays"][0].get("Rotation", 0)
            target_device["Displays"][0]["Rotation"] = int(display_rotation)
            
            _LOGGER.info(f"Zmiana rotacji z {old_rotation} na {display_rotation} dla urządzenia {uuid}")
            
            # Zaktualizuj urządzenie w liście
            all_devices[target_index] = target_device
            
            # Wyślij zaktualizowaną tablicę przez API
            put_url = f"{self.base_url}/api/device/"
            headers = {
                'Content-Type': 'application/json'
            }
            
            async with session.put(put_url, json=all_devices, headers=headers) as response:
                if response.status in [200, 204]:
                    _LOGGER.info(f"Rotacja ekranu urządzenia {uuid} zmieniona na: {DISPLAY_ROTATIONS.get(display_rotation, display_rotation)} przez HTTP API")
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"Błąd API przy zmianie rotacji: {response.status}")
                    _LOGGER.debug(f"Odpowiedź: {response_text}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"Błąd podczas ustawiania rotacji przez HTTP API: {e}")
            return False
        finally:
            await self._cleanup_session()

    async def set_display_rotation_via_web(self, uuid: str, display_rotation: str) -> bool:
        """Ustawia rotację ekranu urządzenia - używa bezpośrednio API HTTP."""
        _LOGGER.info(f"Próba ustawienia rotacji ekranu {uuid} na {DISPLAY_ROTATIONS.get(display_rotation, display_rotation)}")
        
        return await self.set_display_rotation_via_http(uuid, display_rotation)

    async def set_device_url_via_web(self, uuid: str, url: str) -> bool:
        """Ustawia URL urządzenia przez API HTTP."""
        session = await self._get_session()
        
        try:
            # Uwierzytelnij sesję
            if not await self._authenticate(session):
                _LOGGER.error("Nie udało się uwierzytelnić sesji HTTP")
                return False
            
            # Pobierz aktualne dane sesji
            session_url = f"{self.base_url}/api/session/{uuid}"
            _LOGGER.debug(f"Pobieranie danych sesji: {session_url}")
            
            async with session.get(session_url) as response:
                if response.status != 200:
                    _LOGGER.error(f"Nie można pobrać danych sesji: {response.status}")
                    return False
                
                session_data = await response.json()
                
            # Zaktualizuj URL w danych sesji
            if "Backend" not in session_data:
                session_data["Backend"] = {"Name": "HTML", "Fields": {}}
            if "Fields" not in session_data["Backend"]:
                session_data["Backend"]["Fields"] = {}
                
            session_data["Backend"]["Fields"]["url"] = url
            
            # Wyślij zaktualizowane dane sesji
            put_url = f"{self.base_url}/api/session/{uuid}"
            headers = {
                'Content-Type': 'application/json'
            }
            
            async with session.put(put_url, json=session_data, headers=headers) as response:
                if response.status in [200, 204]:
                    _LOGGER.info(f"URL urządzenia {uuid} zmieniony na: {url} przez HTTP API")
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.error(f"Błąd API przy zmianie URL: {response.status}")
                    _LOGGER.debug(f"Odpowiedź: {response_text}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"Błąd podczas ustawiania URL przez HTTP API: {e}")
            return False
        finally:
            await self._cleanup_session()

    async def test_web_connection(self, uuid: str = None) -> bool:
        """Testuje połączenie z API."""
        session = await self._get_session()
        
        try:
            # Uwierzytelnij sesję
            if not await self._authenticate(session):
                _LOGGER.error("Nie udało się uwierzytelnić dla testu połączenia")
                return False
            
            # Testuj endpoint API
            if uuid:
                test_url = f"{self.base_url}/api/device/{uuid}"
            else:
                test_url = f"{self.base_url}/api/device/"
                
            async with session.get(test_url) as response:
                if response.status == 200:
                    _LOGGER.debug(f"Test połączenia API pomyślny: {test_url}")
                    return True
                else:
                    _LOGGER.error(f"Test połączenia API nieudany: {response.status}")
                    return False
                    
        except Exception as e:
            _LOGGER.error(f"Błąd podczas testowania połączenia API: {e}")
            return False
        finally:
            await self._cleanup_session()