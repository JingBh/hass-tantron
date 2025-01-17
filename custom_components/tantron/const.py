from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = 'tantron'

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.WEATHER
]
