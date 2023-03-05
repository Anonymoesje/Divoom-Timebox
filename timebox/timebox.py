from datetime import datetime, timedelta, timezone
import re
import requests
import logging
from .const import DOMAIN, TIMEOUT

_LOGGER = logging.getLogger(__name__)


class Timebox():
    def __init__(self, url, port, mac, image_dir, name):
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

    def send_request(self, error_message, url, data, files={}):
        r = requests.post(f'{self.url}:{self.port}{url}', data=data, files=files, timeout=TIMEOUT)
        if (r.status_code != 200):
            _LOGGER.error(r.content)
            _LOGGER.error(error_message)
            return False
        return True

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
