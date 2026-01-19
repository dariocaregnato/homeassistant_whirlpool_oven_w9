"""Config flow for Whirlpool Sixth Sense integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .whirlpool.auth import Auth
from .whirlpool.backendselector import BackendSelector
from .whirlpool.types import Brand, Region

LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Forno"): str,
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION, default="EU"): vol.In(["EU", "US"]),
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
                backend_selector = BackendSelector(Brand.Whirlpool, region)
                auth = Auth(
                    backend_selector,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
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
