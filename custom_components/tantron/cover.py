from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature

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
        if device['type'] == 'curtain':
            entities.append(TantronCurtain(coordinator, device))
    async_add_entities(entities)


class TantronCurtain(TantronDeviceEntity, CoverEntity):

    _attr_device_class = CoverDeviceClass.CURTAIN
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device)
        # Curtains have no state feedback from the cloud at all, so track the
        # last command locally to drive the UI optimistically.
        self._optimistic_closed: Optional[bool] = None

    @property
    def is_closed(self) -> Optional[bool]:
        if self.function_state is not None and 'switch' in self.function_state:
            return self.function_state['switch'] == '1'
        return self._optimistic_closed

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._send_values({
            'switch': '1'
        })
        self._optimistic_closed = True
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._send_values({
            'switch': '0'
        })
        self._optimistic_closed = False
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._send_values({
            'stop': '1'
        })
