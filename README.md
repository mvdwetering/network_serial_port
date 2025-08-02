# Network serial port

An integration that exposes a serial port on a tcp port so you can connect to the serial port from the network. Basically like running socat, tcp2ser or any of the other existing solutions except that this is packaged as a Home Assistant integration.

When needing to expose multiple serial ports, just add the integration multiple times.

Since it is using PySerial under the hood it is possible to use any [URL handler as supported by PySerial](https://pyserial.readthedocs.io/en/latest/url_handlers.html). This can come in handy when addressing USB adapters by serial with `hwgrep://` to handle changing paths if USB-serial adapters don't have proper serials assigned..

Note that this integration just starts the `tcp_serial_redirect.py` example script from PySerial. It might not be the most fancy solution but it works for now.

## Future?

Some possible useful future additions. 

> Just to manage expectations, this is just a list, I will probably not implement these any time soon if at all.

* Make more settings available in config flow, e.g. byte size, parity, flow control etc...
* Make settings configurable through integration options. E.g. port number
* During configflow show available/detected serial ports with enough info to build a `hwgrep` regex
* Add reconfigure option to the integration
