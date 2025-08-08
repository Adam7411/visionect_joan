# custom_components/visionect_joan/entity.py

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MODEL_JOAN6, IP_UNKNOWN, UNKNOWN_STRINGS

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
        
        # Sprawdź nazwę z konfiguracji. Jeśli jej nie ma lub jest "nieznana", użyj UUID.
        device_name = config.get("Name")
        if not device_name or str(device_name).lower() in UNKNOWN_STRINGS:
            device_name = self.uuid # Użyj pełnego UUID jako domyślnej nazwy

        # Pobierz adres IP z konfiguracji entry (adres serwera Visionect)
        # Musimy mieć dostęp do entry.data[CONF_HOST]
        config_url = None
        if hasattr(self.coordinator, 'config_entry'):
            host = self.coordinator.config_entry.data.get('host')
            if host:
                # Upewnij się, że ma protokół
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