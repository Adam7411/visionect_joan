import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

from .api import VisionectAPI
from .const import DOMAIN, CONF_API_KEY, CONF_API_SECRET

_LOGGER = logging.getLogger(__name__)

class VisionectJoanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfiguracja przepływu konfiguracji."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Krok konfiguracji użytkownika."""
        errors = {}
        if user_input is not None:
            try:
                api = VisionectAPI(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input.get(CONF_USERNAME),
                    user_input.get(CONF_PASSWORD),
                    user_input.get(CONF_API_KEY),
                    user_input.get(CONF_API_SECRET)
                )
                
                if await api.async_test_authentication():
                    return self.async_create_entry(
                        title="Visionect Joan",
                        data=user_input
                    )
                errors["base"] = "auth_failed"
            except Exception as ex:
                _LOGGER.error("Error during setup: %s", str(ex))
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_USERNAME): str,
            vol.Optional(CONF_PASSWORD): str,
            vol.Optional(CONF_API_KEY): str,
            vol.Optional(CONF_API_SECRET): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": "Podaj dane logowania lub klucze API"
            }
        )