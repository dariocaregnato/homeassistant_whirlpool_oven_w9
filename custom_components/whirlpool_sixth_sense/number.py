"""Platform for number integration."""
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Local import hacking
from .whirlpool.oven import Oven, Cavity, CavityState
from .const import DOMAIN, BRAND

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager = data["manager"]

    entities = []
    for oven in manager.ovens:
        entities.append(WhirlpoolOvenTimerNumber(oven, Cavity.Upper, "Upper"))
    
    async_add_entities(entities)

import asyncio

class WhirlpoolOvenTimerNumber(NumberEntity):
    """Representation of an Oven Timer Number entity with duration formatting."""
    _attr_icon = "mdi:timer"
    _attr_device_class = "duration"
    _attr_native_unit_of_measurement = "s"
    _attr_native_min_value = 0
    _attr_native_max_value = 86400  # 24 hours in seconds
    _attr_native_step = 1
    _attr_mode = "box"

    def __init__(self, oven: Oven, cavity: Cavity, cavity_name: str) -> None:
        """Initialize the number entity."""
        self._oven = oven
        self._cavity = cavity
        self._attr_name = f"{oven.name} Timer"
        self._attr_unique_id = f"{oven.said}_{cavity_name}_timer"
        self._debounce_task = None
        self._local_value = None

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
            # If we aren't currently debouncing, update from server
            if self._debounce_task is None:
                self._local_value = None
                self.schedule_update_ha_state()
        self._oven.register_attr_callback(update)

    async def async_added_to_hass(self) -> None:
        self._register_callback()

    @property
    def native_value(self) -> float | None:
        """Return the current value in seconds."""
        if self._local_value is not None:
             return self._local_value
             
        seconds = self._oven.get_cook_time(self._cavity)
        return seconds if seconds is not None else 0

    async def async_set_native_value(self, value: float) -> None:
        """Set the timer duration with debounce."""
        self._local_value = value
        self.async_write_ha_state()

        if self._debounce_task:
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(self._async_debounced_set(value))

    async def _async_debounced_set(self, value: float) -> None:
        """Internal method to call the API after a delay."""
        try:
            await asyncio.sleep(4.0)  # Increased debounce to 4 seconds as requested
            await self._oven.set_cook_duration(int(value))
        except asyncio.CancelledError:
            pass
        finally:
            self._debounce_task = None
            self._local_value = None
            self.async_write_ha_state()
