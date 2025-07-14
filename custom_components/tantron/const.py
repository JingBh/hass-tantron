from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = 'tantron'

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.FAN,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.WEATHER
]
