

import asyncio
from dataclasses import dataclass
import pathlib

from .const import CONF_BAUDRATE, CONF_SERIAL_URL, CONF_TCP_PORT

import serial


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

    @staticmethod
    def from_dict(data:dict):
        return NetworkSerialPortConfiguration(
            data[CONF_SERIAL_URL],
            baudrate=data[CONF_BAUDRATE],
            localport=data[CONF_TCP_PORT],
        )



class NetworkSerialProcess:
    def __init__(self, configuration: NetworkSerialPortConfiguration) -> None:
        self._configuration = configuration

    @property
    def is_running(self) -> bool:
        return self._process.returncode is None if self._process else False

    async def start(self):
        path = pathlib.Path(__file__).parent.resolve()

        args = [
            f"{path}/tcp_serial_redirect.py",
            self._configuration.url,
            str(self._configuration.baudrate),
            f"-P {self._configuration.localport}",
        ]

        self._process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE
        )

    async def stop(self):
        self._process.terminate()
        await self._process.wait()
