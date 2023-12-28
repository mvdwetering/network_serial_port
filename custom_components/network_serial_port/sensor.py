from dataclasses import dataclass
from typing import Callable


from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import NetworkSerialPortCoordinator
from .const import DOMAIN
from .network_serial_process import NetworkSerialProcess

@dataclass
class NetworkSerialPortEntitySensorDescription(SensorEntityDescription):
    get_value: Callable[[NetworkSerialProcess], str] = None  # type: ignore[assignment]


ENTITY_DESCRIPTIONS = [
    NetworkSerialPortEntitySensorDescription(  # type: ignore
        key="connected_client",  # type: ignore
        icon="mdi:lan-connect",  # type: ignore
        get_value=lambda api: api.connected_client if api.connected_client else "",
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: NetworkSerialPortCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        entities.append(NetworkSerialPortSensor(config_entry.entry_id, coordinator, entity_description))

    async_add_entities(entities)


class NetworkSerialPortSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry_id: str,
        coordinator: NetworkSerialPortCoordinator,
        entity_description: NetworkSerialPortEntitySensorDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.coordinator: NetworkSerialPortCoordinator

        self.entity_description: NetworkSerialPortEntitySensorDescription = entity_description
        self._attr_translation_key = self.entity_description.key

        self._attr_unique_id = (
            f"{config_entry_id}_{self.entity_description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)}
        )

    @property
    def native_value(self) -> str | None:
        return self.entity_description.get_value(self.coordinator.api)
