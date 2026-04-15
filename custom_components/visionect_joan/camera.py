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
    """Set up camera entities based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api: VisionectAPI = hass.data[DOMAIN][entry.entry_id]["api"]

    if coordinator.data:
        entities = []
        for uuid in coordinator.data:
            entities.append(VisionectScreenshotCamera(coordinator, uuid, api))
        async_add_entities(entities)

class VisionectScreenshotCamera(VisionectEntity, Camera):
    """Camera entity for Visionect device screenshot preview."""

    _attr_translation_key = "live_view"

    def __init__(self, coordinator, uuid: str, api: VisionectAPI):
        """Initialize the camera."""
        VisionectEntity.__init__(self, coordinator, uuid)
        Camera.__init__(self)
        self._api = api
        self._attr_unique_id = f"{uuid}_live_view"
        self._attr_icon = "mdi:monitor-screenshot"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the image from the camera as binary data."""
        try:
            image_bytes = await self._api.async_get_device_screenshot(self.uuid)
            return image_bytes
        except Exception as e:
            _LOGGER.error(f"Error while fetching image for camera {self.unique_id}: {e}")
            return None