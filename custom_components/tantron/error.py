from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.exceptions import HomeAssistantError

if TYPE_CHECKING:
    from typing import Optional, Any


class TantronConnectionError(HomeAssistantError):
    pass


class TantronCloudError(HomeAssistantError):
    def __init__(self, code: int, message: Optional[str], data: Any = None, *args):
        super().__init__(f'cloud error: [{code}] {message or "unknown error"}', *args)
        self.code = code
        self.message = message or 'unknown error'
        self.data = data


class TantronAuthenticationError(TantronCloudError):
    pass
