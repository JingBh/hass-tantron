from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import UnitOfTemperature, UnitOfSpeed, UnitOfLength, UnitOfPressure
from homeassistant.components.weather import DOMAIN as ENTITY_DOMAIN, WeatherEntity, WeatherEntityFeature, Forecast

if TYPE_CHECKING:
    from typing import Optional, List
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .cloud import TantronCloud

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=20)

# The following definitions are adapted from `cheny95/qweather`, originally licensed under the GPL-3.0
# https://github.com/cheny95/qweather/blob/ba3f30b/custom_components/qweather/condition.py
# https://developers.home-assistant.io/docs/core/entity/weather#recommended-values-for-state-and-condition
# https://dev.qweather.com/docs/resource/icons/

CLEAR_NIGHT = 'clear-night'  # 晴（夜）
CLOUDY = 'cloudy'  # 阴
EXCEPTIONAL = 'exceptional'  # 未知
FOG = 'fog'  # 雾
HAIL = 'hail'  # 冰雹
LIGHTNING = 'lightning'  # 闪电
LIGHTNING_RAINY = 'lightning-rainy'  # 雷阵雨
PARTLY_CLOUDY = 'partlycloudy'  # 多云
POURING = 'pouring'  # 暴雨
RAINY = 'rainy'  # 雨
SNOWY = 'snowy'  # 雪
SNOWY_RAINY = 'snowy-rainy'  # 雨夹雪
SUNNY = 'sunny'  # 晴
WINDY = 'windy'  # 大风
WINDY_VARIANT = 'windy-variant'  # 大风（有云）

CONDITION_MAP = {
    '100': SUNNY,  # 晴
    '101': PARTLY_CLOUDY,  # 多云
    '102': PARTLY_CLOUDY,  # 少云
    '103': PARTLY_CLOUDY,  # 晴间多云
    '104': CLOUDY,  # 阴
    '150': CLEAR_NIGHT,  # 晴
    '151': PARTLY_CLOUDY,  # 多云
    '152': PARTLY_CLOUDY,  # 少云
    '153': PARTLY_CLOUDY,  # 夜间多云
    '300': RAINY,  # 阵雨
    '301': RAINY,  # 强阵雨
    '302': LIGHTNING_RAINY,  # 雷阵雨
    '303': LIGHTNING_RAINY,  # 强雷阵雨
    '304': HAIL,  # 雷阵雨伴有冰雹
    '305': RAINY,  # 小雨
    '306': RAINY,  # 中雨
    '307': POURING,  # 大雨
    '308': POURING,  # 极端降雨
    '309': RAINY,  # 毛毛雨/细雨
    '310': POURING,  # 暴雨
    '311': POURING,  # 大暴雨
    '312': POURING,  # 特大暴雨
    '313': RAINY,  # 冻雨
    '314': RAINY,  # 小到中雨
    '315': RAINY,  # 中到大雨
    '316': POURING,  # 大到暴雨
    '317': POURING,  # 暴雨到大暴雨
    '318': POURING,  # 大暴雨到特大暴雨
    '350': RAINY,  # 阵雨
    '351': POURING,  # 强阵雨
    '399': RAINY,  # 雨
    '400': SNOWY,  # 小雪
    '401': SNOWY,  # 中雪
    '402': SNOWY,  # 大雪
    '403': SNOWY,  # 暴雪
    '404': SNOWY_RAINY,  # 雨夹雪
    '405': SNOWY_RAINY,  # 雨雪天气
    '406': SNOWY_RAINY,  # 阵雨夹雪
    '407': RAINY,  # 阵雪
    '408': RAINY,  # 小到中雪
    '409': RAINY,  # 中到大雪
    '410': SNOWY,  # 大到暴雪
    '456': SNOWY_RAINY,  # 阵雨夹雪
    '457': RAINY,  # 阵雪
    '499': RAINY,  # 雪
    '500': FOG,  # 薄雾
    '501': FOG,  # 雾
    '502': FOG,  # 霾
    '503': FOG,  # 扬沙
    '504': FOG,  # 浮尘
    '507': FOG,  # 沙尘暴
    '508': FOG,  # 强沙尘暴
    '509': FOG,  # 浓雾
    '510': FOG,  # 强浓雾
    '511': FOG,  # 中度霾
    '512': FOG,  # 重度霾
    '513': FOG,  # 严重霾
    '514': FOG,  # 大雾
    '515': FOG,  # 特强浓雾
}


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry[TantronCloud],
                            async_add_entities: AddEntitiesCallback):
    async_add_entities([
        TantronWeatherEntity(entry.runtime_data)
    ], True)


class TantronWeatherEntity(WeatherEntity):
    _attr_unique_id = f'{ENTITY_DOMAIN}'
    _attr_has_entity_name = True
    _attr_translation_key = 'weather'
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self,
                 cloud: TantronCloud,
                 latitude: Optional[float] = None,
                 longitude: Optional[float] = None):
        self.cloud = cloud
        self.latitude = latitude
        self.longitude = longitude
        self.forecast_hourly = None
        self.forecast_hourly_expires_at = 0
        self.forecast_daily = None
        self.forecast_daily_expires_at = 0

    @property
    def native_apparent_temperature(self) -> Optional[float]:
        return self._attr_native_apparent_temperature

    @property
    def native_temperature(self) -> Optional[float]:
        return self._attr_native_temperature

    @property
    def native_dew_point(self) -> Optional[float]:
        return self._attr_native_dew_point

    @property
    def native_pressure(self) -> Optional[float]:
        return self._attr_native_pressure

    @property
    def humidity(self) -> Optional[float]:
        return self._attr_humidity

    @property
    def native_wind_speed(self) -> Optional[float]:
        return self._attr_native_wind_speed

    @property
    def wind_bearing(self) -> Optional[float | str]:
        return self._attr_wind_bearing

    @property
    def cloud_coverage(self) -> Optional[float]:
        return self._attr_cloud_coverage

    @property
    def uv_index(self) -> Optional[float]:
        return self._attr_uv_index

    @property
    def native_visibility(self) -> Optional[float]:
        return self._attr_native_visibility

    @property
    def condition(self) -> Optional[str]:
        return self._attr_condition

    async def async_update(self):
        await self.update_coordinates()

        data = await self.cloud.get_weather('now', self.latitude, self.longitude)
        if type(data) is not dict:
            _LOGGER.error(f'failed to parse weather data: {data}')
            return
        data = data.get('now', {})
        _LOGGER.debug(f'weather data: {data}')

        self._attr_native_temperature = float(data['temp'])
        if data.get('feelsLike'):
            self._attr_native_apparent_temperature = float(data['feelsLike'])
        self._attr_condition = CONDITION_MAP.get(data['icon'], EXCEPTIONAL)
        if data.get('wind360'):
            self._attr_wind_bearing = float(data['wind360'])
        if data.get('windSpeed'):
            self._attr_native_wind_speed = float(data['windSpeed'])
        if data.get('humidity'):
            self._attr_humidity = float(data['humidity'])
        if data.get('pressure'):
            self._attr_native_pressure = float(data['pressure'])
        if data.get('vis'):
            self._attr_native_visibility = float(data['vis'])
        if data.get('cloud'):
            self._attr_cloud_coverage = int(data['cloud'])
        if data.get('dew'):
            self._attr_native_dew_point = float(data['dew'])

    async def async_forecast_hourly(self) -> Optional[List[Forecast]]:
        await self.update_coordinates()

        if self.forecast_hourly_expires_at > time.time():
            return self.forecast_hourly

        result = []
        data = await self.cloud.get_weather('24hour', self.latitude, self.longitude)
        if type(data) is not dict or type(data.get('hourly')) is not list:
            _LOGGER.error(f'failed to parse weather data: {data}')
            return result
        _LOGGER.debug(f'weather data: {data["hourly"]}')

        for item in data['hourly']:
            forecast = Forecast(datetime=item['fxTime'])
            forecast['native_temperature'] = float(item['temp'])
            forecast['condition'] = CONDITION_MAP.get(item['icon'], EXCEPTIONAL)
            if item.get('wind360'):
                forecast['wind_bearing'] = float(item['wind360'])
            if item.get('windSpeed'):
                forecast['native_wind_speed'] = float(item['windSpeed'])
            if item.get('humidity'):
                forecast['humidity'] = float(item['humidity'])
            if item.get('precip'):
                forecast['native_precipitation'] = float(item['precip'])
            if item.get('pop'):
                forecast['precipitation_probability'] = int(item['pop'])
            if item.get('pressure'):
                forecast['native_pressure'] = float(item['pressure'])
            if item.get('cloud'):
                forecast['cloud_coverage'] = int(item['cloud'])
            if item.get('dew'):
                forecast['native_dew_point'] = float(item['dew'])
            result.append(forecast)

        self.forecast_hourly = result
        self.forecast_hourly_expires_at = time.time() + int(data.get('expireTime', 0))
        return result

    async def async_forecast_daily(self) -> Optional[List[Forecast]]:
        await self.update_coordinates()

        if self.forecast_daily_expires_at > time.time():
            return self.forecast_daily

        result = []
        data = await self.cloud.get_weather('7day', self.latitude, self.longitude)
        if type(data) is not dict or type(data.get('daily')) is not list:
            _LOGGER.error(f'failed to parse weather data: {data}')
            return result
        _LOGGER.debug(f'weather data: {data["daily"]}')

        for item in data['daily']:
            forecast = Forecast(datetime=item['fxDate'])
            forecast['native_temperature'] = float(item['tempMax'])
            forecast['native_templow'] = float(item['tempMin'])
            forecast['condition'] = CONDITION_MAP.get(item['iconDay'], EXCEPTIONAL)
            if item.get('wind360Day'):
                forecast['wind_bearing'] = float(item['wind360Day'])
            if item.get('windSpeedDay'):
                forecast['native_wind_speed'] = float(item['windSpeedDay'])
            if item.get('precip'):
                forecast['native_precipitation'] = float(item['precip'])
            if item.get('uvIndex'):
                forecast['uv_index'] = float(item['uvIndex'])
            if item.get('humidity'):
                forecast['humidity'] = float(item['humidity'])
            if item.get('pressure'):
                forecast['native_pressure'] = float(item['pressure'])
            if item.get('cloud'):
                forecast['cloud_coverage'] = int(item['cloud'])
            result.append(forecast)

        self.forecast_daily = result
        self.forecast_daily_expires_at = time.time() + int(data.get('expireTime', 0))
        return result

    async def update_coordinates(self):
        if not self.latitude or not self.longitude:
            self.latitude, self.longitude = await self.cloud.get_household_coordinates()
            self.forecast_hourly_expires_at = 0
            self.forecast_daily_expires_at = 0
