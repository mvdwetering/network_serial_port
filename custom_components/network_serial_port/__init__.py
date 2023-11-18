"""The Network serial port integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .network_serial_port import NetworkSerialPort, NetworkSerialPortConfiguration

from .const import DOMAIN

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Network serial port from a config entry."""

    def connect(network_serial_port:NetworkSerialPort):
        network_serial_port.connect()

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    config = NetworkSerialPortConfiguration("loop://", localport=11111)
    network_serial_port = NetworkSerialPort(config)
    result = await hass.async_add_executor_job(connect, network_serial_port)

    hass.data[DOMAIN][entry.entry_id] = network_serial_port

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):

        def disconnect(network_serial_port:NetworkSerialPort):
            network_serial_port.disconnect()

        network_serial_port = hass.data[DOMAIN].pop(entry.entry_id)
        result = await hass.async_add_executor_job(disconnect, network_serial_port)

        network_serial_port.disconnect()

    return unload_ok
