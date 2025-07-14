from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode, \
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH
from homeassistant.const import UnitOfTemperature, PRECISION_WHOLE

from .coordinator import TantronDeviceEntity

if TYPE_CHECKING:
    from typing import Optional
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .coordinator import TantronCoordinator, TantronDevice
    from .typing import EntryRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry[EntryRuntimeData],
                            async_add_entities: AddEntitiesCallback):
    coordinator = entry.runtime_data['coordinator']
    entities = []
    for device_id, device in coordinator.devices.items():
        if device['type'] == 'AC':
            entities.append(TantronAirConditioner(coordinator, device))
        elif device['type'] == 'heating':
            entities.append(TantronHeater(coordinator, device))
    async_add_entities(entities)


class TantronAirConditioner(TantronDeviceEntity, ClimateEntity):

    _attr_supported_features = (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE |
                                ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF)
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_max_temp = 29
    _attr_min_temp = 18
    _attr_target_temperature_step = PRECISION_WHOLE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device)
        self._hvac_mode_map = {
            '1': HVACMode.HEAT,
            '2': HVACMode.COOL,
            '3': HVACMode.DRY,
            '4': HVACMode.FAN_ONLY,
        }
        self._fan_mode_map = {
            '2': FAN_AUTO,
            '5': FAN_LOW,
            '4': FAN_MEDIUM,
            '3': FAN_HIGH,
        }

    @property
    def hvac_mode(self) -> Optional[HVACMode]:
        if self.function_state is None:
            return None
        if self.function_state.get('switch') == '0':
            return HVACMode.OFF
        return self._hvac_mode_map.get(self.function_state.get('mode'))

    @property
    def target_temperature(self) -> Optional[float]:
        if self.function_state is not None and 'targetTemp' in self.function_state:
            try:
                return float(self.function_state['targetTemp'])
            except ValueError:
                pass
        return None

    @property
    def fan_mode(self) -> Optional[str]:
        if self.function_state is not None and 'speed' in self.function_state:
            return self._fan_mode_map.get(self.function_state['speed'])
        return None

    @property
    def current_temperature(self) -> Optional[float]:
        if self.function_state is not None and 'tempSensor' in self.function_state:
            try:
                return float(self.function_state['tempSensor'])
            except ValueError:
                pass
        return None

    async def async_turn_on(self) -> None:
        await self._send_values({
            'switch': '1'
        })

    async def async_turn_off(self) -> None:
        await self._send_values({
            'switch': '0'
        })

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        mode = next((key for key, value in self._hvac_mode_map.items() if value == hvac_mode), None)
        if mode is not None:
            await self._send_values({
                'mode': mode,
                'switch': '1'
            })

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        mode = next((key for key, value in self._fan_mode_map.items() if value == fan_mode), None)
        if mode is not None:
            await self._send_values({
                'speed': mode
            })

    async def async_set_temperature(self, **kwargs) -> None:
        target_temp = kwargs.get('temperature')
        if target_temp is not None:
            try:
                target_temp = int(target_temp)
            except ValueError:
                return
            await self._send_values({
                'targetTemp': str(target_temp)
            })


class TantronHeater(TantronDeviceEntity, ClimateEntity):

    _attr_supported_features = (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON |
                                ClimateEntityFeature.TURN_OFF)
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_max_temp = 40
    _attr_min_temp = 20
    _attr_target_temperature_step = PRECISION_WHOLE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device)

    @property
    def hvac_mode(self) -> Optional[HVACMode]:
        if self.function_state is None:
            return None
        if self.function_state.get('switch') == '0':
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def target_temperature(self) -> Optional[float]:
        if self.function_state is not None and 'targetTemp' in self.function_state:
            try:
                return float(self.function_state['targetTemp'])
            except ValueError:
                pass
        return None

    async def async_turn_on(self) -> None:
        await self._send_values({
            'switch': '1'
        })

    async def async_turn_off(self) -> None:
        await self._send_values({
            'switch': '0'
        })

    async def async_set_temperature(self, **kwargs) -> None:
        target_temp = kwargs.get('temperature')
        if target_temp is not None:
            try:
                target_temp = int(target_temp)
            except ValueError:
                return
            await self._send_values({
                'targetTemp': str(target_temp)
            })
