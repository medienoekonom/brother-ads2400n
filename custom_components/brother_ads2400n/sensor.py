"""Sensors for Brother ADS-2400N."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import BrotherADS2400NCoordinator


@dataclass
class BrotherSensorDescription(SensorEntityDescription):
    data_key: str = ""


SENSOR_DESCRIPTIONS: tuple[BrotherSensorDescription, ...] = (
    BrotherSensorDescription(
        key="status",
        data_key="status",
        name="Device Status",
        icon="mdi:scanner",
    ),
    BrotherSensorDescription(
        key="scan_page_count",
        data_key="scan_page_count",
        name="Total Pages Scanned",
        icon="mdi:file-multiple",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="pages",
    ),
    BrotherSensorDescription(
        key="total_pages_2sided",
        data_key="total_pages_2sided",
        name="ADF Duplex Pages",
        icon="mdi:file-multiple-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="pages",
    ),
    BrotherSensorDescription(
        key="pickup_roller_pct",
        data_key="pickup_roller_pct",
        name="Pick-up Roller Life",
        icon="mdi:autorenew",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    BrotherSensorDescription(
        key="pickup_roller_pages",
        data_key="pickup_roller_pages",
        name="Pick-up Roller Pages Remaining",
        icon="mdi:autorenew",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="pages",
    ),
    BrotherSensorDescription(
        key="reverse_roller_pct",
        data_key="reverse_roller_pct",
        name="Reverse Roller Life",
        icon="mdi:autorenew",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    BrotherSensorDescription(
        key="reverse_roller_pages",
        data_key="reverse_roller_pages",
        name="Reverse Roller Pages Remaining",
        icon="mdi:autorenew",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="pages",
    ),
    BrotherSensorDescription(
        key="maintenance_pct",
        data_key="maintenance_pct",
        name="Scheduled Maintenance Remaining",
        icon="mdi:wrench-clock",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    BrotherSensorDescription(
        key="maintenance_pages_remaining",
        data_key="maintenance_pages_remaining",
        name="Maintenance Pages Until Service",
        icon="mdi:wrench",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="pages",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BrotherADS2400NCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BrotherSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
    )


class BrotherSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: BrotherADS2400NCoordinator,
        entry: ConfigEntry,
        description: BrotherSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Brother ADS-2400N",
            manufacturer="Brother",
            model="ADS-2400N",
            sw_version=coordinator.data.get("firmware") if coordinator.data else None,
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.data_key)
