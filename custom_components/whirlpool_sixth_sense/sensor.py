"""Platform for sensor integration."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
# Local import hacking
from .whirlpool.oven import Oven, Cavity, CavityState
from .const import DOMAIN, BRAND

LOGGER = logging.getLogger(__name__)

# Mapped states
STATE_STANDBY = "Standby"
STATE_PREHEATING = "Preriscaldamento"
STATE_COOKING = "Cottura"
STATE_NOT_PRESENT = "Non Presente"

CAVITY_STATE_TO_HA = {
    CavityState.Standby: STATE_STANDBY,
    CavityState.Preheating: STATE_PREHEATING,
    CavityState.Cooking: STATE_COOKING,
    CavityState.NotPresent: STATE_NOT_PRESENT
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager = data["manager"]

    entities = []
    for oven in manager.ovens:
        entities.append(WhirlpoolOvenStateSensor(oven, Cavity.Upper, "Upper"))
        # Restored the read-only timer sensor in hh:mm:ss format as requested
        entities.append(WhirlpoolOvenTimerSensor(oven, Cavity.Upper, "Upper"))
        entities.append(WhirlpoolOvenCookTimeStatusSensor(oven, Cavity.Upper, "Upper"))
    
    async_add_entities(entities)

class WhirlpoolOvenStateSensor(SensorEntity):
    """Representation of an Oven State Sensor."""

    def __init__(self, oven: Oven, cavity: Cavity, cavity_name: str) -> None:
        """Initialize the sensor."""
        self._oven = oven
        self._cavity = cavity
        self._attr_name = f"{oven.name} Forno Stato"
        self._attr_unique_id = f"{oven.said}_{cavity_name}_state"

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
    def native_value(self):
        state = self._oven.get_cavity_state(self._cavity)
        return CAVITY_STATE_TO_HA.get(state, "Unknown")

class WhirlpoolOvenTimerSensor(SensorEntity):
    """Representation of an Oven Timer Sensor (hh:mm:ss)."""
    _attr_icon = "mdi:timer"

    def __init__(self, oven: Oven, cavity: Cavity, cavity_name: str) -> None:
        """Initialize the sensor."""
        self._oven = oven
        self._cavity = cavity
        self._attr_name = f"{oven.name} Forno Timer Display"
        self._attr_unique_id = f"{oven.said}_{cavity_name}_timer_display"

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
    def native_value(self):
        # The Oven class now handles the local countdown logic inside get_cook_time
        seconds = self._oven.get_cook_time(self._cavity)
        if seconds is None or seconds == 0:
            return "00:00:00"
        
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def should_poll(self) -> bool:
        # Poll every second to provide smooth countdown in HA
        state = self._oven.get_cavity_state(self._cavity)
        if state in [CavityState.Cooking, CavityState.Preheating]:
             return True
        return False

class WhirlpoolOvenCookTimeStatusSensor(SensorEntity):
    """Sensor for cooking cycle completion status."""
    _attr_icon = "mdi:progress-check"

    def __init__(self, oven: Oven, cavity: Cavity, cavity_name: str) -> None:
        """Initialize the sensor."""
        self._oven = oven
        self._cavity = cavity
        self._attr_name = f"{oven.name} Fine cottura"
        self._attr_unique_id = f"{oven.said}_{cavity_name}_cook_time_status"

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
    def native_value(self):
        state = self._oven.get_cook_time_state(self._cavity)
        if state == 3:
            return "Completato"
        if state == 1:
            return "In corso"
        return "Attesa"
