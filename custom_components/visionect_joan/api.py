# custom_components/visionect_joan1/api.py
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Plik api.py jest wczytywany...")

try:
    import requests
    import ipaddress
    from typing import Optional, Dict, List
    from .const import (
        DOMAIN, IP_UNKNOWN, STATE_ONLINE, STATE_OFFLINE,
        MODEL_JOAN6, DEFAULT_REFRESH_INTERVAL, BATTERY_VOLTAGE_DIVIDER,
        API_PING, API_DEVICES, API_DEVICE_DETAIL, API_SESSION,
        API_REBOOT, API_RESTART_SESSION, API_REFRESH, API_CLEAR,
        API_LOGS, API_SCREENSHOT, API_STATISTICS, API_HISTORY, API_SERVER_INFO
    )
except ImportError as e:
    _LOGGER.critical(f"Krytyczny błąd importu w api.py: {e}")
    raise

_LOGGER.debug("Wszystkie importy w api.py zakończone pomyślnie.")

class VisionectAPI:
    """Klasa do komunikacji z API Visionect."""

    def __init__(self, hass, api_url: str, username: str = None, password: str = None,
                 api_key: str = None, api_secret: str = None):
        """Inicjalizacja API."""
        _LOGGER.debug("Inicjalizacja VisionectAPI...")
        self.hass = hass
        url = api_url.strip()
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        self.base_url = url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.authenticated_by = None
        _LOGGER.debug("Inicjalizacja VisionectAPI zakończona.")

    async def async_test_authentication(self) -> bool:
        """Test autentykacji."""
        if self.api_key and self.api_secret:
            self.session.auth = (self.api_key, self.api_secret)
            _LOGGER.debug("Próba autentykacji za pomocą kluczy API...")
            if await self.async_ping_server():
                self.authenticated_by = "api_key"
                _LOGGER.debug("Autentykacja kluczami API pomyślna.")
                return True
            self.session.auth = None

        if self.username and self.password:
            _LOGGER.debug("Próba autentykacji za pomocą nazwy użytkownika i hasła...")
            if await self.async_login():
                self.authenticated_by = "credentials"
                _LOGGER.debug("Autentykacja danymi logowania pomyślna.")
                return True
        
        _LOGGER.error("Autentykacja nie powiodła się żadną z metod.")
        return False

    async def async_ping_server(self) -> bool:
        def _ping():
            try:
                response = self.session.get(f"{self.base_url}{API_PING}", timeout=10)
                return response.status_code == 200
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd ping: {e}")
                return False
        return await self.hass.async_add_executor_job(_ping)

    async def async_login(self) -> bool:
        def _login():
            try:
                response = self.session.post(
                    f"{self.base_url}/login",
                    data={'username': self.username, 'password': self.password},
                    timeout=10,
                    allow_redirects=False
                )
                if response.status_code not in [200, 302]:
                    _LOGGER.error(f"Błąd logowania. Status: {response.status_code}, Odpowiedź: {response.text}")
                    return False
                return True
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd komunikacji podczas logowania: {e}")
                return False
        return await self.hass.async_add_executor_job(_login)

    async def _async_post_command(self, endpoint_template: str, uuid: str, command_name: str) -> bool:
        def _post():
            url = f"{self.base_url}{endpoint_template.format(uuid=uuid)}"
            try:
                response = self.session.post(url, timeout=10)
                if response.status_code == 200:
                    _LOGGER.info(f"Komenda '{command_name}' dla {uuid} wykonana pomyślnie.")
                    return True
                else:
                    _LOGGER.error(
                        f"Błąd podczas wykonywania komendy '{command_name}' dla {uuid}. "
                        f"Status: {response.status_code}, Odpowiedź: {response.text}"
                    )
                    return False
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd komunikacji podczas komendy '{command_name}' dla {uuid}: {e}")
                return False
        return await self.hass.async_add_executor_job(_post)

    async def async_get_all_devices(self) -> Optional[List[Dict]]:
        def _get_devices():
            try:
                response = self.session.get(f"{self.base_url}{API_DEVICES}", timeout=10)
                if response.status_code == 200:
                    return response.json()
                _LOGGER.error(f"Błąd pobierania urządzeń: {response.status_code}, {response.text}")
                return None
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd komunikacji podczas pobierania urządzeń: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_devices)

    async def async_get_device_data(self, uuid: str) -> Optional[Dict]:
        def _get_device():
            try:
                response = self.session.get(f"{self.base_url}{API_DEVICE_DETAIL.format(uuid=uuid)}", timeout=10)
                response.raise_for_status()
                data = response.json()
                if "Status" not in data: data["Status"] = {}
                if "Config" not in data: data["Config"] = {}
                ip = data["Status"].get("IPAddress", "").strip()
                if not ip or ip.lower() in ["unknown", "none", ""]: data["Status"]["IPAddress"] = IP_UNKNOWN
                else:
                    try: ipaddress.ip_address(ip)
                    except ValueError: data["Status"]["IPAddress"] = IP_UNKNOWN
                if "BatteryVoltage" in data["Status"]:
                    try: data["Status"]["BatteryVoltage"] = float(data["Status"]["BatteryVoltage"]) / BATTERY_VOLTAGE_DIVIDER
                    except (ValueError, TypeError): data["Status"]["BatteryVoltage"] = None
                return data
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania danych urządzenia {uuid}: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_device)

    async def async_set_device_url(self, uuid: str, url: str) -> bool:
        def _set_url():
            device_url = f"{self.base_url}{API_DEVICE_DETAIL.format(uuid=uuid)}"
            try:
                response_get = self.session.get(device_url, timeout=10)
                response_get.raise_for_status()
                current_config = response_get.json()
                if "Config" not in current_config or not isinstance(current_config.get("Config"), dict):
                    current_config["Config"] = {}
                current_config["Config"]["Url"] = url
                current_config["Config"]["UseServerSideRendering"] = True
                response_put = self.session.put(device_url, json=current_config, timeout=15)
                if response_put.status_code in [200, 201, 204]:
                    _LOGGER.info(f"Pomyślnie ustawiono URL '{url}' na urządzeniu {uuid}")
                    return True
                else:
                    _LOGGER.error(f"Błąd podczas ustawiania URL na {uuid}. Status: {response_put.status_code}, Odpowiedź: {response_put.text}")
                    return False
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd komunikacji podczas ustawiania URL na {uuid}: {e}")
                return False
        return await self.hass.async_add_executor_job(_set_url)

    async def async_get_session_data(self, uuid: str) -> Optional[Dict]:
        def _get_session():
            try:
                response = self.session.get(f"{self.base_url}{API_SESSION.format(uuid=uuid)}", timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania sesji {uuid}: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_session)

    async def async_reboot_device(self, uuid: str) -> bool:
        return await self._async_post_command(API_REBOOT, uuid, "Restart urządzenia")

    async def async_restart_session(self, uuid: str) -> bool:
        return await self._async_post_command(API_RESTART_SESSION, uuid, "Restart sesji")

    async def async_force_refresh(self, uuid: str) -> bool:
        return await self._async_post_command(API_REFRESH, uuid, "Wymuszenie odświeżenia")

    async def async_set_device_config(self, uuid: str, config_key: str, config_value: str) -> bool:
        """Ustawia określoną konfigurację urządzenia."""
        def _set_config():
            device_url = f"{self.base_url}{API_DEVICE_DETAIL.format(uuid=uuid)}"
            try:
                # Pobierz aktualną konfigurację
                response_get = self.session.get(device_url, timeout=10)
                response_get.raise_for_status()
                current_config = response_get.json()
                
                # Upewnij się, że Config istnieje
                if "Config" not in current_config or not isinstance(current_config.get("Config"), dict):
                    current_config["Config"] = {}
                
                # Ustaw nową wartość
                current_config["Config"][config_key] = config_value
                
                # Wyślij zaktualizowaną konfigurację
                response_put = self.session.put(device_url, json=current_config, timeout=15)
                if response_put.status_code in [200, 201, 204]:
                    _LOGGER.info(f"Pomyślnie ustawiono {config_key}='{config_value}' na urządzeniu {uuid}")
                    return True
                else:
                    _LOGGER.error(f"Błąd podczas ustawiania konfiguracji na {uuid}. Status: {response_put.status_code}")
                    return False
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd komunikacji podczas ustawiania konfiguracji na {uuid}: {e}")
                return False
        return await self.hass.async_add_executor_job(_set_config)

    async def async_clear_screen(self, uuid: str) -> bool:
        """Czyści ekran urządzenia."""
        return await self._async_post_command(API_CLEAR, uuid, "Czyszczenie ekranu")

    async def async_get_device_logs(self, uuid: str, lines: int = 100) -> Optional[List[str]]:
        """Pobiera logi urządzenia."""
        def _get_logs():
            url = f"{self.base_url}{API_LOGS.format(uuid=uuid)}?lines={lines}"
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                logs_data = response.json()
                return logs_data.get("logs", [])
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania logów urządzenia {uuid}: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_logs)

    async def async_get_device_screenshot(self, uuid: str) -> Optional[bytes]:
        """Pobiera zrzut ekranu urządzenia."""
        def _get_screenshot():
            url = f"{self.base_url}{API_SCREENSHOT.format(uuid=uuid)}"
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania zrzutu ekranu urządzenia {uuid}: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_screenshot)

    async def async_set_device_brightness(self, uuid: str, brightness: int) -> bool:
        """Ustawia jasność urządzenia (0-100)."""
        if not 0 <= brightness <= 100:
            _LOGGER.error(f"Nieprawidłowa wartość jasności: {brightness}. Musi być między 0 a 100.")
            return False
        
        return await self.async_set_device_config(uuid, "Brightness", str(brightness))

    async def async_get_device_statistics(self, uuid: str) -> Optional[Dict]:
        """Pobiera statystyki urządzenia."""
        def _get_statistics():
            url = f"{self.base_url}{API_STATISTICS.format(uuid=uuid)}"
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania statystyk urządzenia {uuid}: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_statistics)

    async def async_set_device_schedule(self, uuid: str, schedule_config: Dict) -> bool:
        """Ustawia harmonogram urządzenia."""
        def _set_schedule():
            device_url = f"{self.base_url}{API_DEVICE_DETAIL.format(uuid=uuid)}"
            try:
                response_get = self.session.get(device_url, timeout=10)
                response_get.raise_for_status()
                current_config = response_get.json()
                
                if "Config" not in current_config:
                    current_config["Config"] = {}
                
                current_config["Config"]["Schedule"] = schedule_config
                
                response_put = self.session.put(device_url, json=current_config, timeout=15)
                if response_put.status_code in [200, 201, 204]:
                    _LOGGER.info(f"Pomyślnie ustawiono harmonogram na urządzeniu {uuid}")
                    return True
                else:
                    _LOGGER.error(f"Błąd podczas ustawiania harmonogramu na {uuid}. Status: {response_put.status_code}")
                    return False
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd komunikacji podczas ustawiania harmonogramu na {uuid}: {e}")
                return False
        return await self.hass.async_add_executor_job(_set_schedule)

    async def async_get_server_info(self) -> Optional[Dict]:
        """Pobiera informacje o serwerze Visionect."""
        def _get_server_info():
            url = f"{self.base_url}{API_SERVER_INFO}"
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania informacji o serwerze: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_server_info)

    async def async_get_device_history(self, uuid: str, days: int = 7) -> Optional[List[Dict]]:
        """Pobiera historię urządzenia."""
        def _get_history():
            url = f"{self.base_url}{API_HISTORY.format(uuid=uuid)}?days={days}"
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                _LOGGER.error(f"Błąd pobierania historii urządzenia {uuid}: {e}")
                return None
        return await self.hass.async_add_executor_job(_get_history)


_LOGGER.debug("Plik api.py wczytany pomyślnie.")