"""Platform for light integration."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import LightEntity, SUPPORT_BRIGHTNESS, ATTR_BRIGHTNESS
from homeassistant.const import CONF_NAME
import voluptuous as vol
from homeassistant.components.notify import ATTR_TARGET, ATTR_DATA, PLATFORM_SCHEMA, BaseNotificationService

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry

import re
import logging
from .const import DOMAIN, TIMEOUT


#_LOGGER = logging.getLogger("timebox")
from .timebox import _LOGGER

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


async def async_setup_entry(
        hass, config_entry: ConfigEntry, async_add_entities, discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    timebox = hass.data[DOMAIN][config_entry.entry_id]

    light_devices = [TimeboxLight(timebox)]
    # Add devices
    async_add_entities(light_devices)

class TimeboxLight(LightEntity):
    """Representation of an Timebox Light."""

    def __init__(self, timebox) -> None:
        """Initialize an TimeboxLight."""
        self._light = timebox
        self._name = timebox.name
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