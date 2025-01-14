from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.device_registry import DeviceEntry
    from .typing import EntryRuntimeData


TO_REDACT = [
    'phone',
    'password',
    'token',
    'household'
]


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData]) -> dict:
    return {
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "devices": async_redact_data(entry.runtime_data['coordinator'].devices, TO_REDACT)
    }


async def async_get_device_diagnostics(hass: HomeAssistant, entry: ConfigEntry[EntryRuntimeData], device: DeviceEntry) -> dict:
    for identifier in device.identifiers:
        device = entry.runtime_data['coordinator'].get_device(identifier[1])
        if device:
            return async_redact_data(device, TO_REDACT)
    return {}
