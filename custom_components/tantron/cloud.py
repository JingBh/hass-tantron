from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Tuple
from hashlib import sha256

from aiohttp import ClientSession

from .error import TantronAuthenticationError, TantronConnectionError, TantronCloudError

if TYPE_CHECKING:
    from typing import Optional, Dict
    from aiohttp import ClientResponse

_LOGGER = logging.getLogger(__name__)

HEADER_TOKEN = 'access_token'

token_cache = {}


class TantronCloud:
    def __init__(self, token: Optional[str] = None, household_id: Optional[str] = None):
        self.session: Optional[ClientSession] = None
        self.base_url = 'https://smart.i-ttg.net/'
        self.user_agent = 'TantronAssistant/1.1.8 (iPhone; iOS 18.2; Scale/3.00)'
        self.token = token
        self.household_id = household_id

    async def __aenter__(self):
        if self.session is None or self.session.closed:
            self.session = ClientSession(base_url=self.base_url, headers={
                'User-Agent': self.user_agent
            })
        return self

    async def __aexit__(self, *args):
        if self.session is not None:
            await self.session.close()

    async def login(self, phone: str, password: str) -> str:
        """
        Authenticates with the Tantron cloud and returns the access token.
        Modifies the current instance to use the token in future requests.

        The WeChat WeApp login channel is used,
        so that this integration cannot be used together with the WeApp.
        Official Android / iOS app is not affected.
        """

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
            async with self.session.post('user-service/wei_xin_mini_program/login', json={
                'phone': phone,
                'password': password
            }) as response:
                data = await self._read_response_json(response)
        except TantronCloudError as e:
            raise TantronAuthenticationError(e.code, e.message, e.data)

        self.token = data['accessToken']
        token_cache[phone] = self.token
        return data['accessToken']

    async def get_user(self) -> dict:
        async with self.session.get('user-service/user', headers={
            HEADER_TOKEN: self.token
        }) as response:
            return await self._read_response_json(response)

    async def list_households(self) -> Dict[str, str]:
        async with self.session.get('user-service/normal/household/list', headers={
            HEADER_TOKEN: self.token
        }) as response:
            data = await self._read_response_json(response)
            if type(data) is not list:
                return {}
            return {
                i['householdId']: i['householdName']
                for i in data
                if i.get('gatewayBound') is True
            }

    async def get_household(self, detailed: bool = False) -> dict:
        if not self.household_id:
            raise ValueError('household id is not set')
        if detailed:
            url = f'user-service/normal/household/detail/{self.household_id}'
        else:
            url = f'user-service/normal/household/change/household/{self.household_id}'
        async with self.session.get(url, headers={
            HEADER_TOKEN: self.token
        }) as response:
            return await self._read_response_json(response)

    async def get_household_coordinates(self) -> Tuple[float, float]:
        if not self.household_id:
            raise ValueError('household id is not set')
        async with self.session.get(f'hinge-service/normal/court/household/{self.household_id}', headers={
            HEADER_TOKEN: self.token
        }) as response:
            response.raise_for_status()
            data = await self._read_response_json(response)
            return float(data['lat']), float(data['lon'])

    async def get_weather(self, period: str, latitude: float, longitude: float) -> dict:
        async with self.session.get(f'common-service/external/weather/{period}', params={
            'lat': latitude,
            'lon': longitude
        }, headers={
            HEADER_TOKEN: self.token
        }) as response:
            return await self._read_response_json(response)

    @staticmethod
    def hash_password(password: str) -> str:
        hashed = sha256(password.encode()).hexdigest()
        _LOGGER.debug(f'generated hash for password: {hashed}')
        return hashed

    @staticmethod
    async def _read_response_json(response: ClientResponse):
        try:
            response.raise_for_status()
        except Exception as e:
            raise TantronConnectionError from e
        data = await response.json()
        if type(data) is not dict or 'code' not in data:
            raise TantronConnectionError('invalid response: ' + str(data))
        if data['code'] == HTTPStatus.FORBIDDEN:
            raise TantronAuthenticationError(HTTPStatus.FORBIDDEN.value, data.get('message'), data.get('data'))
        if data['code'] != HTTPStatus.OK:
            raise TantronCloudError(data['code'], data.get('message'), data.get('data'))
        return data.get('data')
