"""Definicje encji number dla integracji Stiebel Eltron."""
import logging
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .api import StiebelEltronAPI

_LOGGER = logging.getLogger(__name__)

NUMBER_DESCRIPTIONS: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="ustaw_temp_cwu_on",
        name="Temperatura załączenia CWU (30-60°C)",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=30,
        native_max_value=60,
        native_step=0.5,
        mode=NumberMode.BOX,
        icon="mdi:thermometer-chevron-down",
    ),
    NumberEntityDescription(
        key="ustaw_temp_cwu_off",
        name="Temperatura wyłączenia CWU (30-70°C)",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=30,
        native_max_value=70,
        native_step=0.5,
        mode=NumberMode.BOX,
        icon="mdi:thermometer-chevron-up",
    ),
    NumberEntityDescription(
        key="ustaw_temp_pomieszczenia",
        name="Docelowa temperatura pomieszczenia (10-30°C)",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=10,
        native_max_value=30,
        native_step=0.1,
        mode=NumberMode.BOX,
        icon="mdi:home-thermometer-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguruje encje number."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = domain_data["coordinator"]
    api = domain_data["api"]
    
    entities = [
        StiebelEltronNumberEntity(coordinator, description, entry, api)
        for description in NUMBER_DESCRIPTIONS
    ]
    async_add_entities(entities)


class StiebelEltronNumberEntity(CoordinatorEntity, NumberEntity):
    """Reprezentacja encji number z 'pamięcią'."""

    def __init__(
        self,
        coordinator,
        description: NumberEntityDescription,
        entry: ConfigEntry,
        api: StiebelEltronAPI,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": NAME,
            "manufacturer": "Stiebel Eltron",
            "model": "WPE-I Plus",
            "configuration_url": f"http://{entry.data[CONF_HOST]}",
        }

    @property
    def native_value(self) -> float | None:
        """Zwraca aktualną wartość z pamięci koordynatora."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        """Wysyła nową wartość do pompy i zapisuje ją w pamięci HA."""
        key = self.entity_description.key
        success = False
        
        if self.coordinator.data is None:
            self.coordinator.data = {}

        # Używamy wartości z pamięci lub bezpiecznej domyślnej
        current_on = self.coordinator.data.get("ustaw_temp_cwu_on", 42.0)
        current_off = self.coordinator.data.get("ustaw_temp_cwu_off", 48.0)

        if key == "ustaw_temp_pomieszczenia":
            success = await self.api.async_set_values([{"name": "val40006", "value": value}])
            if success:
                self.coordinator.data[key] = value
        elif key in ("ustaw_temp_cwu_on", "ustaw_temp_cwu_off"):
            temp_on = value if key == "ustaw_temp_cwu_on" else current_on
            temp_off = value if key == "ustaw_temp_cwu_off" else current_off
            settings = [
                {"name": "val40023", "value": temp_on},
                {"name": "val40024", "value": temp_off},
            ]
            success = await self.api.async_set_values(settings)
            if success:
                self.coordinator.data["ustaw_temp_cwu_on"] = temp_on
                self.coordinator.data["ustaw_temp_cwu_off"] = temp_off
        
        if success:
            # Ręcznie informujemy HA o zmianie stanu, aby natychmiast pokazał nową wartość
            self.async_write_ha_state()
            # Dla pewności, odświeżamy też stan drugiej encji (jeśli była zmieniana temp. CWU)
            self.coordinator.async_update_listeners()