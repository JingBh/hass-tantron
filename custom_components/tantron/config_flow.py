from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypedDict

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow

from .cloud import TantronCloud
from .const import DOMAIN
from .error import TantronConnectionError, TantronAuthenticationError, TantronCloudError

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required('phone'): str,
    vol.Required('password'): str,
})


class ConfigEntryData(TypedDict):
    phone: str
    password: str
    token: str
    household: str


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    data: Optional[Dict[str, str]] = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        self.data = None

        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                phone = user_input['phone']
                password = TantronCloud.hash_password(user_input['password'])
                async with TantronCloud() as cloud:
                    token = await cloud.login(phone, password)
                    households = await cloud.list_households()
            except TantronConnectionError:
                errors['base'] = 'connection_error'
            except TantronAuthenticationError:
                errors['base'] = 'authentication_error'
            except TantronCloudError as e:
                errors['base'] = e.message
            except Exception:
                _LOGGER.exception('Unexpected exception')
                errors['base'] = 'unknown'
            else:
                if not households:
                    errors['base'] = 'no_households'
                else:
                    self.data = {
                        'phone': phone,
                        'password': password,
                        'token': token,
                        'households': households
                    }
                    return await self.async_step_household()

        return self.async_show_form(step_id='user', data_schema=STEP_USER_DATA_SCHEMA, errors=errors, last_step=False)

    async def async_step_household(self, user_input: Optional[Dict[str, Any]] = None):
        if self.data is None:
            return await self.async_step_user()

        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                household_id = user_input['household']
                async with TantronCloud(token=self.data['token'], household_id=household_id) as cloud:
                    household = await cloud.get_household()
            except TantronConnectionError:
                errors['base'] = 'connection_error'
            except TantronAuthenticationError:
                errors['base'] = 'authentication_error'
            except TantronCloudError as e:
                errors['base'] = e.message
            except Exception:
                _LOGGER.exception('Unexpected exception')
                errors['base'] = 'unknown'
            else:
                await self.async_set_unique_id(household['householdId'])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=household['householdName'], data=ConfigEntryData(
                    phone=self.data['phone'],
                    password=self.data['password'],
                    token=self.data['token'],
                    household=household['householdId']
                ))

        return self.async_show_form(step_id='household', data_schema=vol.Schema({
            vol.Required('household'): vol.In(self.data['households'])
        }), errors=errors, last_step=True)

    async def async_step_reauth(self, entry_data: ConfigEntryData):
        entry = self._get_reauth_entry()
        try:
            async with TantronCloud(household_id=entry_data['household']) as cloud:
                token = await cloud.login(entry_data['phone'], entry_data['password'])
                household = await cloud.get_household()
        except Exception:
            return self.async_abort(reason='reauth_failed')
        await self.async_set_unique_id(household['householdId'])
        self._abort_if_unique_id_mismatch()
        return self.async_update_reload_and_abort(entry, data_updates={
            'token': token
        })
