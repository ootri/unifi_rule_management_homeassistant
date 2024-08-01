"""Config flow for UniFi Rules Management integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .unifi_client import UnifiClient
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi Rules."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.info("Starting async_step_user for UniFi Rules")
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HOST): str,
                        vol.Required(CONF_USERNAME): str,
                        vol.Required(CONF_PASSWORD): str,
                        vol.Optional("scan_interval", default=300): int,
                    }
                )
            )

        errors = {}

        try:
            client = UnifiClient(
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            await client._authenticate()
            
            # Fetch the console name
            console_name = await client.get_console_name()
            
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception(f"Unexpected exception: {str(e)}")
            errors["base"] = "unknown"
        else:
            _LOGGER.info(f"Successfully created entry: {user_input}")
            # Create a friendly name for the integration
            friendly_name = f"{console_name} Rule Management"
            return self.async_create_entry(title=friendly_name, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional("scan_interval", default=300): int,
                }
            ), errors=errors
        )