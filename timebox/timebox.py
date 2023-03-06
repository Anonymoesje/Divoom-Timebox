from datetime import datetime, timedelta, timezone
import io
import re
import aiohttp
import logging
from .const import ATTR_DATA, DOMAIN, TIMEOUT, CONF_IMGDIR, DOMAIN, MODE_BRIGHTNESS, MODE_IMAGE, MODE_TEXT, MODE_TIME, PARAM_BRIGHTNESS, PARAM_DISPLAY_TYPE, PARAM_FILE_NAME, PARAM_LINK, PARAM_MESSAGE, PARAM_MODE, PARAM_OFFSET_DATETIME, PARAM_SET_DATETIME, PARAM_TEXT
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

 
class Timebox(Entity):
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
        self._isConnected = None

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return self._brightness

    async def send_request(self, error_message, url, data, files={}):
        requestUrl = f'{self.url}:{self.port}{url}/hello'
        async with self.session.post(requestUrl, data=data, files=files, timeout=TIMEOUT) as response:
            if (response.status != 200):
                _LOGGER.error(response.content)
                _LOGGER.error(error_message)
            return response.status == 200

    def send_brightness(self, brightness):
        self.send_request('Failed to set brightness', '/brightness', data={"brightness": brightness, "mac": self.mac})

    def set_brightness(self, brightness):
        self.send_brightness(brightness)
        self._brightness = brightness

    def turn_on(self):
        self.send_brightness(50)
        self._brightness = 50
        self._is_on = True

    def turn_off(self):
        self.send_brightness(0)
        self._brightness = 0
        self._is_on = False

    def send_image(self, image):
        return self.send_request('Failed to send image', '/image', data={"mac": self.mac}, files={"image": image})

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
        _LOGGER.warn(f"Inside data: {kwargs.get(ATTR_DATA)} message data: {kwargs.get(PARAM_MESSAGE)} outside data: {kwargs}")
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