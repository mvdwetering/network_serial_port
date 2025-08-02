"""The Network serial port integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry

from .coordinator import NetworkSerialPortCoordinator
from .network_serial_process import NetworkSerialPortConfiguration, NetworkSerialProcess

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Network serial port from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    async def on_process_lost():
        if not hass.is_stopping:
            await hass.config_entries.async_reload(entry.entry_id)

    network_serial_process = NetworkSerialProcess(
        NetworkSerialPortConfiguration.from_dict(dict(entry.data)),
        on_process_lost=on_process_lost,
    )

    if not await network_serial_process.start():
        raise ConfigEntryNotReady

    coordinator = NetworkSerialPortCoordinator(hass, network_serial_process)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Explictly add service, so entities can link up with just the identifiers
    registry = device_registry.async_get(hass)
    registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        entry_type=device_registry.DeviceEntryType.SERVICE,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    def on_connection_change():
        coordinator.async_set_updated_data(network_serial_process)

    network_serial_process.on_connection_change = on_connection_change

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: NetworkSerialPortCoordinator = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        await coordinator.api.stop()

    return unload_ok
