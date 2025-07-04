# custom_components/visionect_joan/entity.py

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MODEL_JOAN6, IP_UNKNOWN

class VisionectEntity(CoordinatorEntity):
    """Bazowa klasa dla wszystkich encji Visionect."""

    def __init__(self, coordinator, uuid: str):
        """Inicjalizacja encji."""
        super().__init__(coordinator)
        self.uuid = uuid
        
        # Atrybut _attr_has_entity_name = True w encjach dziedziczących sprawi,
        # że Home Assistant automatycznie połączy nazwę urządzenia z nazwą encji.
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Zwraca informacje o urządzeniu nadrzędnym."""
        device_data = self.coordinator.data.get(self.uuid, {})
        status = device_data.get("Status", {})
        config = device_data.get("Config", {})
        
        # Używamy nazwy z konfiguracji urządzenia jako nazwy urządzenia w HA
        device_name = config.get("Name", f"Visionect Joan {self.uuid[-4:]}")

        return DeviceInfo(
            identifiers={(DOMAIN, self.uuid)},
            name=device_name,
            manufacturer="Visionect",
            model=MODEL_JOAN6,
            sw_version=status.get("ApplicationVersion"),
            configuration_url=f"http://{status.get('IPAddress')}" if status.get("IPAddress") != IP_UNKNOWN else None
        )