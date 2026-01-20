"""Platform for button integration."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Local import hacking
from .whirlpool.oven import Oven, Cavity
from .const import DOMAIN, BRAND

LOGGER = logging.getLogger(__name__)

ADJUSTMENTS = [-30, -15, 15, 30]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager = data["manager"]

    entities = []
    for oven in manager.ovens:
        for mins in ADJUSTMENTS:
            entities.append(WhirlpoolTimerButton(oven, mins))
    
    async_add_entities(entities)

class WhirlpoolTimerButton(ButtonEntity):
    """Button to adjust timer duration relatively."""

    def __init__(self, oven: Oven, minutes: int) -> None:
        """Initialize the button."""
        self._oven = oven
        self._minutes = minutes
        sign = "+" if minutes > 0 else ""
        action = "add" if minutes > 0 else "sub"
        action_label = "Add" if minutes > 0 else "Subtract"
        self._attr_name = f"{oven.name} Timer {abs(minutes)}m {action_label}"
        self._attr_unique_id = f"{oven.said}_timer_{action}_{abs(minutes)}m"
        self._attr_icon = "mdi:timer-plus" if minutes > 0 else "mdi:timer-minus"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._oven.said)},
            name=self._oven.name,
            manufacturer=BRAND,
            model=self._oven.appliance_info.data_model,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        current_seconds = self._oven.get_cook_time() or 0
        new_seconds = max(0, current_seconds + (self._minutes * 60))
        await self._oven.set_cook_duration(new_seconds)
