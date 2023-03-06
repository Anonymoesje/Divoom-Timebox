import aiohttp
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.notify import ATTR_TARGET, ATTR_DATA,PLATFORM_SCHEMA, BaseNotificationService, SERVICE_NOTIFY
import io
from datetime import datetime, timedelta, timezone
from os.path import join
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

import re
import logging
from .const import CONF_IMGDIR, DOMAIN, TIMEOUT
from .timebox import _LOGGER, Timebox

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

async def async_get_service(hass: HomeAssistant, config: ConfigEntry, discovery_info=None):
        """Set up the notify platform for Timebox"""
        timebox = hass.data[DOMAIN][config.entry_id]
        service = TimeboxService(timebox)
        service.image_dir = config[CONF_IMGDIR]
        return service

class TimeboxService(BaseNotificationService):
    def __init__(self, timebox, body, image_dir = None):
        self.timebox = timebox
        self.image_dir = image_dir
        self.body = body

    async def send_image_link(self, link):
        async with aiohttp.ClientSession() as client:
            async with client.get(link) as response:
                if (response.status != 200):
                    return False
                return await self.timebox.send_image(io.BytesIO(response.content))

    async def send_image_file(self, filename):
        try:
            f = open(join(self.image_dir, filename), 'rb')
            return await self.timebox.send_image(f)
        except Exception as e:
            _LOGGER.error(e)
            _LOGGER.error(f"Failed to read {filename}")
            return False

    async def send_message(self, message="", **kwargs):
        if kwargs.get(ATTR_DATA) is not None:
            data = kwargs.get(ATTR_DATA)
            mode = data.get(PARAM_MODE, MODE_TEXT)
        elif message is not None:
            data = {}
            mode = MODE_TEXT
        else:
            _LOGGER.error("Service call needs a message type")
            return False

        if (mode == MODE_IMAGE):
            if (data.get(PARAM_LINK)):
                return await self.send_image_link(data.get(PARAM_LINK))
            elif (data.get(PARAM_FILE_NAME)):
                return await self.send_image_file(data.get(PARAM_FILE_NAME))
            else:
                _LOGGER.error(f'Invalid payload, {PARAM_LINK} or {PARAM_FILE_NAME} must be provided with {MODE_IMAGE} mode')
                return False
        elif (mode == MODE_TEXT):
            text = data.get(PARAM_TEXT, message)
            if (text):
                return await self.timebox.send_text(text)
            else:
                _LOGGER.error(f"Invalid payload, {PARAM_TEXT} or message must be provided with {MODE_TEXT}")
                return False
        elif (mode == MODE_BRIGHTNESS):
            try:
                brightness = int(data.get(PARAM_BRIGHTNESS))
                return await self.timebox.set_brightness(brightness)
            except Exception:
                _LOGGER.error(f"Invalid payload, {PARAM_BRIGHTNESS}={data.get(PARAM_BRIGHTNESS)}")
                return False
        elif (mode == MODE_TIME):
            set_datetime = data.get(PARAM_SET_DATETIME)
            if set_datetime:
                offset = data.get(PARAM_OFFSET_DATETIME)
                await self.timebox.set_datetime(offset)

            display_type = data.get(PARAM_DISPLAY_TYPE, "fullscreen")
            return await self.timebox.set_time_channel(display_type)
        else:
            _LOGGER.error(f"Invalid mode {mode}")
            return False
        
async def async_unload_entry(hass, entry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Attempting to unload notify")
    hass.services.async_remove(SERVICE_NOTIFY, f"{DOMAIN}")
    if hass.data[DOMAIN].get("notify_service"):
        hass.data[DOMAIN].pop("notify_service")
    return True