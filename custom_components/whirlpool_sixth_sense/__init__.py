"""The Whirlpool Sixth Sense integration."""
from __future__ import annotations

import logging
import sys
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .whirlpool.appliancesmanager import AppliancesManager
from homeassistant.helpers import aiohttp_client

from .whirlpool.backendselector import BackendSelector
from .whirlpool.auth import Auth
from .whirlpool.types import Brand, Region

LOGGER = logging.getLogger(__name__)

# List the platforms that you want to support.
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH, Platform.BUTTON, Platform.NUMBER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Whirlpool Sixth Sense from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    region_key = entry.data[CONF_REGION]
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    # Defaults to Whirlpool and EU if not specified, but valid region is required
    region = Region.EU if region_key == "EU" else Region.US
    brand = Brand.Whirlpool

    session = aiohttp_client.async_get_clientsession(hass)
    backend_selector = BackendSelector(brand, region)
    auth = Auth(backend_selector, email, password, session)
    await auth.do_auth()
    
    manager = AppliancesManager(backend_selector, auth, session)
    await manager.fetch_appliances()
    await manager.connect()

    hass.data[DOMAIN][entry.entry_id] = {
        "manager": manager,
        "auth": auth
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
