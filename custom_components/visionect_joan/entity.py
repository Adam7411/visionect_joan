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

        # Pobierz adres IP z statusu urządzenia
        ip_address = status.get('IPAddress')
        config_url = None
        
        # Sprawdź czy IP jest prawidłowy i nie jest "unknown"
        if ip_address and str(ip_address).lower() not in UNKNOWN_STRINGS and ip_address != IP_UNKNOWN:
            config_url = f"http://{ip_address}"
            # Dodaj IP jako identyfikator połączenia dla lepszej identyfikacji
            connections = {("ip", ip_address)}
        else:
            ip_address = None
            connections = set()

        # Przygotuj dodatkowe informacje o urządzeniu
        device_info = DeviceInfo(
            identifiers={(DOMAIN, self.uuid)},
            name=device_name,
            manufacturer="Visionect",
            model=MODEL_JOAN6,
            sw_version=status.get("ApplicationVersion"),
            configuration_url=config_url,
            connections=connections
        )
        
        # Dodaj adres IP jako dodatkowy atrybut jeśli jest dostępny
        if ip_address:
            # Możemy dodać sugerowaną nazwę obszaru na podstawie IP
            device_info["suggested_area"] = self._suggest_area_from_ip(ip_address)
        
        return device_info
    
    def _suggest_area_from_ip(self, ip_address: str) -> str:
        """Sugeruje nazwę obszaru na podstawie adresu IP."""
        try:
            # Przykład: jeśli IP to 192.168.1.100, sugeruj "Network_192_168_1"
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"Network_{parts[0]}_{parts[1]}_{parts[2]}"
        except:
            pass
        return "Visionect Devices"