"""Timebox integration"""
from __future__ import annotations
import asyncio

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from .const import DOMAIN
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from .timebox import Timebox
from .notify import TimeboxService, async_unload_entry as notify_async_unload_entry
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
    "light"
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up timebox from the config entry."""
    
    image_dir = entry.data["img_dir"]
    timebox_url = entry.data["url"]
    timebox_port = entry.data["port"]
    timebox_mac = entry.data["mac"]
    timebox_name = entry.data["name"]
    
    # Setup timebox singleton
    timebox = Timebox(timebox_url, timebox_port, timebox_mac, image_dir, timebox_name)
    if not timebox.isConnected():
        _LOGGER.error("No connection to Timebox, check your bluetooth connection!")
        return False # Return false because integration cannot operate without connection
    else:
        _LOGGER.info("Timebox succesfully connected")

    # Store an instance of the "connecting" class that does the work of speaking with the actual devices.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = timebox

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def complete_startup(event=None) -> None:
        # pylint: disable=unused-argument
        """Run final tasks after startup."""
        _LOGGER.debug("Completing remaining startup tasks.")
        # notify = hass.data[DOMAIN].get("notify_service")
        # hass.services.async_register(DOMAIN, DOMAIN, TimeboxService(timebox, timebox.image_dir))

        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                Platform.NOTIFY,
                DOMAIN,
                dict(entry.data),
                hass.data[DOMAIN]
            )
        )

        return True

    await complete_startup()
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok