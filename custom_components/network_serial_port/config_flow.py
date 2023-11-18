"""Config flow for Network serial port integration."""
from __future__ import annotations
import asyncio

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from custom_components.network_serial_port.network_serial_process import NetworkSerialPortConfiguration, NetworkSerialProcess

from .const import CONF_BAUDRATE, CONF_SERIAL_URL, CONF_TCP_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_URL): str,
        vol.Required(CONF_BAUDRATE): int,
        vol.Required(CONF_TCP_PORT): int,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # validate the data can be used to set up a connection.

    network_serial_process = NetworkSerialProcess(NetworkSerialPortConfiguration.from_dict(data))
    await network_serial_process.start()
    await asyncio.sleep(2)
    if not network_serial_process.is_running:
        raise CannotConnect
    await network_serial_process.stop()

    # Return info that you want to store in the config entry.
    return {"title": data["serial_url"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Network serial port."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            # except InvalidAuth:
            #     errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
