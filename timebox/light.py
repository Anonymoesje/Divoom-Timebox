"""Platform for light integration."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import LightEntity, SUPPORT_BRIGHTNESS, ATTR_BRIGHTNESS
from homeassistant.const import CONF_NAME, CONF_URL, CONF_MAC
import voluptuous as vol
from homeassistant.components.notify import ATTR_TARGET, ATTR_DATA, PLATFORM_SCHEMA, BaseNotificationService

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType

import re
import requests
import logging
from .const import DOMAIN
from .timebox import Timebox

_LOGGER = logging.getLogger("timebox")
TIMEOUT = 15

PARAM_MODE = "mode"

MODE_IMAGE = "image"
PARAM_FILE_NAME = "file-name"
PARAM_LINK = "link"

MODE_TEXT = "text"
PARAM_TEXT = "text"

MODE_BRIGHTNESS = "brightness"
PARAM_BRIGHTNESS = "brightness"

MODE_TIME = "time"
PARAM_SET_DATETIME = "set-datetime"
PARAM_OFFSET_DATETIME = "offset-datetime"
PARAM_DISPLAY_TYPE = "display-type"


def is_valid_server_url(url):
    r = requests.get(f'{url}/hello', timeout=TIMEOUT)
    if r.status_code != 200:
        return False
    return True


def setup_platform(
        hass, config, add_entities: AddEntitiesCallback, discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.

    if not is_valid_server_url(config[CONF_URL]):
        _LOGGER.error(f'Invalid server url "{config[CONF_URL]}"')
        return None
    timebox = Timebox(config[CONF_URL], config[CONF_MAC])
    if not timebox.isConnected():
        return None

    light_devices = [TimeboxLight(timebox, config[CONF_NAME])]
    # Add devices
    add_entities(light_devices)


class TimeboxLight(LightEntity):
    """Representation of an Timebox Light."""

    def __init__(self, timebox, name) -> None:
        """Initialize an TimeboxLight."""
        self._light = timebox
        self._name = name
        self._state = None
        self._brightness = None

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS
    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._light.turn_on()
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness != self._light.brightness:
            self._light.set_brightness(brightness)

        self.update()

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._light.turn_off()
        self.update()

    def update(self) -> None:
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self._light.is_on
        self._brightness = self._light.brightness