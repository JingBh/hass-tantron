from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TantronCoordinator, TantronDeviceEntity

if TYPE_CHECKING:
    from typing import Optional, List
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity import Entity
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .coordinator import TantronDevice
    from .typing import EntryRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry[EntryRuntimeData],
                            async_add_entities: AddEntitiesCallback):
    coordinator = entry.runtime_data['coordinator']
    entities: List[Entity] = [GatewayOnlineSensor(coordinator)]
    for device_id, device in coordinator.devices.items():
        if device['type'] == 'secuSensor' and device['icon'] == 'icon_secusensor_02':
            entities.append(TantronMotionSensor(coordinator, device))
    async_add_entities(entities)


class GatewayOnlineSensor(CoordinatorEntity[TantronCoordinator], BinarySensorEntity):
    _attr_unique_id = f'gateway.online'
    _attr_has_entity_name = True
    _attr_translation_key = 'gateway_online'
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: TantronCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._state: Optional[dict] = coordinator.gateway

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.gateway != self._state:
            self._state = self.coordinator.gateway
            self.async_write_ha_state()

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        return self.coordinator.gateway_info

    @property
    def is_on(self) -> Optional[bool]:
        if self._state is not None:
            if self._state.get('onlineState') == 0:
                return False
            if self._state.get('onlineState') == 1:
                return True
        return None


class TantronMotionSensor(TantronDeviceEntity, BinarySensorEntity):

    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device, 'status')

    @property
    def is_on(self) -> Optional[bool]:
        if self.function_state is not None:
            return self.function_state == '1'
        return None
