import logging
import time
from enum import Enum

from .appliance import Appliance

LOGGER = logging.getLogger(__name__)

ATTR_DISPLAY_BRIGHTNESS = "Sys_DisplaySetBrightnessPercent"
ATTR_CONTROL_LOCK = "Sys_OperationSetControlLock"
ATTR_SABBATH_MODE = "Sys_OperationSetSabbathModeEnabled"

ATTR_POSTFIX_DOOR_OPEN_STATUS = "OpStatusDoorOpen"
ATTR_POSTFIX_LIGHT_STATUS = "DisplaySetLightOn"
ATTR_POSTFIX_TARGET_TEMP = "CycleSetTargetTemp"
ATTR_POSTFIX_TEMP = "DisplStatusDisplayTemp"
ATTR_POSTFIX_RAW_TEMP = "OpStatusRawTemp" # New mapping for internal temp
ATTR_POSTFIX_COOK_TIME = "TimeSetCookTimeSet"
ATTR_POSTFIX_STATUS_STATE = "OpStatusState"
ATTR_POSTFIX_COOK_TIME_STATE = "OpStatusCookTimeState" # New mapping
ATTR_POSTFIX_COOK_MODE = "CycleSetCommonMode"
ATTR_POSTFIX_FROZEN_BAKE = "CycleSetFrozenBakeFood"
ATTR_POSTFIX_MULTI_RACK = "CycleSetMultiRackFood"
ATTR_POSTFIX_CULINARY_ID = "CulinaryCtrSetId"
ATTR_POSTFIX_MEAT_PROBE_STATUS = "AlertStatusMeatProbePluggedIn"
ATTR_POSTFIX_MEAT_PROBE_TARGET_TEMP = "CycleSetMeatProbeTargetTemp"
ATTR_POSTFIX_SET_OPERATION = "OpSetOperations"

ATTRVAL_CAVITY_STATE_STANDBY = "0"
ATTRVAL_CAVITY_STATE_PREHEATING = "1"
ATTRVAL_CAVITY_STATE_COOKING = "2"
ATTRVAL_CAVITY_STATE_NOT_PRESENT = "4"

ATTRVAL_CAVITY_OPERATION_CANCEL = "1"
ATTRVAL_CAVITY_OPERATION_START = "2"
ATTRVAL_CAVITY_OPERATION_MODIFY = "4"
ATTRVAL_CAVITY_OPERATION_PAUSE = "5"

ATTRVAL_COOK_MODE_STANDBY = "0"
ATTRVAL_COOK_MODE_RAPID_PREHEAT = "1"
ATTRVAL_COOK_MODE_BAKE = "2"
ATTRVAL_COOK_MODE_FORCED_AIR = "14" # Updated from 3 based on log
ATTRVAL_COOK_MODE_CONVECT_BAKE = "6"
ATTRVAL_COOK_MODE_BROIL = "8"
ATTRVAL_COOK_MODE_CONVECT_BROIL = "9"
ATTRVAL_COOK_MODE_STEAM = "14"
ATTRVAL_COOK_MODE_CONVECT_ROAST = "16"
ATTRVAL_COOK_MODE_RISING = "19"
ATTRVAL_COOK_MODE_KEEP_WARM = "24"
# Removed AirFry (41) as user confirmed not supported

ATTR_POSTFIX_KITCHEN_TIMER_TIME_REMAINING = "StatusTimeRemaining"
ATTR_POSTFIX_KITCHEN_TIMER_STATUS = "StatusState"
ATTR_POSTFIX_KITCHEN_TIMER_SET_TIME = "SetTimeSet"
ATTR_POSTFIX_KITCHEN_TIMER_SET_OPS = "SetOperations"

ATTRVAL_KITCHEN_TIMER_STATE_STANDBY = "0"
ATTRVAL_KITCHEN_TIMER_STATE_RUNNING = "1"
ATTRVAL_KITCHEN_TIMER_STATE_COMPLETED = "3"

ATTRVAL_KITCHEN_TIMER_OPERATION_CANCEL = "1"
ATTRVAL_KITCHEN_TIMER_OPERATION_START = "2"


class Cavity(Enum):
    Upper = 0
    Lower = 1


CAVITY_PREFIX_MAP = {Cavity.Upper: "OvenUpperCavity", Cavity.Lower: "OvenLowerCavity"}


class CookMode(Enum):
    Standby = 0
    RapidPreheat = 1
    Bake = 2
    ForcedAir = 3
    ConvectBake = 6
    Broil = 8
    ConvectBroil = 9
    Steam = 14
    ConvectRoast = 16
    Rising = 19
    KeepWarm = 24


COOK_MODE_MAP = {
    CookMode.Standby: ATTRVAL_COOK_MODE_STANDBY,
    CookMode.RapidPreheat: ATTRVAL_COOK_MODE_RAPID_PREHEAT,
    CookMode.Bake: ATTRVAL_COOK_MODE_BAKE,
    CookMode.ForcedAir: ATTRVAL_COOK_MODE_FORCED_AIR,
    CookMode.ConvectBake: ATTRVAL_COOK_MODE_CONVECT_BAKE,
    CookMode.Broil: ATTRVAL_COOK_MODE_BROIL,
    CookMode.ConvectBroil: ATTRVAL_COOK_MODE_CONVECT_BROIL,
    CookMode.Steam: ATTRVAL_COOK_MODE_STEAM,
    CookMode.ConvectRoast: ATTRVAL_COOK_MODE_CONVECT_ROAST,
    CookMode.Rising: ATTRVAL_COOK_MODE_RISING,
    CookMode.KeepWarm: ATTRVAL_COOK_MODE_KEEP_WARM,
}


class CookOperation(Enum):
    Cancel = 1
    Start = 2
    Modify = 4
    Pause = 5


COOK_OPERATION_MAP = {
    CookOperation.Cancel: ATTRVAL_CAVITY_OPERATION_CANCEL,
    CookOperation.Start: ATTRVAL_CAVITY_OPERATION_START,
    CookOperation.Modify: ATTRVAL_CAVITY_OPERATION_MODIFY,
    CookOperation.Pause: ATTRVAL_CAVITY_OPERATION_PAUSE,
}


class CavityState(Enum):
    Standby = 0
    Preheating = 1
    Cooking = 2
    NotPresent = 4


CAVITY_STATE_MAP = {
    CavityState.Standby: ATTRVAL_CAVITY_STATE_STANDBY,
    CavityState.Preheating: ATTRVAL_CAVITY_STATE_PREHEATING,
    CavityState.Cooking: ATTRVAL_CAVITY_STATE_COOKING,
    CavityState.NotPresent: ATTRVAL_CAVITY_STATE_NOT_PRESENT,
}


class KitchenTimerState(Enum):
    Standby = 0
    Running = 1
    Completed = 3


KITCHEN_TIMER_STATE_MAP = {
    KitchenTimerState.Standby: ATTRVAL_KITCHEN_TIMER_STATE_STANDBY,
    KitchenTimerState.Running: ATTRVAL_KITCHEN_TIMER_STATE_RUNNING,
    KitchenTimerState.Completed: ATTRVAL_KITCHEN_TIMER_STATE_COMPLETED,
}


class KitchenTimerOperations(Enum):
    Cancel = 1
    Start = 2


KITCHEN_TIMER_OPERATIONS_MAP = {
    KitchenTimerOperations.Cancel: ATTRVAL_KITCHEN_TIMER_OPERATION_CANCEL,
    KitchenTimerOperations.Start: ATTRVAL_KITCHEN_TIMER_OPERATION_START,
}


class KitchenTimer:
    def __init__(self, appliance: Appliance, timer_id: int = 1):
        self._timer_id = timer_id
        self._appliance = appliance
        self._attr_prefix = f"KitchenTimer{timer_id:02d}_"

    def get_total_time(self):
        return self._appliance._get_attribute(
            self._attr_prefix + ATTR_POSTFIX_KITCHEN_TIMER_SET_TIME
        )

    def get_remaining_time(self):
        return self._appliance._get_attribute(
            self._attr_prefix + ATTR_POSTFIX_KITCHEN_TIMER_TIME_REMAINING
        )

    def get_state(self):
        state_raw = self._appliance._get_attribute(
            self._attr_prefix + ATTR_POSTFIX_KITCHEN_TIMER_STATUS
        )
        for k, v in KITCHEN_TIMER_STATE_MAP.items():
            if v == state_raw:
                return k
        LOGGER.error("Unknown kitchen timer state: " + str(state_raw))
        return None

    async def set_timer(
        self,
        timer_time: int,
        operation: KitchenTimerOperations = KitchenTimerOperations.Start,
    ) -> bool:
        return await self._appliance.send_attributes(
            {
                self._attr_prefix + ATTR_POSTFIX_KITCHEN_TIMER_SET_TIME: str(
                    timer_time
                ),
                self._attr_prefix
                + ATTR_POSTFIX_KITCHEN_TIMER_SET_OPS: KITCHEN_TIMER_OPERATIONS_MAP[
                    operation
                ],
            }
        )

    async def cancel_timer(self) -> bool:
        return await self._appliance.send_attributes(
            {
                self._attr_prefix
                + ATTR_POSTFIX_KITCHEN_TIMER_SET_OPS: KITCHEN_TIMER_OPERATIONS_MAP[
                    KitchenTimerOperations.Cancel
                ]
            }
        )


class Oven(Appliance):
    def get_meat_probe_status(self, cavity: Cavity = Cavity.Upper):
        return self.attr_value_to_bool(
            self._get_attribute(
                CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_MEAT_PROBE_STATUS
            )
        )

    def get_door_opened(self, cavity: Cavity = Cavity.Upper):
        return self.attr_value_to_bool(
            self._get_attribute(
                CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_DOOR_OPEN_STATUS
            )
        )

    def get_display_brightness_percent(self) -> int | None:
        brightness = self._get_attribute(ATTR_DISPLAY_BRIGHTNESS)
        return int(brightness) if brightness is not None else None

    async def set_display_brightness_percent(self, pct: int) -> bool:
        return await self.send_attributes({ATTR_DISPLAY_BRIGHTNESS: str(pct)})

    def get_cook_time(self, cavity: Cavity = Cavity.Upper):
        if not hasattr(self, "_desired_cook_time"):
             self._desired_cook_time = {Cavity.Upper: 0, Cavity.Lower: 0}
        if not hasattr(self, "_timer_updated_at"):
             self._timer_updated_at = {Cavity.Upper: 0, Cavity.Lower: 0}
        if not hasattr(self, "_timer_val"):
             self._timer_val = {Cavity.Upper: 0, Cavity.Lower: 0}
        if not hasattr(self, "_timer_preserved"):
             self._timer_preserved = {Cavity.Upper: False, Cavity.Lower: False}

        time_raw = self._get_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_COOK_TIME
        )
        server_seconds = int(time_raw) if time_raw is not None else 0
        state = self.get_cavity_state(cavity)
        
        # If server says 0 and we are in standby
        if server_seconds == 0 and state == CavityState.Standby:
             # If we explicitly preserved it, return the preserved value
             if self._timer_preserved[cavity]:
                  return self._desired_cook_time[cavity]
                  
             # Otherwise, it's a natural/manual stop, so reset
             self._desired_cook_time[cavity] = 0
             self._timer_val[cavity] = 0
             return 0

        # If server says 0 but we aren't cooking, OR we just started, use our desired time
        if server_seconds == 0:
             return self._desired_cook_time[cavity]

        # Sync local tracking with server
        if server_seconds != self._timer_val[cavity]:
             self._timer_val[cavity] = server_seconds
             self._timer_updated_at[cavity] = time.time()
        
        # Calculate local countdown if cooking
        if state in [CavityState.Cooking, CavityState.Preheating] and server_seconds > 0:
             elapsed = time.time() - self._timer_updated_at[cavity]
             remaining = max(0, server_seconds - int(elapsed))
             # Update desired time to match current remaining for consistency
             self._desired_cook_time[cavity] = remaining
             return remaining

        return server_seconds

    def get_control_locked(self):
        return self.attr_value_to_bool(self._get_attribute(ATTR_CONTROL_LOCK))

    async def set_control_locked(self, on: bool) -> bool:
        return await self.send_attributes(
            {ATTR_CONTROL_LOCK: self.bool_to_attr_value(on)}
        )

    def get_light(self, cavity: Cavity = Cavity.Upper):
        return self.attr_value_to_bool(
            self._get_attribute(
                CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_LIGHT_STATUS
            )
        )

    async def set_light(self, on: bool, cavity: Cavity = Cavity.Upper) -> bool:
        return await self.send_attributes(
            {
                CAVITY_PREFIX_MAP[cavity]
                + "_"
                + ATTR_POSTFIX_LIGHT_STATUS: self.bool_to_attr_value(on)
            }
        )

    def get_temp(self, cavity: Cavity = Cavity.Upper):
        # Prefer raw internal sensor for current temperature
        raw_temp = self._get_int_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_RAW_TEMP
        )
        if raw_temp is not None and raw_temp > 0:
             return raw_temp / 10
        
        # Fallback to display temp (which might be target)
        reported_temp = self._get_int_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_TEMP
        )
        if reported_temp is None or reported_temp == 0:
            return None

        # temperatures are returned in 1/10ths of a degree Celsius
        return reported_temp / 10

    def get_target_temp(self, cavity: Cavity = Cavity.Upper):
        reported_temp = self._get_int_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_TARGET_TEMP
        )
        if reported_temp is None or reported_temp == 0:
            return None

        # temperatures are returned in 1/10ths of a degree Celsius
        return reported_temp / 10

    def get_cavity_state(self, cavity: Cavity = Cavity.Upper):
        state_raw = self._get_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_STATUS_STATE
        )
        for k, v in CAVITY_STATE_MAP.items():
            if v == state_raw:
                return k
        LOGGER.error("Unknown cavity state: " + str(state_raw))
        return None

    def get_oven_cavity_exists(self, cavity: Cavity):
        cavity_state = self.get_cavity_state(cavity=cavity)
        return cavity_state is not None and cavity_state != CavityState.NotPresent

    def get_kitchen_timer(self, timer_id=1):
        timer = KitchenTimer(appliance=self, timer_id=timer_id)
        return timer

    def get_cook_time_state(self, cavity: Cavity = Cavity.Upper) -> int:
        return self._get_int_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_COOK_TIME_STATE
        ) or 0

    def get_cook_mode(self, cavity: Cavity = Cavity.Upper):
        cook_mode_raw = self._get_attribute(
            CAVITY_PREFIX_MAP[cavity] + "_" + ATTR_POSTFIX_COOK_MODE
        )
        for k, v in COOK_MODE_MAP.items():
            if v == cook_mode_raw:
                return k
        LOGGER.error("Unknown cook mode: " + str(cook_mode_raw))
        return None

    async def set_cook(
        self,
        target_temp: float,
        mode: CookMode = CookMode.Bake,
        cavity: Cavity = Cavity.Upper,
        rapid_preheat: bool | None = None,
        meat_probe_target_temp: float | None = None,
        delay_cook: int | None = None,
        cook_time: int | None = None,
        operation_type: CookOperation = CookOperation.Start,
    ) -> bool:
        cavity_prefix = CAVITY_PREFIX_MAP[cavity] + "_"
        attrs: dict[str, str] = {
            cavity_prefix + ATTR_POSTFIX_COOK_MODE: COOK_MODE_MAP[mode],
            cavity_prefix + ATTR_POSTFIX_TARGET_TEMP: str(round(target_temp * 10)),
            cavity_prefix + ATTR_POSTFIX_SET_OPERATION: COOK_OPERATION_MAP[
                operation_type
            ],
        }
        if meat_probe_target_temp is not None:
            attrs[cavity_prefix + ATTR_POSTFIX_MEAT_PROBE_TARGET_TEMP] = str(
                round(meat_probe_target_temp * 10)
            )
        
        if cook_time is not None:
            attrs[cavity_prefix + ATTR_POSTFIX_COOK_TIME] = str(cook_time)

        if not hasattr(self, "_timer_preserved"):
             self._timer_preserved = {Cavity.Upper: False, Cavity.Lower: False}
        self._timer_preserved[cavity] = False

        return await self.send_attributes(attrs)

    async def set_frozen_bake(self, temp: float, food_type: int = 4, cavity: Cavity = Cavity.Upper, cook_time: int | None = None) -> bool:
        cavity_prefix = CAVITY_PREFIX_MAP[cavity] + "_"
        attrs = {
            cavity_prefix + ATTR_POSTFIX_FROZEN_BAKE: str(food_type),
            cavity_prefix + ATTR_POSTFIX_TARGET_TEMP: str(round(temp * 10)),
            cavity_prefix + ATTR_POSTFIX_SET_OPERATION: COOK_OPERATION_MAP[CookOperation.Start]
        }
        if cook_time is not None:
            attrs[cavity_prefix + ATTR_POSTFIX_COOK_TIME] = str(cook_time)
        
        self._timer_preserved[cavity] = False
        return await self.send_attributes(attrs)

    async def set_cook_4(self, temp: float, food_type: int = 2, cavity: Cavity = Cavity.Upper, cook_time: int | None = None) -> bool:
        cavity_prefix = CAVITY_PREFIX_MAP[cavity] + "_"
        attrs = {
            cavity_prefix + ATTR_POSTFIX_MULTI_RACK: str(food_type),
            cavity_prefix + ATTR_POSTFIX_TARGET_TEMP: str(round(temp * 10)),
            cavity_prefix + ATTR_POSTFIX_SET_OPERATION: COOK_OPERATION_MAP[CookOperation.Start]
        }
        if cook_time is not None:
            attrs[cavity_prefix + ATTR_POSTFIX_COOK_TIME] = str(cook_time)
        
        self._timer_preserved[cavity] = False
        return await self.send_attributes(attrs)

    async def set_culinary_cycle(self, cycle_id: int, temp: float | None = None, cavity: Cavity = Cavity.Upper, cook_time: int | None = None, **kwargs) -> bool:
        cavity_prefix = CAVITY_PREFIX_MAP[cavity] + "_"
        attrs = {
            cavity_prefix + ATTR_POSTFIX_CULINARY_ID: str(cycle_id),
            cavity_prefix + ATTR_POSTFIX_SET_OPERATION: COOK_OPERATION_MAP[CookOperation.Start]
        }
        if temp:
             attrs[cavity_prefix + ATTR_POSTFIX_TARGET_TEMP] = str(round(temp * 10))
        
        if cook_time is not None:
             attrs[cavity_prefix + ATTR_POSTFIX_COOK_TIME] = str(cook_time)
        
        self._timer_preserved[cavity] = False
        
        # Map common kwargs to attribute names (Case Sensitive based on APK)
        if "weight" in kwargs:
             attrs[cavity_prefix + "Weight"] = str(kwargs["weight"])
        if "doneness" in kwargs:
             attrs[cavity_prefix + "Doneness"] = str(kwargs["doneness"])
        if "food_type" in kwargs:
             attrs[cavity_prefix + "FoodType"] = str(kwargs["food_type"])
        if "flexi_cook" in kwargs:
             attrs[cavity_prefix + "FlexiCook"] = "1" if kwargs["flexi_cook"] else "0"
        if "steam_level" in kwargs:
             attrs[cavity_prefix + "SteamLevel"] = str(kwargs["steam_level"])
        
        if "steam_level" in kwargs:
             attrs[cavity_prefix + "SteamLevel"] = str(kwargs["steam_level"])
        
        # Allow passing arbitrary attributes prefixed with "attr_"
        for k, v in kwargs.items():
            if k.startswith("attr_"):
                attrs[k.replace("attr_", "")] = str(v)

        return await self.send_attributes(attrs)

    async def set_cook_duration(self, seconds: int, cavity: Cavity = Cavity.Upper) -> bool:
        if not hasattr(self, "_desired_cook_time"):
             self._desired_cook_time = {Cavity.Upper: 0, Cavity.Lower: 0}
        if not hasattr(self, "_timer_updated_at"):
             self._timer_updated_at = {Cavity.Upper: 0, Cavity.Lower: 0}
        if not hasattr(self, "_timer_val"):
             self._timer_val = {Cavity.Upper: 0, Cavity.Lower: 0}

        self._desired_cook_time[cavity] = seconds
        self._timer_val[cavity] = seconds
        self._timer_updated_at[cavity] = time.time()

        cavity_prefix = CAVITY_PREFIX_MAP[cavity] + "_"
        attrs = {
            cavity_prefix + ATTR_POSTFIX_COOK_TIME: str(seconds),
        }
        
        # Only send modify operation if currently cooking
        state = self.get_cavity_state(cavity)
        if state in [CavityState.Cooking, CavityState.Preheating]:
             attrs[cavity_prefix + ATTR_POSTFIX_SET_OPERATION] = COOK_OPERATION_MAP[CookOperation.Modify]
             
        return await self.send_attributes(attrs)

    async def stop_cook(self, cavity: Cavity = Cavity.Upper, reset_timer: bool = True) -> bool:
        if not hasattr(self, "_timer_preserved"):
             self._timer_preserved = {Cavity.Upper: False, Cavity.Lower: False}
        
        if reset_timer:
            if hasattr(self, "_desired_cook_time"):
                 self._desired_cook_time[cavity] = 0
            if hasattr(self, "_timer_val"):
                 self._timer_val[cavity] = 0
            self._timer_preserved[cavity] = False
        else:
            self._timer_preserved[cavity] = True
             
        return await self.send_attributes(
            {
                CAVITY_PREFIX_MAP[cavity]
                + "_"
                + ATTR_POSTFIX_SET_OPERATION: COOK_OPERATION_MAP[CookOperation.Cancel]
            }
        )

    def get_sabbath_mode(self):
        return self.attr_value_to_bool(self._get_attribute(ATTR_SABBATH_MODE))

    async def set_sabbath_mode(self, on: bool) -> bool:
        return await self.send_attributes(
            {ATTR_SABBATH_MODE: self.bool_to_attr_value(on)}
        )
