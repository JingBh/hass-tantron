from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import DOMAIN as ENTITY_DOMAIN, BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

if TYPE_CHECKING:
    from typing import Optional
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .cloud import TantronCloud

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry[TantronCloud],
                            async_add_entities: AddEntitiesCallback):
    async_add_entities([
        GatewayOnlineSensor(entry.runtime_data)
    ], True)


class GatewayOnlineSensor(BinarySensorEntity):
    _attr_unique_id = f'{ENTITY_DOMAIN}.gateway_online'
    _attr_has_entity_name = True
    _attr_translation_key = 'gateway_online'
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = False

    def __init__(self, cloud: TantronCloud):
        self.cloud = cloud
        self._state: Optional[dict] = None

    @property
    def device_info(self) -> DeviceInfo | None:
        if self._state is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, self._state['id'])},
            manufacturer='Tantron',
            model=self._state.get('model'),
            name=self._state.get('name'),
            serial_number=self._state.get('serialNo'),
            sw_version=self._state.get('versionName')
        )

    @property
    def is_on(self) -> bool | None:
        if self._state is not None:
            if self._state.get('onlineState') == 0:
                return False
            if self._state.get('onlineState') == 1:
                return True
        return None

    async def async_update(self):
        self._state = await self.cloud.get_gateway()
