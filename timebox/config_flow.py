"""Config flow for Timebox integration."""
from __future__ import annotations

import logging
import aiohttp
import voluptuous as vol
from typing import Any

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_URL, CONF_PORT, CONF_MAC, CONF_NAME, CONF_PATH

from .const import DOMAIN, TIMEOUT  # pylint:disable=unused-import
from .timebox import Timebox

_LOGGER = logging.getLogger(__name__)
DEFAULT_PORT = 5555
DEFAULT_URL = "http://localhost"
DEFAULT_MAC = "11:75:"

# This is the schema used to display the UI to the user
DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_MAC, default=DEFAULT_MAC): str,
        vol.Optional(CONF_NAME, default="TimeboxEvo"): str,
        vol.Optional(CONF_PATH, default="pixelart") : str
    }
)

async def server_is_reachable(url, port):
    async with aiohttp.ClientSession() as client:
        url = f'{url}:{port}/hello'
        async with client.get(url) as response:
            return response.status == 200

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.
    # Check url valid
    if not await server_is_reachable(data["url"], data["port"]):
        raise CannotConnect # Return CannotConnect because integration cannot be setup without server

    # Check host not too short: TODO: enhance host validation
    if len(data["url"]) < 3:
        raise InvalidHost

    # # Check image dir valid
    # if (data[CONF_IMGDIR]):
    #     image_dir = data[CONF_IMGDIR]),
    # else:
    #     image_dir = ""
    #     _LOGGER.warn(f'Invalid image_dir "{data[CONF_IMGDIR]}"')

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    # Return info that you want to store in the config entry.
    # "Title" is what is displayed to the user for this hub device
    # It is stored internally in HA as part of the device config.
    # See `async_step_user` below for how this is used
    return {
        "title": data["name"],
        "url": data["url"],
        "port": data["port"],
        "mac": data["mac"],
        "name": data["name"],
        "path": data["path"]
    }

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Timebox."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_ASSUMED

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                # The error string is set here, and should be translated.
                # This example does not currently cover translations, see the
                # comments on `DATA_SCHEMA` for further details.
                # Set the error on the `host` field, not the entire form.
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(img_path=self.hass.config.path(info["path"]), data=user_input)
            except InvalidDirectory:
                _LOGGER.exception("Failed to convert map name to path")
                errors["base"] = "path_fail"
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

class InvalidDirectory(exceptions.HomeAssistantError):
    """Error to indicate a wrong file path is entered."""