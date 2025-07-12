from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, \
    PERCENTAGE, CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, CONCENTRATION_PARTS_PER_MILLION

from .coordinator import TantronDeviceEntity

if TYPE_CHECKING:
    from typing import Optional
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .coordinator import TantronCoordinator, TantronDevice
    from .typing import EntryRuntimeData

_LOGGER = logging.getLogger(__name__)

TANTRON_SENSOR_NAME_CLASS_MAP = {
    '温度': SensorDeviceClass.TEMPERATURE,
    '湿度': SensorDeviceClass.HUMIDITY,
    'PM2.5': SensorDeviceClass.PM25,
    'PM10': SensorDeviceClass.PM10,
    'CO2': SensorDeviceClass.CO2,
}

TANTRON_SENSOR_ICON_CLASS_MAP = {
    'icon_envsensor_01': SensorDeviceClass.TEMPERATURE,
    'icon_envsensor_02': SensorDeviceClass.HUMIDITY,
    'icon_envsensor_03': SensorDeviceClass.PM25,
    'icon_envsensor_04': SensorDeviceClass.PM10,
    'icon_envsensor_05': SensorDeviceClass.CO2,
}

TANTRON_SENSOR_UNIT_MAP = {
    SensorDeviceClass.TEMPERATURE: UnitOfTemperature.CELSIUS,
    SensorDeviceClass.HUMIDITY: PERCENTAGE,
    SensorDeviceClass.PM25: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    SensorDeviceClass.PM10: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    SensorDeviceClass.CO2: CONCENTRATION_PARTS_PER_MILLION
}


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry[EntryRuntimeData],
                            async_add_entities: AddEntitiesCallback):
    coordinator = entry.runtime_data['coordinator']
    entities = []
    for device_id, device in coordinator.devices.items():
        if device['type'] == 'envSensor':
            entities.append(TantronEnvSensor(coordinator, device))
    async_add_entities(entities)


class TantronEnvSensor(TantronDeviceEntity, SensorEntity):

    def __init__(self, coordinator: TantronCoordinator, device: TantronDevice):
        super().__init__(coordinator, device, 'value')

    @property
    def device_class(self) -> Optional[SensorDeviceClass]:
        if self.device_state['name'] in TANTRON_SENSOR_NAME_CLASS_MAP:
            return TANTRON_SENSOR_NAME_CLASS_MAP[self.device_state['name']]
        return TANTRON_SENSOR_ICON_CLASS_MAP.get(self.device_state.get('icon', ''))

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        return TANTRON_SENSOR_UNIT_MAP.get(self.device_class)

    @property
    def native_value(self):
        if self.function_state is not None:
            return float(self.function_state)
        return None
