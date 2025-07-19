from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .cloud import TantronCloud
from .const import PLATFORMS, EVENT_PUT_STATE
from .coordinator import TantronCoordinator
from .error import TantronCloudError
from .event import handle_put_state
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
    entry.runtime_data = EntryRuntimeData(cloud=_cloud, coordinator=_coordinator, handlers=[])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 4. register custom event handlers
    cancel = hass.bus.async_listen(EVENT_PUT_STATE, functools.partial(handle_put_state, cloud=_cloud))
    entry.runtime_data['handlers'].append(cancel)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData]) -> bool:
    # 1. cancel all event handlers
    for cancel in entry.runtime_data['handlers']:
        cancel()

    # 2. unload all platforms
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData]) -> bool:
    return True
