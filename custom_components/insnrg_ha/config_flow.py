"""Config flow for Insnrg Pool integration."""
import logging
from .call_api import InsnrgPool
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import aiohttp_client
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)

class InsnrgPoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Insnrg Pool."""
    VERSION = 1
    def __init__(self) -> None:
        """Initialize Insnrg Pool config flow."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            _LOGGER.debug(
                "Configuring user: %s - Password hidden", user_input[CONF_EMAIL]
            )
            insnrg_pool = InsnrgPool(
                aiohttp_client.async_get_clientsession(self.hass),
                user_input[CONF_EMAIL],
                user_input[CONF_PASSWORD],
            )
            api_key_valid = await insnrg_pool.test_insnrg_pool_credentials()
            if not api_key_valid:
                errors["base"] = "invalid_auth"
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str
                },
            ),
            errors=errors,
        )
