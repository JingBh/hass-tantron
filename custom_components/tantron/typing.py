from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Callable, List
    from .cloud import TantronCloud
    from .coordinator import TantronCoordinator


class EntryRuntimeData(TypedDict):
    cloud: TantronCloud
    coordinator: TantronCoordinator
    handlers: List[Callable[[], None]]
