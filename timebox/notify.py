import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, CONF_URL, CONF_MAC
import voluptuous as vol
from homeassistant.components.notify import ATTR_TARGET, ATTR_DATA,PLATFORM_SCHEMA, BaseNotificationService
import io
from os.path import join

import re
import requests
import logging
from .const import DOMAIN
from .timebox import Timebox, _LOGGER

CONF_IMAGE_DIR = "image_dir"
TIMEOUT = 15

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_IMAGE_DIR): cv.string
})

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

def get_service(hass, config, discovery_info=None):
    image_dir = None
    if (config[CONF_IMAGE_DIR]):
        image_dir = hass.config.path(config[CONF_IMAGE_DIR])
    if not is_valid_server_url(config[CONF_URL]):
        _LOGGER.error(f'Invalid server url "{config[CONF_URL]}"')
        return None
    timebox = Timebox(config[CONF_URL], config[CONF_MAC])
    if not timebox.isConnected():
        return None
    return TimeboxService(timebox, image_dir)

class TimeboxService(BaseNotificationService):
    def __init__(self, timebox, image_dir = None):
        self.timebox = timebox
        self.image_dir = image_dir

    def send_image_link(self, link):
        r = requests.get(link)
        if (r.status_code != 200):
            return False
        return self.timebox.send_image(io.BytesIO(r.content))

    def send_image_file(self, filename):
        try:
            f = open(join(self.image_dir, filename), 'rb')
            return self.timebox.send_image(f)
        except Exception as e:
            _LOGGER.error(e)
            _LOGGER.error(f"Failed to read {filename}")
            return False

    def send_message(self, message="", **kwargs):
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
                return self.send_image_link(data.get(PARAM_LINK))
            elif (data.get(PARAM_FILE_NAME)):
                return self.send_image_file(data.get(PARAM_FILE_NAME))
            else:
                _LOGGER.error(f'Invalid payload, {PARAM_LINK} or {PARAM_FILE_NAME} must be provided with {MODE_IMAGE} mode')
                return False
        elif (mode == MODE_TEXT):
            text = data.get(PARAM_TEXT, message)
            if (text):
                return self.timebox.send_text(text)
            else:
                _LOGGER.error(f"Invalid payload, {PARAM_TEXT} or message must be provided with {MODE_TEXT}")
                return False
        elif (mode == MODE_BRIGHTNESS):
            try:
                brightness = int(data.get(PARAM_BRIGHTNESS))
                return self.timebox.set_brightness(brightness)
            except Exception:
                _LOGGER.error(f"Invalid payload, {PARAM_BRIGHTNESS}={data.get(PARAM_BRIGHTNESS)}")
                return False
        elif (mode == MODE_TIME):
            set_datetime = data.get(PARAM_SET_DATETIME)
            if set_datetime:
                offset = data.get(PARAM_OFFSET_DATETIME)
                self.timebox.set_datetime(offset)

            display_type = data.get(PARAM_DISPLAY_TYPE, "fullscreen")
            return self.timebox.set_time_channel(display_type)
        else:
            _LOGGER.error(f"Invalid mode {mode}")
            return False
        return True