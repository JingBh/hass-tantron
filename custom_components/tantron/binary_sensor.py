from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import DOMAIN as ENTITY_DOMAIN, BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TantronCoordinator

if TYPE_CHECKING:
    from typing import Optional
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .typing import EntryRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry[EntryRuntimeData],
                            async_add_entities: AddEntitiesCallback):
    async_add_entities([
        GatewayOnlineSensor(entry.runtime_data['coordinator'])
    ])


class GatewayOnlineSensor(CoordinatorEntity[TantronCoordinator], BinarySensorEntity):
    _attr_unique_id = f'{ENTITY_DOMAIN}.gateway_online'
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
    def device_info(self) -> DeviceInfo | None:
        return self.coordinator.gateway_info

    @property
    def is_on(self) -> bool | None:
        if self._state is not None:
            if self._state.get('onlineState') == 0:
                return False
            if self._state.get('onlineState') == 1:
                return True
        return None
