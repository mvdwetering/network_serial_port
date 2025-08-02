import asyncio
from dataclasses import dataclass
import pathlib
import re
from typing import Awaitable, Callable

from .const import CONF_BAUDRATE, CONF_SERIAL_URL, CONF_TCP_PORT, LOGGER

import serial  # type: ignore


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

    _connected_regex = re.compile(r"Connected by \('(?P<client_ip>[^']*)',")


    def __init__(self, configuration: NetworkSerialPortConfiguration, on_connection_change:Callable[[], None]|None=None, on_process_lost:Callable[[], Awaitable[None]]|None=None) -> None:
        self._configuration = configuration
        self.connected_client:str|None = None
        self.on_connection_change = on_connection_change
        self._on_process_lost = on_process_lost
        self._started_event = asyncio.Event()
        self._start_success = False

    @property
    def is_running(self) -> bool:
        return self._process.returncode is None if self._process else False

    async def start(self) -> bool:
        self._started_event.clear()
        self._start_success = False

        path = pathlib.Path(__file__).parent.resolve()
        args = [
            "python3",
            f"{path}/tcp_serial_redirect.py",
            self._configuration.url,
            str(self._configuration.baudrate),
            f"-P {self._configuration.localport}",
        ]

        self._process = await asyncio.create_subprocess_exec(
            *args, stderr=asyncio.subprocess.PIPE
        )
        self._process_wait_task = asyncio.create_task(self._wait_for_process_exit(), name="TCP Serial Redirect process waiter")
        self._reader_task = asyncio.create_task(self._process_stderr_output(), name="TCP Serial Redirect stderr reader")

        # Make sure the process is started properly
        try:
            await asyncio.wait_for(self._started_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            LOGGER.error("Timeout waiting for process to start")
            return False
        except Exception as e:
            LOGGER.error(f"Exception while waiting for process start: {e}")
            return False

        return self._start_success

    async def stop(self):
        # Clear the callback because stopping on purpose
        self._on_process_lost = None  

        self._process.terminate()
        await self._process.wait()
        self._start_success = False

        LOGGER.info(f"Tasks: {self._process_wait_task.done=}, {self._reader_task.done=}")

    async def _wait_for_process_exit(self):
        await self._process.wait()
        LOGGER.debug("Process exited")
        if self._start_success and self._on_process_lost:
            await self._on_process_lost()

    async def _process_stderr_output(self):
        assert self._process.stderr is not None

        while True:
            try:
                line = await self._process.stderr.readline()
                if line.endswith(b'\n'):
                    LOGGER.debug(line)
                    self._handle_line(line)
                else:
                    LOGGER.debug("EOF detected")
                    return
            except ValueError:
                LOGGER.error("ValueError, limit was reached", exc_info=True)
            except asyncio.CancelledError:
                LOGGER.debug("asyncio.CancelledError", exc_info=True)
                return
            except Exception as e:
                LOGGER.exception(e)
                return

    def _handle_line(self, input:bytes):
        line = input.decode("utf-8")

        # Checks related to process start
        if line.startswith("Could not open serial port"):
            LOGGER.error("Could not open serial port, check your configuration")
            self._start_success = False
            self._started_event.set()
        elif line.startswith("Waiting for connection on"):
            LOGGER.info("Ready to accept connections")
            self._start_success = True
            self._started_event.set()
        # Checks related to client connection state
        elif line.startswith("Disconnected"):
            self.connected_client = None
            self._signal_connection_change()
        elif m := self._connected_regex.match(line):
            self.connected_client = m.group("client_ip")
            self._signal_connection_change()


    def _signal_connection_change(self):
        if self.on_connection_change:
            self.on_connection_change()
