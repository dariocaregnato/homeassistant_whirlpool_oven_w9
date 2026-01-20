"""Config flow for Whirlpool Sixth Sense integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from homeassistant.data_entry_flow import FlowResult

from homeassistant.helpers import aiohttp_client

from .const import DOMAIN
from .whirlpool.appliancesmanager import AppliancesManager
from .whirlpool.auth import Auth
from .whirlpool.backendselector import BackendSelector
from .whirlpool.types import Brand, Region

LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_REGION, default="EU"): str,
    }
)

class WhirlpoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Whirlpool Sixth Sense."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                region = Region.EU if user_input[CONF_REGION] == "EU" else Region.US
                session = aiohttp_client.async_get_clientsession(self.hass)
                backend_selector = BackendSelector(Brand.Whirlpool, region)
                auth = Auth(
                    backend_selector,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    session,
                )
                await auth.do_auth()
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
