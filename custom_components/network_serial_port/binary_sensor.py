from dataclasses import dataclass
from typing import Callable


from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import NetworkSerialPortCoordinator
from .const import DOMAIN
from .network_serial_process import NetworkSerialProcess

@dataclass
class NetworkSerialPortEntityBinarySensorDescription(BinarySensorEntityDescription):
    is_on: Callable[[NetworkSerialProcess], bool] = None  # type: ignore[assignment]


ENTITY_DESCRIPTIONS = [
    NetworkSerialPortEntityBinarySensorDescription(  # type: ignore
        key="client_connected",  # type: ignore
        device_class="connectivity",  # type: ignore
        is_on=lambda api: api.connected_client is not None,
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: NetworkSerialPortCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        entities.append(NetworkSerialPortBinarySensor(config_entry.entry_id, coordinator, entity_description))

    async_add_entities(entities)


class NetworkSerialPortBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry_id: str,
        coordinator: NetworkSerialPortCoordinator,
        entity_description: NetworkSerialPortEntityBinarySensorDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.coordinator: NetworkSerialPortCoordinator

        self.entity_description: NetworkSerialPortEntityBinarySensorDescription = entity_description
        self._attr_translation_key = self.entity_description.key

        self._attr_unique_id = (
            f"{config_entry_id}_{self.entity_description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)}
        )

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on(self.coordinator.api)
