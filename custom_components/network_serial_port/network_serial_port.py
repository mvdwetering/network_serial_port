# Network serial port implementation
#
# Basically a copy of the tcp_serial_redirect.py example from pyserial wrapped in a thread
# and takes settings from a structure instead of commandline

from dataclasses import dataclass
from threading import Thread
import socket
import time

import serial  # type: ignore
import serial.threaded  # type: ignore

from .const import LOGGER

@dataclass
class NetworkSerialPortConfiguration:
    url:str
    baudrate:int=115200
    bytesize:int = 8
    parity:str = serial.PARITY_NONE
    stopbits:int = 1
    rtscts:bool = False
    xonxoff:bool = False
    rts:int|None = None
    dtr:bool|None = None
    localport:int|None = None
    client:str = ""

class SerialToNet(serial.threaded.Protocol):
    """serial->socket"""

    def __init__(self):
        self.socket = None

    def __call__(self):
        return self

    def data_received(self, data):
        if self.socket is not None:
            self.socket.sendall(data)


class NetworkSerialPort(): 

    def __init__(self, configuration:NetworkSerialPortConfiguration) -> None:
        self._configuration = configuration
        self._thread:Thread|None = None

    def connect(self):
        self._thread = Thread(target=self._main)
        self._thread.daemon = True
        self._thread.start()

    def disconnect(self):
        if self._thread:
            self._thread.join(2)
        pass

    def _main(self):
        # connect to serial port
        ser = serial.serial_for_url(self._configuration.url, do_not_open=True)
        ser.baudrate = self._configuration.baudrate
        ser.bytesize = self._configuration.bytesize
        ser.parity = self._configuration.parity
        ser.stopbits = self._configuration.stopbits
        ser.rtscts = self._configuration.rtscts
        ser.xonxoff = self._configuration.xonxoff

        if self._configuration.rts is not None:
            ser.rts = self._configuration.rts

        if self._configuration.dtr is not None:
            ser.dtr = self._configuration.dtr

        LOGGER.debug(
                '--- TCP/IP to Serial redirect on {p.name}  {p.baudrate},{p.bytesize},{p.parity},{p.stopbits} ---\n'
                '--- type Ctrl-C / BREAK to quit\n'.format(p=ser))

        try:
            ser.open()
        except serial.SerialException as e:
            LOGGER.error('Could not open serial port %s: %s\n', ser.name, e)
            return

        ser_to_net = SerialToNet()
        serial_worker = serial.threaded.ReaderThread(ser, ser_to_net)
        serial_worker.start()

        if not self._configuration.client:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(('', self._configuration.localport))
            srv.listen(1)

        try:
            intentional_exit = False
            while True:
                if self._configuration.client:
                    host, port = self._configuration.client.split(':')
                    LOGGER.info("Opening connection to {}:{}...\n".format(host, port))
                    client_socket = socket.socket()
                    try:
                        client_socket.connect((host, int(port)))
                    except socket.error as msg:
                        LOGGER.warn('WARNING: {}\n'.format(msg))
                        time.sleep(5)  # intentional delay on reconnection as client
                        continue
                    LOGGER.info('Connected\n')
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    #~ client_socket.settimeout(5)
                else:
                    LOGGER.info('Waiting for connection on {}...\n'.format(self._configuration.localport))
                    client_socket, addr = srv.accept()
                    LOGGER.info('Connected by {}\n'.format(addr))
                    # More quickly detect bad clients who quit without closing the
                    # connection: After 1 second of idle, start sending TCP keep-alive
                    # packets every 1 second. If 3 consecutive keep-alive packets
                    # fail, assume the client is gone and close the connection.
                    try:
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
                        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    except AttributeError:
                        pass # XXX not available on windows
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                try:
                    ser_to_net.socket = client_socket
                    # enter network <-> serial loop
                    while True:
                        try:
                            data = client_socket.recv(1024)
                            if not data:
                                break
                            print("data:", data)
                            ser.write(data)                 # get a bunch of bytes and send them
                        except socket.error as msg:
                            # if args.develop:
                            #     raise
                            LOGGER.error('ERROR: {}\n'.format(msg))
                            # probably got disconnected
                            break
                except KeyboardInterrupt:
                    intentional_exit = True
                    raise
                except socket.error as msg:
                    # if args.develop:
                    #     raise
                    LOGGER.error('ERROR: {}\n'.format(msg))
                finally:
                    ser_to_net.socket = None
                    LOGGER.info('Disconnected\n')
                    client_socket.close()
                    if self._configuration.client and not intentional_exit:
                        time.sleep(5)  # intentional delay on reconnection as client
        except KeyboardInterrupt:
            pass

        LOGGER.info('\n--- exit ---\n')
        serial_worker.stop()        
