from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .cloud import TantronCloud
from .const import PLATFORMS
from .error import TantronCloudError

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[TantronCloud]) -> bool:
    _cloud = TantronCloud(hass, entry.data.get('token'), entry.data.get('household'))
    try:
        await _cloud.get_household()
    except TantronCloudError as e:
        raise ConfigEntryAuthFailed from e
    except Exception as e:
        raise ConfigEntryNotReady from e
    entry.runtime_data = _cloud

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry[TantronCloud]) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry[TantronCloud]) -> bool:
    return True
