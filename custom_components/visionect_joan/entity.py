# custom_components/visionect_joan/entity.py

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MODEL_JOAN6, UNKNOWN_STRINGS

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
        
        device_name = config.get("Name")
        if not device_name or str(device_name).lower() in UNKNOWN_STRINGS:
            device_name = self.uuid

        config_url = None
        if hasattr(self.coordinator, 'config_entry'):
            host = self.coordinator.config_entry.data.get('host')
            if host:
                if not host.startswith(('http://', 'https://')):
                    host = f"http://{host}"
                config_url = host

        return DeviceInfo(
            identifiers={(DOMAIN, self.uuid)},
            name=device_name,
            manufacturer="Visionect",
            model=MODEL_JOAN6,
            sw_version=status.get("ApplicationVersion"),
            configuration_url=config_url
        )