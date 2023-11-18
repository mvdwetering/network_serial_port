"""The Network serial port integration."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
import pathlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import serial

from .const import DOMAIN

PLATFORMS: list[Platform] = []


@dataclass
class NetworkSerialPortConfiguration:
    url: str
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = serial.PARITY_NONE
    stopbits: int = 1
    rtscts: bool = False
    xonxoff: bool = False
    rts: int | None = None
    dtr: bool | None = None
    localport: int | None = None
    client: str = ""


class NetworkSerialProcess:
    def __init__(self, configuration: NetworkSerialPortConfiguration) -> None:
        self._configuration = configuration

    async def start(self):
        path = pathlib.Path(__file__).parent.resolve()

        args = [
            f"{path}/tcp_serial_redirect.py",
            self._configuration.url,
            str(self._configuration.baudrate),
            f"-P {self._configuration.localport}"
        ]

        self._process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE
        )

    async def stop(self):
        self._process.terminate()
        await self._process.wait()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Network serial port from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    config = NetworkSerialPortConfiguration("loop://", localport=11111)
    network_serial_port = NetworkSerialProcess(config)

    await network_serial_port.start()

    hass.data[DOMAIN][entry.entry_id] = network_serial_port

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
