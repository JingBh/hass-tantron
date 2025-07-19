from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import Event
    from .cloud import TantronCloud

_LOGGER = logging.getLogger(__name__)


async def handle_put_state(event: Event[dict], cloud: TantronCloud):
    """
    This event handler enables the user to send custom states to the Tantron cloud.
    Event data should be exactly what the put state API expects.

    For example,
    to trigger the action to dim the control panel from the scene in the app,
    the event data should look like this:
    ```yaml
    deviceConfigId: '37416'  # ets id
    configVersion: 75        # version of household config, can be found in any device's configuration
    masterId: '{master_id}'
    cmd:
      - dataType: '0'
        dataValueList:
          - '0'
        dataLength: '0'
        ext: null
        addr: 1/5/255
        protocolType: KNX
        sleep: 0
        type: activate       # 'type' taken from the function of the ets that you want to trigger
        value: '0'           # value to send, can be taken from the `dataValueList`
    ```
    """
    connection = event.data.copy()
    cmd = connection.pop('cmd')
    _LOGGER.debug(f'received put_state event: {connection=}, {cmd=}')
    await cloud.put_state(connection, cmd)
