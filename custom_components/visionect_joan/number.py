import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTime

from .const import DOMAIN, EVENT_COMMAND_RESULT
from .entity import VisionectEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if coordinator.data:
        async_add_entities(
            VisionectReloadIntervalNumber(coordinator, uuid) for uuid in coordinator.data
        )
        # Polling time (częstotliwość połączeń urządzenia)
        async_add_entities(
            VisionectPollingTimeNumber(coordinator, uuid) for uuid in coordinator.data
        )
        # Harmonogram uśpienia (Sleep Schedule)
        async_add_entities(
            VisionectSleepScheduleNumber(coordinator, uuid) for uuid in coordinator.data
        )

class VisionectReloadIntervalNumber(VisionectEntity, NumberEntity):
    """Number entity to set the refresh interval (ReloadTimeout)."""

    def __init__(self, coordinator, uuid: str):
        """Initialize the entity."""
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "reload_interval"
        self._attr_unique_id = f"{uuid}_reload_interval"
        self._attr_icon = "mdi:timer-sync-outline"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        
        self._attr_native_min_value = 0
        self._attr_native_max_value = 86400
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the current value of the refresh interval."""
        device_data = self.coordinator.data.get(self.uuid, {})
        config = device_data.get("Config", {})
        reload_timeout_str = config.get("ReloadTimeout", "0")

        try:
            return float(reload_timeout_str)
        except (ValueError, TypeError):
            _LOGGER.warning(f"Failed to parse ReloadTimeout for {self.uuid}: '{reload_timeout_str}'")
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value for the refresh interval."""
        api = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        
        timeout_str = str(int(value))
        status = "failure"
        
        _LOGGER.debug(f"Setting ReloadTimeout for {self.uuid} to {timeout_str}s")
        success = await api.async_set_reload_timeout(self.uuid, timeout_str)

        if success:
            _LOGGER.info(f"ReloadTimeout for {self.uuid} was successfully set.")
            status = "success"
            # Manually update the value in the coordinator for an immediate UI effect
            if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["Config"]["ReloadTimeout"] = timeout_str
                self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to set ReloadTimeout for {self.uuid}.")

        self.hass.bus.async_fire(EVENT_COMMAND_RESULT, {
            "uuid": self.uuid,
            "service": "number.set_value",
            "entity_id": self.entity_id,
            "status": status,
            "params": {"value": timeout_str}
        })
        
        await self.coordinator.async_request_refresh()

class VisionectPollingTimeNumber(VisionectEntity, NumberEntity):
    """Sterowanie czasem wybudzania fizycznego urządzenia (oszczędzanie baterii)."""

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "polling_time"
        self._attr_unique_id = f"{uuid}_polling_time"
        self._attr_icon = "mdi:battery-clock"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_native_min_value = 60
        self._attr_native_max_value = 86400
        self._attr_native_step = 60

    @property
    def native_value(self) -> float | None:
        # Pobieramy z Options urządzenia, nie z Config sesji
        opts = self.coordinator.data.get(self.uuid, {}).get("Options", {})
        val = opts.get("PollingTime")
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        api = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        # Wymaga dodania metody async_set_device_option w api.py
        await api.async_set_device_option(self.uuid, "PollingTime", str(int(value)))
        await self.coordinator.async_request_refresh()


class VisionectSleepScheduleNumber(VisionectEntity, NumberEntity):
    """Czas uśpienia urządzenia w minutach (0 = wyłączone).
    
    Ustawia pole Options.SleepSchedule w API Visionect.
    Przy PeriodicSleep=true: czas w minutach między wybudzeniami.
    Przy PeriodicSleep=false: minuta dnia kiedy urządzenie się wybudza.
    """

    def __init__(self, coordinator, uuid: str):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "sleep_schedule"
        self._attr_unique_id = f"{uuid}_sleep_schedule"
        self._attr_icon = "mdi:sleep"
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1440   # max 24h
        self._attr_native_step = 5
        self._attr_mode = NumberMode.BOX
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self) -> float | None:
        opts = self.coordinator.data.get(self.uuid, {}).get("Options", {})
        val = opts.get("SleepSchedule")
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        api = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        await api.async_set_device_option(self.uuid, "SleepSchedule", str(int(value)))
        await self.coordinator.async_request_refresh()

