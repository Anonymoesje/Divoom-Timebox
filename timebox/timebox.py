from datetime import datetime, timedelta, timezone
import io
import json
import re
import aiohttp
import logging
from .const import ATTR_DATA, DOMAIN, TIMEOUT, CONF_IMGDIR, DOMAIN, MODE_BRIGHTNESS, MODE_IMAGE, MODE_TEXT, MODE_TIME, PARAM_BRIGHTNESS, PARAM_DISPLAY_TYPE, PARAM_FILE_NAME, PARAM_LINK, PARAM_MESSAGE, PARAM_MODE, PARAM_OFFSET_DATETIME, PARAM_SET_DATETIME, PARAM_TEXT
from os.path import join
# from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

 
class Timebox():
    def __init__(self, hass, session, url, port, mac, image_dir, name):
        self.hass = hass
        self.session = session
        self.url = url
        self.port = port
        self.mac = mac
        self.image_dir = image_dir
        self.name = name

        self._is_on = None
        self._brightness = None
        self._previous_brightness = None
        self._isConnected = None

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return self._brightness

    async def send_request(self, error_message, url, data):
        requestUrl = f'{self.url}:{self.port}{url}'
        async with self.session.post(requestUrl, data=data, timeout=TIMEOUT) as response: #, files=files
            if (response.status != 200):
                _LOGGER.error(response.content)
                _LOGGER.error(error_message)
            _LOGGER.error(f"Request was: {requestUrl} data was {data} timeout was {TIMEOUT} Response was: status code: {response.status} reply is {response} content is {response.content} response will be {response.status == 200}")
            return response.status == 200

    async def send_brightness(self, brightness):
        return await self.send_request('Failed to set brightness', '/brightness', data={"brightness": brightness, "mac": self.mac})

    async def set_brightness(self, brightness):
        if (brightness is None):
            _LOGGER.error("Failed to set brightness, brightness is none")
            return False
        self.send_brightness(brightness)
        self._brightness = brightness

    async def turn_on(self, brightness):
        self._is_on = True
        if (brightness is None):
            if (self._previous_brightness is None):
                self._previous_brightness = 50
            return await self.send_brightness(self._previous_brightness) #self._brightness
        else:
            return await self.send_brightness(brightness) #self._brightness

    async def turn_off(self):
        self._is_on = False
        self._previous_brightness = self._brightness
        return await self.send_brightness(0)

    def send_image(self, image):
        return self.send_request('Failed to send image', '/image', data={"mac": self.mac, "image": image}) #, files={"image": }

    def send_text(self, text):
        return self.send_request('Failed to send text', '/text', data={"text": text, "mac": self.mac})

    def isConnected(self):
        connected = self.send_request('Failed to connect to the timebox', '/connect', data={"mac": self.mac})
        self._isConnected = connected
        return connected

    def set_time_channel(self, display_type):
        return self.send_request('Failed to switch to time channel', '/time',
                                 data={"mac": self.mac, "display_type": display_type})

    def set_datetime(self, offset):
        if offset:
            # parse offset, see https://stackoverflow.com/a/37097784
            sign, hours, minutes = re.match('([+\-]?)(\d{2}):(\d{2})', offset).groups()
            sign = -1 if sign == '-' else 1
            hours, minutes = int(hours), int(minutes)

            tzinfo = timezone(sign * timedelta(hours=hours, minutes=minutes))
        else:
            tzinfo = None

        current_date = datetime.now(tzinfo)

        # convert to unaware datetime, as timebox doesn't support timezone offsets.
        current_date = current_date.replace(tzinfo=None)

        dt = current_date = current_date.isoformat(timespec="seconds")

        return self.send_request('Failed to switch to set datetime', '/datetime',
                                 data={"mac": self.mac, "datetime": dt})


# Service part


    async def send_image_link(self, link):
        async with aiohttp.ClientSession() as client:
            async with client.get(link) as response:
                if (response.status != 200):
                    return False
                return await self.send_image(io.BytesIO(await response.content.read()))

    async def send_image_file(self, filename):
        try:
            f = open(join(self.image_dir, filename), 'rb')
            return await self.send_image(f)
        except Exception as e:
            _LOGGER.error(e)
            _LOGGER.error(f"Failed to read {filename}")
            return False

    async def send_message(self, kwargs):
        _LOGGER.info(f"Sending message to {self.mac}")
        data = kwargs #.get(ATTR_DATA)

        if kwargs is not None:
            mode = data.get(PARAM_MODE, MODE_TEXT)
            _LOGGER.info(f"Data = {data} mode = {mode}")
        else:
            _LOGGER.error(f"Service call needs a message type, data: {data} is not enough")
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
            text = data.get(PARAM_TEXT)
            if (text):
                return await self.send_text(text)
            else:
                _LOGGER.error(f"Invalid payload, {PARAM_TEXT} or message must be provided with {MODE_TEXT}")
                return False
        elif (mode == MODE_BRIGHTNESS):
            if (not f"{brightness}".isdigit()):
                _LOGGER.error("Use a brightness number!")
                return False
            elif (brightness > 100 or brightness < 0):
                _LOGGER.error(f"Use a brightness between 0 and 100! Payload {data.get(PARAM_BRIGHTNESS)} is invalid!")
                return False
            try:
                brightness = int(data.get(PARAM_BRIGHTNESS))
                return await self.set_brightness(brightness)
            except Exception as ex:
                _LOGGER.error(str(ex))
                return False
        elif (mode == MODE_TIME):
            set_datetime = data.get(PARAM_SET_DATETIME)
            if set_datetime:
                offset = data.get(PARAM_OFFSET_DATETIME)
                await self.set_datetime(offset)

            display_type = data.get(PARAM_DISPLAY_TYPE, "fullscreen")
            return await self.set_time_channel(display_type)
        else:
            _LOGGER.error(f"Invalid mode {mode}")
            return False