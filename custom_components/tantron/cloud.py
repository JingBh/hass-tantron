from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from hashlib import sha256

from homeassistant.helpers.httpx_client import create_async_httpx_client

from .error import TantronAuthenticationError, TantronConnectionError, TantronCloudError

if TYPE_CHECKING:
    from typing import Optional, Dict, List, Tuple
    from homeassistant.core import HomeAssistant
    from httpx import AsyncClient, Response

_LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://smart.i-ttg.net/'
HEADER_TOKEN = 'access_token'
USER_AGENT = 'TantronAssistant/1.1.8 (iPhone; iOS 18.2; Scale/3.00)'

token_cache = {}


class TantronCloud:

    _session: Optional[AsyncClient] = None

    def __init__(self, hass: HomeAssistant, token: Optional[str] = None, household_id: Optional[str] = None):
        self.hass = hass
        self.token = token
        self.household_id = household_id

    async def _get_session(self) -> AsyncClient:
        if not self._session:
            self._session = create_async_httpx_client(self.hass)
            self._session.base_url = BASE_URL
            self._session.headers.update({
                'User-Agent': USER_AGENT
            })
        return self._session

    async def login(self, phone: str, password: str) -> str:
        """
        Authenticates with the Tantron cloud and returns the access token.
        Modifies the current instance to use the token in future requests.

        The WeChat WeApp login channel is used,
        so that this integration cannot be used together with the WeApp.
        Official Android / iOS app is not affected.
        """
        session = await self._get_session()

        # if the phone has a cached token, verify it
        if phone in token_cache:
            try:
                self.token = token_cache[phone]
                user = await self.get_user()
                if user is not None:
                    return self.token
            except Exception as e:
                _LOGGER.debug('error while trying to reuse cached token', exc_info=e)
            self.token = None
            del token_cache[phone]
            _LOGGER.debug('cached token is invalid')

        # if the password is not hashed, hash it
        if len(password) != 64:
            password = self.hash_password(password)

        try:
            response = await session.post('user-service/wei_xin_mini_program/login', json={
                'phone': phone,
                'password': password
            })
            data = self._read_response_json(response)
        except TantronCloudError as e:
            raise TantronAuthenticationError(e.code, e.message, e.data)

        self.token = data['accessToken']
        token_cache[phone] = self.token
        return data['accessToken']

    async def get_user(self) -> dict:
        session = await self._get_session()

        response = await session.get('user-service/user', headers={
            HEADER_TOKEN: self.token
        })
        return self._read_response_json(response)

    async def list_households(self) -> Dict[str, str]:
        session = await self._get_session()

        response = await session.get('user-service/normal/household/list', headers={
            HEADER_TOKEN: self.token
        })
        data = self._read_response_json(response)
        if type(data) is not list:
            return {}
        return {
            i['householdId']: i['householdName']
            for i in data
            if i.get('gatewayBound') is True
        }

    async def get_household(self, detailed: bool = False) -> dict:
        session = await self._get_session()

        if not self.household_id:
            raise ValueError('household id is not set')

        if detailed:
            url = f'user-service/normal/household/detail/{self.household_id}'
        else:
            url = f'user-service/normal/household/change/household/{self.household_id}'
        response = await session.get(url, headers={
            HEADER_TOKEN: self.token
        })
        return self._read_response_json(response)

    async def get_household_coordinates(self) -> Tuple[float, float]:
        session = await self._get_session()

        if not self.household_id:
            raise ValueError('household id is not set')

        response = await session.get(f'hinge-service/normal/court/household/{self.household_id}', headers={
            HEADER_TOKEN: self.token
        })
        data = self._read_response_json(response)
        return float(data['lat']), float(data['lon'])

    async def get_weather(self, period: str, latitude: float, longitude: float) -> dict:
        session = await self._get_session()

        response = await session.get(f'common-service/external/weather/{period}', params={
            'lat': latitude,
            'lon': longitude
        }, headers={
            HEADER_TOKEN: self.token
        })
        return self._read_response_json(response)

    async def get_gateway(self) -> dict:
        session = await self._get_session()

        response = await session.get(f'device-service/normal/gateway', params={
            'householdId': self.household_id
        }, headers={
            HEADER_TOKEN: self.token
        })
        return self._read_response_json(response)

    async def get_areas(self) -> list:
        session = await self._get_session()

        response = await session.get('device-service/normal/device/location', params={
            'householdId': self.household_id
        }, headers={
            HEADER_TOKEN: self.token
        })
        data = self._read_response_json(response)
        return data.get('floorList', [])

    async def get_devices(self, device_type: Optional[str] = None, area: Optional[str] = None) -> List[dict]:
        session = await self._get_session()

        params = {
            'householdId': self.household_id,
            'pageNum': 1,
            'pageSize': 1000
        }
        if device_type:
            params['type'] = device_type
        if area:
            params['area'] = area

        response = await session.get('device-service/normal/device/list', params=params, headers={
            HEADER_TOKEN: self.token
        })
        data = self._read_response_json(response)
        if type(data) != dict:
            return []
        return data.get('list', [])

    async def put_state(self, connection: dict, commands: List[dict]):
        session = await self._get_session()

        response = await session.put('device-service/normal/device/state', json={
            'cmd': commands,
            **connection
        }, headers={
            HEADER_TOKEN: self.token
        })
        return self._read_response_json(response)

    async def get_state(self, connections: List[dict]) -> List[dict]:
        session = await self._get_session()

        response = session.post('state-service/shadow/device/state/block', json=connections, headers={
            HEADER_TOKEN: self.token
        }, timeout=None)
        return self._read_response_json(await response)

    @staticmethod
    def hash_password(password: str) -> str:
        hashed = sha256(password.encode()).hexdigest()
        _LOGGER.debug(f'generated hash for password: {hashed}')
        return hashed

    @staticmethod
    def _read_response_json(response: Response):
        try:
            response.raise_for_status()
        except Exception as e:
            raise TantronConnectionError from e
        data = response.json()
        if type(data) is not dict or 'code' not in data:
            raise TantronConnectionError('invalid response: ' + str(data))
        if data['code'] == HTTPStatus.FORBIDDEN:
            raise TantronAuthenticationError(HTTPStatus.FORBIDDEN.value, data.get('message'), data.get('data'))
        if data['code'] != HTTPStatus.OK:
            raise TantronCloudError(data['code'], data.get('message'), data.get('data'))
        return data.get('data')
