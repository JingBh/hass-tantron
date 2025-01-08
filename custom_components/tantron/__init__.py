from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .cloud import TantronCloud
from .const import PLATFORMS
from .coordinator import TantronCoordinator
from .error import TantronCloudError
from .typing import EntryRuntimeData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData]) -> bool:
    # 1. construct cloud instance and verify authentication
    _cloud = TantronCloud(hass, entry.data.get('token'), entry.data.get('household'))
    try:
        await _cloud.get_household()
    except TantronCloudError as e:
        raise ConfigEntryAuthFailed from e
    except Exception as e:
        raise ConfigEntryNotReady from e

    # 2. construct coordinator instance using the cloud
    _coordinator = TantronCoordinator(hass, entry, _cloud)
    await _coordinator.async_config_entry_first_refresh()

    # 3. save cloud and coordinator instances and forward setup to platforms
    entry.runtime_data = EntryRuntimeData(cloud=_cloud, coordinator=_coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData]) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData]) -> bool:
    return True
