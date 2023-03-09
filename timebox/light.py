"""Platform for light integration."""
from __future__ import annotations
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import LightEntity, SUPPORT_BRIGHTNESS, ATTR_BRIGHTNESS
from homeassistant.const import CONF_NAME
import voluptuous as vol
from homeassistant.components.notify import ATTR_TARGET, ATTR_DATA, PLATFORM_SCHEMA, BaseNotificationService

from homeassistant.core import (
    Context,
    Event,
    HomeAssistant,
    ServiceCall,
    State,
    callback)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_platform

import re
import logging
from .const import DOMAIN, PARAM_BRIGHTNESS, PARAM_DISPLAY_TYPE, PARAM_FILE_NAME, PARAM_LINK, PARAM_MODE, PARAM_TEXT, SERVICE_ACTION, TIMEOUT

#_LOGGER = logging.getLogger("timebox")
from .timebox import _LOGGER


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Light platform."""
    _LOGGER.error("SETTING UP LIGHT")
    timebox = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([TimeboxLight(timebox)]) # , False

    # Send service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_ACTION,
        {
            vol.Required(PARAM_MODE, default=PARAM_TEXT): cv.string,
            vol.Optional(PARAM_LINK): cv.string,
            vol.Optional(PARAM_FILE_NAME): cv.isfile,
            vol.Optional(PARAM_BRIGHTNESS, default=50): int,
            vol.Optional(PARAM_TEXT): cv.string,
            vol.Optional(PARAM_DISPLAY_TYPE): cv.string,
            # vol.Optional(PARAM_TIME)
        },
        handle_send
    )

class TimeboxLight(LightEntity):
    """Representation of an Timebox Light."""

    def __init__(self, timebox) -> None:
        """Initialize an TimeboxLight."""
        self._coordinator = timebox
        self._name = timebox.name
        #self._unique_id = 

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._coordinator.name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._coordinator.brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._coordinator.is_on

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        brightness = None
        if (kwargs.get(ATTR_BRIGHTNESS) is not None):
            brightness = (kwargs.get(ATTR_BRIGHTNESS)/255) * 100
        _LOGGER.error(f"Turned on! With {ATTR_BRIGHTNESS} {self._coordinator.brightness} changing to {kwargs.get(ATTR_BRIGHTNESS)}")
        return await self._coordinator.turn_on(brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._coordinator.turn_off()

        _LOGGER.error("Turned off!")
        self.update()

    async def update(self) -> None:
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        # await self._coordinator.async_request_refresh()


async def handle_send(entity, service_call: ServiceCall):
    await entity.send_message(service_call.data)