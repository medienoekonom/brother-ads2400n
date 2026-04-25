"""Config flow for Brother ADS-2400N integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

from .const import DOMAIN, DEFAULT_PORT
from .scanner_client import BrotherADS2400NClient, ScannerConnectionError, ScannerAuthError

_LOGGER = logging.getLogger(__name__)


class BrotherADS2400NConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            password = user_input[CONF_PASSWORD]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            client = BrotherADS2400NClient(host, password, port)
            try:
                _LOGGER.debug("Testing connection to %s:%s", host, port)
                data = await client.async_fetch_info()
                _LOGGER.debug("Connection successful, data: %s", data)
                serial = data.get("serial") or host
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Brother ADS-2400N ({host})",
                    data={CONF_HOST: host, CONF_PASSWORD: password, CONF_PORT: port},
                )
            except ScannerAuthError as err:
                _LOGGER.warning("Auth error: %s", err)
                errors["password"] = "invalid_auth"
            except ScannerConnectionError as err:
                _LOGGER.warning("Connection error: %s", err)
                errors["host"] = "cannot_connect"
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during setup: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }),
            errors=errors,
        )
