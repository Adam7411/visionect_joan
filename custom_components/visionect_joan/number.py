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