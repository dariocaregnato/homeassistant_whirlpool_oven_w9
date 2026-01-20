"""Platform for switch integration."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Local import hacking
from .whirlpool.oven import Oven, Cavity
from .const import DOMAIN, BRAND

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager = data["manager"]

    entities = []
    for oven in manager.ovens:
        entities.append(WhirlpoolOvenLight(oven, Cavity.Upper, "Upper"))
        # Control Lock is usually global for the appliance
        entities.append(WhirlpoolControlLock(oven))
    
    async_add_entities(entities)

class WhirlpoolOvenLight(SwitchEntity):
    """Representation of an Oven Light."""

    def __init__(self, oven: Oven, cavity: Cavity, cavity_name: str) -> None:
        """Initialize the switch."""
        self._oven = oven
        self._cavity = cavity
        self._attr_name = f"{oven.name} Luce" # Renamed from "Light"
        self._attr_unique_id = f"{oven.said}_{cavity_name}_light"
        self._attr_icon = "mdi:lightbulb"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._oven.said)},
            name=self._oven.name,
            manufacturer=BRAND,
            model=self._oven.appliance_info.data_model,
        )

    def _register_callback(self):
        def update():
            self.schedule_update_ha_state()
        self._oven.register_attr_callback(update)

    async def async_added_to_hass(self) -> None:
        self._register_callback()

    @property
    def is_on(self) -> bool | None:
        # Default to False if None to avoid "lightning bolts" assumed state
        return bool(self._oven.get_light(self._cavity))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._oven.set_light(True, self._cavity)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._oven.set_light(False, self._cavity)

class WhirlpoolControlLock(SwitchEntity):
    """Representation of Control Lock."""

    def __init__(self, oven: Oven) -> None:
        """Initialize the switch."""
        self._oven = oven
        # Renamed from "Control Lock"
        self._attr_name = f"{oven.name} Blocco tasti" 
        self._attr_unique_id = f"{oven.said}_control_lock"
        self._attr_icon = "mdi:lock"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._oven.said)},
            name=self._oven.name,
            manufacturer=BRAND,
            model=self._oven.appliance_info.data_model,
        )

    def _register_callback(self):
        def update():
            self.schedule_update_ha_state()
        self._oven.register_attr_callback(update)

    async def async_added_to_hass(self) -> None:
        self._register_callback()

    @property
    def is_on(self) -> bool | None:
        return self._oven.get_control_locked()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._oven.set_control_locked(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._oven.set_control_locked(False)
