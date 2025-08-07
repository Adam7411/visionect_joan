# custom_components/visionect_joan/web_controller.py
import logging
import asyncio
import functools
from typing import Optional

_LOGGER = logging.getLogger(__name__)

# Opcjonalne importy - jeśli nie ma Selenium, to po prostu nie będzie działać interfejs webowy
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    
    # Próbuj import webdriver_manager, ale jeśli nie ma, użyj domyślnej ścieżki
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
        _LOGGER.warning("webdriver_manager niedostępny, używam domyślnej ścieżki chromedriver")
    
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    _LOGGER.warning("Selenium niedostępny - funkcje interfejsu webowego będą wyłączone")

from .const import SELENIUM_TIMEOUT, WEBDRIVER_WAIT_TIME

class VisionectWebController:
    """Klasa do kontrolowania interfejsu webowego Visionect przez Selenium."""

    def __init__(self, hass, base_url: str, username: str = None, password: str = None):
        """Inicjalizacja kontrolera web."""
        self.hass = hass
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.driver = None
        self.selenium_available = SELENIUM_AVAILABLE

    async def _setup_driver(self):
        """Konfiguruje i uruchamia WebDriver."""
        if not self.selenium_available:
            _LOGGER.error("Selenium nie jest dostępny - nie można uruchomić WebDriver")
            return False
            
        def _create_driver():
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Różne sposoby uzyskania ChromeDriver
            try:
                if WEBDRIVER_MANAGER_AVAILABLE:
                    # Preferowana metoda z webdriver_manager
                    service = Service(ChromeDriverManager().install())
                else:
                    # Fallback - spróbuj standardowych lokalizacji
                    possible_paths = [
                        "/usr/bin/chromedriver",
                        "/usr/local/bin/chromedriver",
                        "/opt/google/chrome/chromedriver",
                        "chromedriver"  # W PATH
                    ]
                    
                    driver_path = None
                    for path in possible_paths:
                        try:
                            import os
                            if os.path.isfile(path) and os.access(path, os.X_OK):
                                driver_path = path
                                break
                        except:
                            continue
                    
                    if driver_path:
                        service = Service(driver_path)
                    else:
                        # Ostatnia próba - bez ścieżki (może być w PATH)
                        service = Service()
                        
                return webdriver.Chrome(service=service, options=chrome_options)
                
            except Exception as e:
                _LOGGER.error(f"Nie udało się utworzyć ChromeDriver: {e}")
                # Próba z Firefox jako fallback
                try:
                    from selenium.webdriver.firefox.options import Options as FirefoxOptions
                    from selenium.webdriver.firefox.service import Service as FirefoxService
                    
                    firefox_options = FirefoxOptions()
                    firefox_options.add_argument("--headless")
                    
                    return webdriver.Firefox(options=firefox_options)
                except Exception as ff_e:
                    _LOGGER.error(f"Nie udało się utworzyć FirefoxDriver: {ff_e}")
                    raise e

        try:
            self.driver = await self.hass.async_add_executor_job(_create_driver)
            _LOGGER.debug("WebDriver został pomyślnie utworzony")
            return True
        except Exception as e:
            _LOGGER.error(f"Nie udało się utworzyć WebDriver: {e}")
            return False

    async def _cleanup_driver(self):
        """Zamyka WebDriver."""
        if self.driver:
            def _quit_driver():
                try:
                    self.driver.quit()
                except Exception as e:
                    _LOGGER.warning(f"Błąd podczas zamykania WebDriver: {e}")

            await self.hass.async_add_executor_job(_quit_driver)
            self.driver = None

    async def set_device_url_via_web(self, uuid: str, url: str) -> bool:
        """Ustawia URL urządzenia przez interfejs webowy."""
        if not self.selenium_available:
            _LOGGER.error("Selenium nie jest dostępny - nie można ustawić URL przez interfejs webowy")
            return False
            
        if not await self._setup_driver():
            return False

        try:
            def _set_url():
                try:
                    # Przejdź do strony konfiguracji urządzenia - na podstawie referera z Twoich danych
                    device_config_url = f"{self.base_url}/devices/{uuid}/basic"
                    _LOGGER.debug(f"Przechodzę do: {device_config_url}")
                    self.driver.get(device_config_url)
                    
                    # Poczekaj na załadowanie strony
                    wait = WebDriverWait(self.driver, WEBDRIVER_WAIT_TIME)
                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    
                    # Znajdź pole URL - na podstawie Twoich danych HTML
                    url_input = None
                    selectors = [
                        'input[type="search"][placeholder*="http"]',
                        'input[value*="http"]',
                        'input[placeholder="http://"]',
                        'input.form-control.input-lg',
                        'input[type="text"][autocomplete="off"]',
                        'input[role="combobox"]'
                    ]
                    
                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                current_value = element.get_attribute('value') or ''
                                if 'http' in current_value.lower() or not current_value:
                                    url_input = element
                                    _LOGGER.debug(f"Znaleziono pole URL używając selektora: {selector}")
                                    break
                            if url_input:
                                break
                        except Exception:
                            continue
                    
                    if not url_input:
                        _LOGGER.error("Nie znaleziono pola URL na stronie")
                        return False

                    # Wyczyść pole i wprowadź nowy URL
                    self.driver.execute_script("arguments[0].value = '';", url_input)
                    url_input.clear()
                    url_input.send_keys(url)
                    _LOGGER.debug(f"Wprowadzono URL: {url}")
                    
                    # Znajdź przycisk Save - na podstawie Twoich danych HTML
                    save_button = None
                    
                    # Najpierw spróbuj znaleźć przycisk z ikoną fa-save
                    try:
                        save_icon = self.driver.find_element(By.CSS_SELECTOR, 'i.fa.fa-save')
                        save_button = save_icon.find_element(By.XPATH, '..')  # Przejdź do rodzica (button)
                        _LOGGER.debug("Znaleziono przycisk Save przez ikonę fa-save")
                    except NoSuchElementException:
                        pass
                    
                    if not save_button:
                        # Alternatywne selektory
                        save_selectors = [
                            'button[type="submit"].btn.btn-lg.btn-primary.pull-right',
                            'button.btn.btn-lg.btn-primary.pull-right',
                            'button[type="submit"]'
                        ]
                        
                        for selector in save_selectors:
                            try:
                                save_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                _LOGGER.debug(f"Znaleziono przycisk Save używając: {selector}")
                                break
                            except NoSuchElementException:
                                continue
                        
                        # Jeśli dalej nie ma, szukaj po tekście
                        if not save_button:
                            try:
                                save_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
                                _LOGGER.debug("Znaleziono przycisk Save po tekście")
                            except NoSuchElementException:
                                pass
                    
                    if not save_button:
                        _LOGGER.error("Nie znaleziono przycisku Save")
                        return False

                    # Sprawdź czy przycisk jest widoczny i klikalny
                    if not save_button.is_displayed():
                        _LOGGER.error("Przycisk Save nie jest widoczny")
                        return False
                    
                    if not save_button.is_enabled():
                        _LOGGER.error("Przycisk Save nie jest aktywny")
                        return False

                    # Kliknij przycisk Save
                    self.driver.execute_script("arguments[0].click();", save_button)
                    _LOGGER.debug("Kliknięto przycisk Save")
                    
                    # Poczekaj chwilę na przetworzenie
                    import time
                    time.sleep(3)
                    
                    _LOGGER.info(f"URL urządzenia {uuid} zmieniony na: {url} przez interfejs webowy")
                    return True
                    
                except Exception as e:
                    _LOGGER.error(f"Błąd podczas ustawiania URL przez interfejs webowy: {e}")
                    # Zapisz screenshot dla debugowania (jeśli to możliwe)
                    try:
                        screenshot_path = f"/tmp/visionect_error_{uuid}.png"
                        self.driver.save_screenshot(screenshot_path)
                        _LOGGER.debug(f"Screenshot zapisany: {screenshot_path}")
                    except:
                        pass
                    return False

            result = await self.hass.async_add_executor_job(_set_url)
            return result

        finally:
            await self._cleanup_driver()

    async def test_web_connection(self, uuid: str = None) -> bool:
        """Testuje połączenie z interfejsem webowym."""
        if not self.selenium_available:
            _LOGGER.warning("Selenium nie jest dostępny - nie można przetestować połączenia webowego")
            return False
            
        if not await self._setup_driver():
            return False

        try:
            def _test_connection():
                try:
                    # Jeśli mamy UUID, testuj bezpośrednio stronę urządzenia
                    if uuid:
                        test_url = f"{self.base_url}/devices/{uuid}/basic"
                    else:
                        test_url = self.base_url
                        
                    self.driver.get(test_url)
                    
                    # Sprawdź czy strona się załadowała
                    WebDriverWait(self.driver, WEBDRIVER_WAIT_TIME).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    
                    _LOGGER.debug(f"Test połączenia webowego pomyślny: {test_url}")
                    return True
                    
                except Exception as e:
                    _LOGGER.error(f"Błąd podczas testowania połączenia webowego: {e}")
                    return False

            result = await self.hass.async_add_executor_job(_test_connection)
            return result

        finally:
            await self._cleanup_driver()