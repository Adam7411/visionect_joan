# custom_components/visionect_joan/select.py
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.persistent_notification import async_create

from .const import DOMAIN
from .entity import VisionectEntity
from .api import VisionectAPI

_LOGGER = logging.getLogger(__name__)

# ---> NOWY KOD: Definiujemy klucz dla naszej opcji instrukcji <---
INSTRUCTION_OPTION_KEY = "unconfigured_prompt"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja encji select na podstawie wpisu konfiguracyjnego."""
    views = hass.data[DOMAIN].get('views', [])
    
    coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    if coordinator and coordinator.data:
        entities = [
            VisionectViewSelect(coordinator, uuid, views) for uuid in coordinator.data
        ]
        async_add_entities(entities)

class VisionectViewSelect(VisionectEntity, SelectEntity):
    """Encja select do przełączania predefiniowanych widoków na urządzeniu Visionect."""

    def __init__(self, coordinator, uuid: str, views: list):
        super().__init__(coordinator, uuid)
        self._attr_translation_key = "view_select"
        self._attr_unique_id = f"{uuid}_view_select"
        self._attr_icon = "mdi:view-dashboard-outline"
        
        self._is_configured = bool(views)
        self._views = {view["name"]: view["url"] for view in views}
        
        # ---> NOWA LOGIKA: Zawsze dodajemy opcję instrukcji na końcu listy <---
        # Zaczynamy od listy zdefiniowanych widoków...
        options = list(self._views.keys())
        # ...i zawsze doklejamy do niej opcję z instrukcją.
        options.append(INSTRUCTION_OPTION_KEY)
        self._attr_options = options

    @property
    def current_option(self) -> str | None:
        if not self._is_configured:
            return "unconfigured_state"

        device_data = self.coordinator.data.get(self.uuid, {})
        current_url = device_data.get("Config", {}).get("Url")
        if not current_url: return None
        for name, url in self._views.items():
            if url == current_url: return name
        if current_url.startswith("data:text/html,"): return "Wiadomość tekstowa"
        return "URL niestandardowy"

    async def async_select_option(self, option: str) -> None:
        # ---> NOWA LOGIKA: Sprawdzamy, czy kliknięto opcję instrukcji <---
        if option == INSTRUCTION_OPTION_KEY:
            _LOGGER.info("Użytkownik zażądał instrukcji konfiguracji. Tworzenie powiadomienia.")

            if self.hass.config.language == "pl":
                title = "Skonfiguruj widoki dla Visionect Joan"
                message = (
                    "Integracja **Visionect Joan** nie ma skonfigurowanych żadnych widoków do wyboru.\n\n"
                    "Dodaj poniższy przykład do pliku `configuration.yaml` i dostosuj go do swoich potrzeb:\n\n"
                    "```yaml\n"
                    "visionect_joan:\n"
                    "  views:\n"
                    "    - name: \"Przykład z Appdaemon\"\n"
                    "      url: \"http://<TWOJE_IP_HA>:5050/nazwa_dashboardu\"\n"
                    "    - name: \"Przykład Zdjęcie\"\n"
                    "      url: \"http://<TWOJE_IP_HA>:8123/local/obrazek.png\"\n"
                    "    - name: \"Przykład Adres URL\"\n"
                    "      url: \"https://www.home-assistant.io/\"\n"
                    "```"
                )
            else:
                title = "Configure Views for Visionect Joan"
                message = (
                    "The **Visionect Joan** integration has no views configured for the select entity.\n\n"
                    "Add the following example to your `configuration.yaml` file and customize it to your needs:\n\n"
                    "```yaml\n"
                    "visionect_joan:\n"
                    "  views:\n"
                    "    - name: \"Example with AppDaemon\"\n"
                    "      url: \"http://<YOUR_HA_IP>:5050/dashboard_name\"\n"
                    "    - name: \"Example Photo\"\n"
                    "      url: \"http://<YOUR_HA_IP>:8123/local/image.png\"\n"
                    "    - name: \"Example URL\"\n"
                    "      url: \"https://www.home-assistant.io/\"\n"
                    "```"
                )
            
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="visionect_joan_setup_views"
            )
            
            # Resetujemy stan, aby encja nie "zapamiętała" wyboru instrukcji
            self.async_write_ha_state()
            return
            
        if option not in self._views:
            _LOGGER.error(f"Wybrano nieznany widok: {option}")
            return
            
        target_url = self._views[option]
        api: VisionectAPI = self.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["api"]
        _LOGGER.info(f"Zmiana widoku dla {self.uuid} na '{option}' ({target_url})")
        
        if await api.async_set_device_url(self.uuid, target_url) and await api.async_restart_session(self.uuid):
            _LOGGER.info(f"Widok dla {self.uuid} pomyślnie zmieniony.")
            if self.uuid in self.coordinator.data and "Config" in self.coordinator.data[self.uuid]:
                self.coordinator.data[self.uuid]["Config"]["Url"] = target_url
                self.async_write_ha_state()
        else:
            _LOGGER.error(f"Nie udało się zmienić widoku dla {self.uuid}.")
        await self.coordinator.async_request_refresh()