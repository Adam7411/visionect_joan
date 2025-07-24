"""Definicje przełączników dla integracji Stiebel Eltron."""
from typing import Any
import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, NAME
from .api import StiebelEltronAPI

_LOGGER = logging.getLogger(__name__)

class StiebelEltronBaseSwitch(CoordinatorEntity, SwitchEntity):
    """Bazowa klasa dla przełączników Stiebel Eltron."""
    def __init__(self, coordinator, api: StiebelEltronAPI, entry: ConfigEntry):
        super().__init__(coordinator)
        self.api = api
        
        # Pobierz host z entry.data z debugowaniem
        host = entry.data.get(CONF_HOST, "unknown")
        _LOGGER.info(f"Tworzenie przełącznika - host z entry.data: {host}")
        _LOGGER.info(f"Zawartość entry.data: {entry.data}")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)}, 
            "name": NAME, 
            "manufacturer": "Stiebel Eltron",
            "model": "WPE-I Plus",
            "configuration_url": f"http://{host}",
            "sw_version": "1.0.1",
        }
        
        _LOGGER.info(f"Device info dla przełącznika: {self._attr_device_info}")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Aktualizacja po zmianie danych w koordynatorze."""
        super()._handle_coordinator_update()
        _LOGGER.debug(f"Aktualizacja {self._attr_name}: {self.is_on}")

    async def _async_delayed_refresh(self, _):
        """Zaplanowane odświeżenie w tle."""
        _LOGGER.debug(f"Zaplanowane odświeżenie dla {self._attr_name}")
        await self.coordinator.async_request_refresh()

class StiebelEltronCWUSwitch(StiebelEltronBaseSwitch):
    _attr_name = "Tryb CWU"
    _attr_icon = "mdi:water-pump"
    
    def __init__(self, coordinator, api, entry):
        super().__init__(coordinator, api, entry)
        self._attr_unique_id = f"{entry.entry_id}_tryb_cwu"
    
    @property
    def is_on(self) -> bool | None:
        """Zwraca rzeczywisty stan CWU z koordynatora."""
        if self.coordinator.data is None:
            return None
        
        state = self.coordinator.data.get("stan_cwu")
        _LOGGER.debug(f"Stan CWU z koordynatora: {state}")
        return state

    @property
    def available(self) -> bool:
        """Dostępność encji - true jeśli mamy połączenie z koordynatorem."""
        return super().available and self.coordinator.data is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Włącza tryb CWU."""
        _LOGGER.info("Włączanie trybu CWU")
        success = await self.api.async_set_values([{"name": "val9", "value": "1"}])
        
        if success:
            # Nie ustawiamy stanu lokalnie - pozwalamy koordynatorowi go odczytać
            _LOGGER.info("Pomyślnie wysłano komendę włączenia CWU")
            # Odświeżamy po krótkim czasie, aby pobrać rzeczywisty stan
            async_call_later(self.hass, 3, self._async_delayed_refresh)
        else:
            _LOGGER.error("Błąd podczas włączania CWU")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Wyłącza tryb CWU."""
        _LOGGER.info("Wyłączanie trybu CWU")
        success = await self.api.async_set_values([{"name": "val9", "value": "0"}])
        
        if success:
            _LOGGER.info("Pomyślnie wysłano komendę wyłączenia CWU")
            async_call_later(self.hass, 3, self._async_delayed_refresh)
        else:
            _LOGGER.error("Błąd podczas wyłączania CWU")

class StiebelEltronHeatingSwitch(StiebelEltronBaseSwitch):
    _attr_name = "Tryb ogrzewania"
    _attr_icon = "mdi:radiator"
    
    def __init__(self, coordinator, api, entry):
        super().__init__(coordinator, api, entry)
        self._attr_unique_id = f"{entry.entry_id}_tryb_ogrzewania"

    @property
    def is_on(self) -> bool | None:
        """Zwraca rzeczywisty stan ogrzewania z koordynatora."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("stan_ogrzewania")
        _LOGGER.debug(f"Stan ogrzewania z koordynatora: {state}")
        return state

    @property
    def available(self) -> bool:
        """Dostępność encji - true jeśli mamy połączenie z koordynatorem."""
        return super().available and self.coordinator.data is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Włącza tryb ogrzewania."""
        _LOGGER.info("Włączanie trybu ogrzewania")
        success = await self.api.async_set_values([{"name": "val10", "value": "1"}])
        
        if success:
            _LOGGER.info("Pomyślnie wysłano komendę włączenia ogrzewania")
            async_call_later(self.hass, 3, self._async_delayed_refresh)
        else:
            _LOGGER.error("Błąd podczas włączania ogrzewania")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Wyłącza tryb ogrzewania."""
        _LOGGER.info("Wyłączanie trybu ogrzewania")
        success = await self.api.async_set_values([{"name": "val10", "value": "0"}])
        
        if success:
            _LOGGER.info("Pomyślnie wysłano komendę wyłączenia ogrzewania")
            async_call_later(self.hass, 3, self._async_delayed_refresh)
        else:
            _LOGGER.error("Błąd podczas wyłączania ogrzewania")

class StiebelEltronAntilegionellaSwitch(StiebelEltronBaseSwitch):
    _attr_name = "Antylegionella"
    _attr_icon = "mdi:shield-check"
    
    def __init__(self, coordinator, api, entry):
        super().__init__(coordinator, api, entry)
        self._attr_unique_id = f"{entry.entry_id}_antylegionella"

    @property
    def is_on(self) -> bool | None:
        """Zwraca rzeczywisty stan antylegionella z koordynatora."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("stan_antylegionella")
        _LOGGER.debug(f"Stan antylegionella z koordynatora: {state}")
        return state

    @property
    def available(self) -> bool:
        """Dostępność encji - true jeśli mamy połączenie z koordynatorem."""
        return super().available and self.coordinator.data is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Włącza antylegionella."""
        _LOGGER.info("Włączanie antylegionella")
        success = await self.api.async_set_values([{"name": "val25", "value": "1"}])
        
        if success:
            _LOGGER.info("Pomyślnie wysłano komendę włączenia antylegionella")
            async_call_later(self.hass, 3, self._async_delayed_refresh)
        else:
            _LOGGER.error("Błąd podczas włączania antylegionella")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Wyłącza antylegionella."""
        _LOGGER.info("Wyłączanie antylegionella")
        success = await self.api.async_set_values([{"name": "val25", "value": "0"}])
        
        if success:
            _LOGGER.info("Pomyślnie wysłano komendę wyłączenia antylegionella")
            async_call_later(self.hass, 3, self._async_delayed_refresh)
        else:
            _LOGGER.error("Błąd podczas wyłączania antylegionella")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Konfiguruje encje przełączników."""
    _LOGGER.info(f"Konfiguracja przełączników - entry.data: {entry.data}")
    
    domain_data = hass.data[DOMAIN][entry.entry_id]
    coordinator, api = domain_data["coordinator"], domain_data["api"]
    
    switches = [
        StiebelEltronCWUSwitch(coordinator, api, entry),
        StiebelEltronHeatingSwitch(coordinator, api, entry),
        StiebelEltronAntilegionellaSwitch(coordinator, api, entry),
    ]
    
    async_add_entities(switches)
    _LOGGER.info(f"Utworzono {len(switches)} przełączników")