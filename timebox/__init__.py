"""Timebox integration"""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import requests

from .const import DOMAIN
from .timebox import Timebox
TIMEOUT = 15

_LOGGER = logging.getLogger(__name__)

# Supported Platforms
PLATFORMS = [
    # "binary_sensor",
    # "button",
    # "light",
    # "media_player",
    # "number",
    # "sensor",
    # "switch",
    "light",
    "notify"
]



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up timebox from the config entry."""
    
    image_dir = entry.data["img_dir"]
    timebox_url = entry.data["url"]
    timebox_port = entry.data["port"]
    timebox_mac = entry.data["mac"]
    timebox_name = entry.data["name"]
    
    # Setup timebox singleton
    timebox = Timebox(timebox_url, timebox_mac)
    if not timebox.isConnected():
        return False # Return false because integration cannot operate without connection

    # Store an instance of the "connecting" class that does the work of speaking with the actual devices.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = Timebox(hass, timebox_url, timebox_port, timebox_mac, image_dir, timebox_name)

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok