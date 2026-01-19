"""Platform for climate integration."""
import logging
import asyncio
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    PRESET_NONE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_get_current_platform
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, BRAND
# Local import hacking
from .whirlpool.oven import Oven, CookMode, Cavity, CookOperation, CavityState

LOGGER = logging.getLogger(__name__)

# Italian mapping for presets
PRESET_BAKE = "Statico"
PRESET_CONVECT_BAKE = "Cottura ventilata" # Renamed
PRESET_BROIL = "Grill"
PRESET_CONVECT_BROIL = "Turbo grill" # Renamed
PRESET_CONVECT_ROAST = "Maxi cooking" # Renamed
PRESET_KEEP_WARM = "Mantenere in caldo" # Renamed
PRESET_FORCED_AIR = "Termoventilato" # New
PRESET_STEAM = "Vapore" # New
PRESET_RISING = "Speciale lievitazione" # New
PRESET_RAPID_PREHEAT = "Preriscaldamento veloce" # New

# New Modes
PRESET_FROZEN_BAKE = "Cottura Surgelati"
PRESET_COOK_4 = "Cook 4"
PRESET_PIZZA = "Pizza"
PRESET_BREAD = "Pane"

COOK_MODE_TO_PRESET = {
    CookMode.Bake: PRESET_BAKE,
    CookMode.ConvectBake: PRESET_CONVECT_BAKE,
    CookMode.Broil: PRESET_BROIL,
    CookMode.ConvectBroil: PRESET_CONVECT_BROIL,
    CookMode.ConvectRoast: PRESET_CONVECT_ROAST,
    CookMode.KeepWarm: PRESET_KEEP_WARM,
    CookMode.ForcedAir: PRESET_FORCED_AIR,
    CookMode.Steam: PRESET_STEAM,
    CookMode.Rising: PRESET_RISING,
    CookMode.RapidPreheat: PRESET_RAPID_PREHEAT,
    CookMode.Standby: PRESET_NONE
}

PRESET_TO_COOK_MODE = {v: k for k, v in COOK_MODE_TO_PRESET.items() if k != CookMode.Standby}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager = data["manager"]

    device_name = data.get("device_name", "Whirlpool")

    entities = []
    for oven in manager.ovens:
        # Assuming single cavity for simplicity, or we could loop cavities
        entities.append(WhirlpoolOven(oven, Cavity.Upper, "Upper", device_name))
    
    async_add_entities(entities)

    platform = async_get_current_platform()

    platform.async_register_entity_service(
        "set_sixth_sense_mode",
        {
            vol.Required("id"): cv.positive_int,
            vol.Optional("temp"): vol.Coerce(float),
            vol.Optional("weight"): vol.Coerce(float),
            vol.Optional("doneness"): cv.positive_int,
            vol.Optional("food_type"): cv.positive_int,
            vol.Optional("flexi_cook"): cv.boolean,
            vol.Optional("steam_level"): cv.positive_int,
        },
        "async_set_sixth_sense_mode",
    )
    
    platform.async_register_entity_service(
        "set_frozen_bake_id",
        {
            vol.Required("id"): cv.positive_int,
            vol.Optional("temp"): vol.Coerce(float),
        },
        "async_set_frozen_bake_id",
    )

class WhirlpoolOven(ClimateEntity):
    """Representation of a Whirlpool Oven."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 30
    _attr_max_temp = 250
    # Add new presets to the list
    _attr_preset_modes = list(PRESET_TO_COOK_MODE.keys()) + [
        # Hidden per user request
        # PRESET_FROZEN_BAKE,
        # PRESET_COOK_4,
        # PRESET_PIZZA,
        # PRESET_BREAD,
        PRESET_NONE
    ]

    def __init__(self, oven: Oven, cavity: Cavity, cavity_name: str, device_name: str) -> None:
        """Initialize the oven."""
        self._oven = oven
        self._cavity = cavity
        self._cavity_name = cavity_name
        self._attr_name = device_name
        self._attr_unique_id = f"{oven.said}_{cavity_name}_climate"
        self._device_name = device_name
        self._last_preset = PRESET_BAKE # Default to Static on first turn on
        self._current_preset_name = PRESET_NONE # Track manual/custom presets locally

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._oven.said)},
            name=self._device_name,
            manufacturer=BRAND,
            model=self._oven.appliance_info.data_model or "Sixth Sense Appliance",
        )

    def _register_callback(self):
        def update():
            # Try to infer preset from attributes if not tracking
            # This is hard because multiple attributes map to modes.
            # Ideally we check the attributes to update _current_preset_name
            self.schedule_update_ha_state()
        self._oven.register_attr_callback(update)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._register_callback()

    @property
    def current_temperature(self) -> float | None:
        temp = self._oven.get_temp(self._cavity)
        return temp if temp is not None else 0

    @property
    def target_temperature(self) -> float | None:
        temp = self._oven.get_target_temp(self._cavity)
        # If temp is 0/None (Standby), return default valid temp (e.g. 180) 
        # so the UI control remains usable/visible.
        if temp is None or temp == 0:
            return 180
        return temp

    @property
    def hvac_mode(self) -> HVACMode | None:
        state = self._oven.get_cavity_state(self._cavity)
        if state == CavityState.Standby:
             # Force OFF if we just requested it
             return HVACMode.OFF

        if self._current_preset_name == PRESET_NONE:
             return HVACMode.OFF

        return HVACMode.HEAT

    @property
    def preset_mode(self) -> str | None:
        if self.hvac_mode == HVACMode.OFF:
            return PRESET_NONE
        
        # Check Standard Modes
        mode = self._oven.get_cook_mode(self._cavity)
        standard_preset = COOK_MODE_TO_PRESET.get(mode)
        
        if standard_preset and standard_preset != PRESET_NONE:
            return standard_preset
        
        # Check Custom Modes based on stored state or inference
        if self._current_preset_name != PRESET_NONE:
            return self._current_preset_name
        
        return PRESET_NONE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._oven.stop_cook(self._cavity)
            self._current_preset_name = PRESET_NONE
        elif hvac_mode == HVACMode.HEAT:
            # Turn on with last used or default preset
            await self.async_set_preset_mode(self._last_preset)
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_NONE:
             await self._oven.stop_cook(self._cavity)
             self._current_preset_name = PRESET_NONE
             self.async_write_ha_state()
             return

        # Capture current time before potential transition
        cook_time = self._oven.get_cook_time(self._cavity)

        # If switching from one running mode to another, stop first to be safe
        state = self._oven.get_cavity_state(self._cavity)
        transition = False
        if state != CavityState.Standby and self.preset_mode != preset_mode:
             transition = True
             # Preserve timer by not resetting it in stop_cook
             await self._oven.stop_cook(self._cavity, reset_timer=False)
             await asyncio.sleep(0.5)
             state = CavityState.Standby # Refresh internal state after stop

        self._last_preset = preset_mode
        self._current_preset_name = preset_mode
        current_temp = self.target_temperature or 180
        
        # Determine operation
        op = CookOperation.Modify if state in [CavityState.Cooking, CavityState.Preheating] else CookOperation.Start

        if cook_time == 0:
             cook_time = None

        # Handle Standard Modes
        cook_mode = PRESET_TO_COOK_MODE.get(preset_mode)
        if cook_mode:
            await self._oven.set_cook(mode=cook_mode, target_temp=current_temp, cavity=self._cavity, cook_time=cook_time, operation_type=op)
        elif preset_mode == PRESET_FROZEN_BAKE:
            await self._oven.set_frozen_bake(temp=current_temp, cavity=self._cavity, cook_time=cook_time)
        elif preset_mode == PRESET_COOK_4:
            await self._oven.set_cook_4(temp=current_temp, cavity=self._cavity, cook_time=cook_time)
        elif preset_mode == PRESET_PIZZA:
            await self._oven.set_culinary_cycle(cycle_id=454, temp=current_temp, cavity=self._cavity, cook_time=cook_time)
        elif preset_mode == PRESET_BREAD:
            await self._oven.set_culinary_cycle(cycle_id=459, temp=current_temp, cavity=self._cavity, cook_time=cook_time)
        
        # Delayed restoration if it was a transition and we had a timer
        if transition and cook_time and cook_time > 0:
            async def restore_timer():
                await asyncio.sleep(2.5)
                await self._oven.set_cook_duration(cook_time, self._cavity)
            asyncio.create_task(restore_timer())

        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        
        preset = self._current_preset_name
        if preset == PRESET_NONE:
             preset = self._last_preset
             
        # Determine operation
        state = self._oven.get_cavity_state(self._cavity)
        op = CookOperation.Modify if state in [CavityState.Cooking, CavityState.Preheating] else CookOperation.Start
        
        cook_time = self._oven.get_cook_time(self._cavity)
        if cook_time == 0:
             cook_time = None

        # Italian mapping for presets
        cook_mode = PRESET_TO_COOK_MODE.get(preset)
        if cook_mode:
            await self._oven.set_cook(mode=cook_mode, target_temp=temp, cavity=self._cavity, cook_time=cook_time, operation_type=op)
            self._current_preset_name = preset
            return

        # For custom modes, try calling them again with the new temperature
        if preset == PRESET_FROZEN_BAKE:
            await self._oven.set_frozen_bake(temp=temp, cavity=self._cavity, cook_time=cook_time)
        elif preset == PRESET_COOK_4:
            await self._oven.set_cook_4(temp=temp, cavity=self._cavity, cook_time=cook_time)
        elif preset == PRESET_PIZZA:
            await self._oven.set_culinary_cycle(cycle_id=454, temp=temp, cavity=self._cavity, cook_time=cook_time)
        elif preset == PRESET_BREAD:
            await self._oven.set_culinary_cycle(cycle_id=459, temp=temp, cavity=self._cavity, cook_time=cook_time)
            
        self.async_write_ha_state()

    async def async_set_sixth_sense_mode(self, id: int, temp: float | None = None, **kwargs: Any) -> None:
        """Set a custom 6th Sense mode by ID with optional parameters."""
        if self.hvac_mode != HVACMode.OFF:
             await self._oven.stop_cook(self._cavity)
             
        target_temp = temp or self.target_temperature or 180
        await self._oven.set_culinary_cycle(cycle_id=id, temp=target_temp, cavity=self._cavity, **kwargs)
        self._current_preset_name = f"6th Sense {id}"
        self.async_write_ha_state()

    async def async_set_frozen_bake_id(self, id: int, temp: float | None = None) -> None:
        """Set a custom Frozen Bake mode by ID."""
        if self.hvac_mode != HVACMode.OFF:
             await self._oven.stop_cook(self._cavity)

        target_temp = temp or self.target_temperature or 180
        await self._oven.set_frozen_bake(temp=target_temp, food_type=id, cavity=self._cavity)
        self._current_preset_name = f"Frozen/Custom {id}"
        self.async_write_ha_state()
