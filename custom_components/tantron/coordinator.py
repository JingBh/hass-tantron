from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, TypedDict

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

if TYPE_CHECKING:
    from typing import Dict, List, Optional
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from .cloud import TantronCloud
    from .typing import EntryRuntimeData

_LOGGER = logging.getLogger(__name__)


class TantronDevice(TypedDict):
    id: str
    name: str
    area_id: str
    config_id: str
    connection: dict
    entities: List[dict]
    info: DeviceInfo


class TantronCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData], cloud: TantronCloud):
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=timedelta(hours=1))
        self.cloud = cloud
        self.gateway: Optional[dict] = None
        self.gateway_info: Optional[DeviceInfo] = None
        self.areas: Dict[str, str] = {}
        self.devices: List[dict] = []

    async def _async_setup(self) -> None:
        await self._load_gateway()
        await self._load_areas()
        await self._load_devices()

    async def _load_gateway(self):
        self.gateway = await self.cloud.get_gateway()
        self.gateway_info = DeviceInfo(
            identifiers={(DOMAIN, self.gateway['id'])},
            manufacturer='Tantron',
            model=self.gateway.get('model'),
            name=self.gateway.get('name'),
            serial_number=self.gateway.get('serialNo'),
            sw_version=self.gateway.get('versionName')
        )

    async def _load_areas(self):
        result = {}
        floors = await self.cloud.get_areas()
        for floor in floors:
            for area in floor.get('areaList', []):
                name = area['name']
                if len(floors) > 1:
                    name = f'{floor["name"]}-{name}'
                result[area['id']] = name
        self.areas = result

    async def _load_devices(self):
        self.devices = []
        for device in await self.cloud.get_devices():
            self.devices.append(TantronDevice(
                id=device['masterId'],
                name=device['name'],
                area_id=device['area'],
                config_id=device['id'],
                connection={
                    'deviceConfigId': device['id'],
                    'configVersion': device['configVersion'],
                    'masterId': device['masterId'],
                    'version': 0  # value unknown
                },
                entities=device.get('functionList', []),
                info=DeviceInfo(
                    identifiers={(DOMAIN, device['masterId'])},
                    default_manufacturer='Tantron',
                    name=device.get('name'),
                    suggested_area=self.areas.get(device['area']),
                    via_device=(DOMAIN, self.gateway['id'])
                )
            ))

    async def _async_update_data(self):
        await self._load_gateway()
