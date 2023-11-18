"""The Network serial port integration."""
from __future__ import annotations
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .network_serial_process import NetworkSerialPortConfiguration, NetworkSerialProcess

from .const import CONF_BAUDRATE, CONF_SERIAL_URL, CONF_TCP_PORT, DOMAIN

PLATFORMS: list[Platform] = []



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Network serial port from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    network_serial_process = NetworkSerialProcess(NetworkSerialPortConfiguration.from_dict(entry.data))
    await network_serial_process.start()
    await asyncio.sleep(2)
    if not network_serial_process.is_running:
        return False

    hass.data[DOMAIN][entry.entry_id] = network_serial_process

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        network_serial_port: NetworkSerialProcess = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        await network_serial_port.stop()

    return unload_ok
