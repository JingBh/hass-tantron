from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.util.percentage import ranged_value_to_percentage, percentage_to_ranged_value
from homeassistant.util.scaling import int_states_in_range

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
        if device['type'] == 'freshAir':
            entities.append(TantronAirPurifier(coordinator, device))
    async_add_entities(entities)


class TantronAirPurifier(TantronDeviceEntity, FanEntity):

    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.SET_SPEED

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device)
        self._speed_range = (1, 3)

    @property
    def is_on(self) -> Optional[bool]:
        if self.function_state is not None and 'switch' in self.function_state:
            return self.function_state['switch'] == '1'
        return None

    @property
    def percentage(self) -> Optional[int]:
        if self.function_state is not None and 'speed' in self.function_state:
            try:
                current_speed = int(self.function_state['speed'])
                return ranged_value_to_percentage(self._speed_range, current_speed)
            except ValueError:
                pass
        return None

    async def async_turn_on(self, percentage: Optional[int] = None, **kwargs) -> None:
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        await self._send_values({
            'switch': '1'
        })

    async def turn_off(self, **kwargs) -> None:
        await self._send_values({
            'switch': '0'
        })

    async def async_set_percentage(self, percentage: int) -> None:
        value_in_range = math.ceil(percentage_to_ranged_value(self._speed_range, percentage))
        await self._send_values({
            'switch': '1',
            'speed': str(value_in_range)
        })

    @property
    def speed_count(self) -> int:
        return int_states_in_range(self._speed_range)
