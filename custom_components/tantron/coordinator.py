from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import TYPE_CHECKING, Dict, TypedDict

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from typing import List, Optional
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from .cloud import TantronCloud
    from .typing import EntryRuntimeData

_LOGGER = logging.getLogger(__name__)


class TantronDevice(TypedDict):
    id: str
    type: Optional[str]
    name: Optional[str]
    area_id: Optional[str]
    config_id: str
    icon: Optional[str]
    connection: dict
    functions: List[dict]
    values: Optional[Dict[str, str]]
    info: DeviceInfo
    updated_at: Optional[int]  # ns timestamp of last update, used for change detection


class TantronCoordinator(DataUpdateCoordinator[Dict[str, TantronDevice]]):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData], cloud: TantronCloud):
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=timedelta(hours=1))
        self.cloud = cloud
        self.gateway: Optional[dict] = None
        self.gateway_info: Optional[DeviceInfo] = None
        self.areas: Dict[str, str] = {}
        self.devices: Dict[str, TantronDevice] = {}
        self.device_master_ids: List[str] = []
        self.subscription_task: Optional[asyncio.Task] = None

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
        result: Dict[str, str] = {}
        floors = await self.cloud.get_areas()
        for floor in floors:
            for area in floor.get('areaList', []):
                name = area['name']
                if len(floors) > 1:
                    name = f'{floor["name"]}-{name}'
                result[area['id']] = name
        self.areas = result

    async def _load_devices(self):
        result: Dict[str, TantronDevice] = {}
        master_ids = set()

        for device in await self.cloud.get_devices():
            device_id = f'{device["masterId"]}.{device["id"]}'
            master_ids.add(device['masterId'])
            result[device_id] = TantronDevice(
                id=device_id,
                type=device.get('type'),
                name=device.get('name'),
                area_id=device.get('area'),
                config_id=device['id'],
                icon=device.get('icon'),
                connection={
                    'deviceConfigId': device['id'],
                    'configVersion': device['configVersion'],
                    'masterId': device['masterId'],
                    'version': 0  # value unknown
                },
                functions=device.get('functionList', []),
                values=device.get('functionValues'),
                info=DeviceInfo(
                    identifiers={(DOMAIN, device_id)},
                    manufacturer='Tantron',
                    name=device.get('name'),
                    suggested_area=self.areas.get(device.get('area', '')),
                    via_device=(DOMAIN, self.gateway['id'])
                ),
                updated_at=time.time_ns()
            )

        self.devices = result
        self.device_master_ids = list(master_ids)

        if self.subscription_task is not None:
            self.subscription_task.cancel()
        self.subscription_task = self.config_entry.async_create_background_task(
            self.hass,
            self._async_subscribe_data(),
            'tantron_subscription_task'
        )

    async def _async_update_data(self):
        _LOGGER.debug('Updating Tantron data')
        await self._load_gateway()
        await self._load_devices()
        self.data = self.devices

    def get_device(self, device_id: str) -> Optional[dict]:
        if device_id == self.gateway['id']:
            return self.gateway
        return self.devices.get(device_id)

    async def _async_subscribe_data(self):
        while True:
            try:
                if not self.devices:
                    await asyncio.sleep(1)
                    continue

                connections = [device['connection'] for device in self.devices.values()]
                for item in await self.cloud.get_state(connections):
                    if not item.get('deviceConfigId'):
                        continue

                    for possible_master_id in self.device_master_ids:
                        device_id = f'{possible_master_id}.{item["deviceConfigId"]}'
                        if device_id in self.devices:
                            self.devices[device_id]['connection']['version'] = item.get('version', 0)

                            values = item.get('function')
                            if values is None:
                                self.devices[device_id]['values'] = None
                            elif self.devices[device_id]['values'] is None:
                                self.devices[device_id]['values'] = values
                            else:
                                self.devices[device_id]['values'].update(values)

                            self.devices[device_id]['updated_at'] = time.time_ns()

                self.async_set_updated_data(self.devices)
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                return

            except:
                _LOGGER.warning('Tantron data subscription interrupted, retrying in 5 seconds', exc_info=True)
                await asyncio.sleep(5)


class TantronDeviceEntity(CoordinatorEntity[TantronCoordinator]):

    _attr_has_entity_name = True

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice, function_name: Optional[str] = None):
        # for multi-function entities, set `function_name` to `None`
        super().__init__(coordinator)
        self.device_id = device['id']
        self.device_state = device
        self.device_updated_at: Optional[int] = None
        self.function_name = function_name
        self.function_info: Dict[str, dict] = {}
        self.function_state: Optional[str | Dict[str, str]] = None
        for function in device['functions']:
            if function_name is None or function['type'] == function_name:
                self.function_info[function['type']] = function

    @property
    def available(self) -> bool:
        return self.device_state['values'] is not None

    @property
    def unique_id(self):
        if self.function_name is not None:
            return f'{self.device_id}.{self.function_name}'
        else:
            return self.device_id

    @property
    def name(self) -> Optional[str]:
        if self.function_name is not None:
            return self.function_info.get(self.function_name, {}).get('name')
        return self.device_state.get('name')

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        if self.device_state is not None:
            return self.device_state['info']
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._update_function_state()

    @callback
    def _handle_coordinator_update(self):
        new_state = self.coordinator.get_device(self.device_id)
        if new_state is not None and self.device_updated_at != new_state['updated_at']:
            self.device_state = new_state
            self._update_function_state()
            self.async_write_ha_state()

    def _update_function_state(self):
        if self.device_state['values'] is not None:
            if self.function_name is not None:
                self.function_state = self.device_state['values'].get(self.function_name)
            else:
                self.function_state = self.device_state['values']
        else:
            self.function_state = None
        self.device_updated_at = self.device_state['updated_at']
        _LOGGER.debug('New function state for %s: %s', self.device_id, self.device_state['values'])

    async def _send_values(self, values: str | Dict[str, str]):
        commands = []
        if not isinstance(values, dict) and self.function_name is not None:
            values = {
                self.function_name: str(values)
            }
        for key, value in values.items():
            if not self.function_info.get(key, {}).get('sendList'):
                continue
            send_info = self.function_info[key]['sendList'][0]
            commands.append({
                'dataType': send_info.get('dataType'),
                'dataLength': send_info.get('dataLength'),
                'addr': send_info.get('addr'),
                'protocolType': send_info.get('protocolType'),
                'value': value,
                'sleep': send_info.get('sleep'),
                'type': key
            })
        if commands:
            await self.coordinator.cloud.put_state(self.device_state['connection'], commands)
