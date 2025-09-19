# custom_components/visionect_joan/camera.py
import logging

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja encji kamery na podstawie wpisu konfiguracyjnego."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api: VisionectAPI = hass.data[DOMAIN][entry.entry_id]["api"]

    if coordinator.data:
        entities = []
        for uuid in coordinator.data:
            # Tworzymy naszą nową, dedykowaną encję kamery
            entities.append(VisionectScreenshotCamera(coordinator, uuid, api))
        async_add_entities(entities)

class VisionectScreenshotCamera(VisionectEntity, Camera):
    """Encja kamery dla podglądu zrzutu ekranu z urządzenia Visionect."""

    def __init__(self, coordinator, uuid: str, api: VisionectAPI):
        """Inicjalizacja kamery."""
        VisionectEntity.__init__(self, coordinator, uuid)
        Camera.__init__(self)
        self._api = api
        
        device_name = self.device_info.get("name", uuid)
        self._attr_name = f"{device_name} Live View"
        self._attr_unique_id = f"{uuid}_live_view"
        self._attr_icon = "mdi:monitor-screenshot"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Zwraca obraz z kamery jako dane binarne."""
        try:
            # Używamy naszej nowej funkcji z api.py, która korzysta z zalogowanej sesji
            image_bytes = await self._api.async_get_device_screenshot(self.uuid)
            return image_bytes
        except Exception as e:
            _LOGGER.error(f"Błąd podczas pobierania obrazu dla kamery {self.unique_id}: {e}")
            return None