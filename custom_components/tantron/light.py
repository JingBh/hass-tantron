from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.light import LightEntity, ColorMode

from .coordinator import TantronDeviceEntity

if TYPE_CHECKING:
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
        if device['type'] == 'light':
            entities.append(TantronLight(coordinator, device))
    async_add_entities(entities)


class TantronLight(TantronDeviceEntity, LightEntity):

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device, 'switch')

    @property
    def is_on(self) -> bool | None:
        if self.device_state is not None:
            return

    async def async_turn_on(self, **kwargs) -> None:
        await self._send_values('1')

    async def async_turn_off(self, **kwargs) -> None:
        await self._send_values('0')
