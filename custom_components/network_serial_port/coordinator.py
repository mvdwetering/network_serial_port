"""Coordinator for the Network Serial Port integration."""

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import LOGGER
from .network_serial_process import NetworkSerialProcess

class NetworkSerialPortCoordinator(DataUpdateCoordinator[NetworkSerialProcess]):
    """My custom coordinator."""

    def __init__(self, hass, api: NetworkSerialProcess):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            # Name of the data. For logging purposes.
            name="Network Serial Port",
        )
        self.api = api
        self.data = api # Can just read data directly from API
