"""Binary sensors for Brother ADS-2400N."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BrotherADS2400NCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BrotherADS2400NCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BrotherOnlineSensor(coordinator, entry),
        BrotherReadySensor(coordinator, entry),
    ])


class BrotherOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Online"
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator: BrotherADS2400NCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Brother ADS-2400N",
            manufacturer="Brother",
            model="ADS-2400N",
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None


class BrotherReadySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_name = "Ready"
    _attr_icon = "mdi:scanner"

    def __init__(self, coordinator: BrotherADS2400NCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ready"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Brother ADS-2400N",
            manufacturer="Brother",
            model="ADS-2400N",
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        status = (self.coordinator.data.get("status") or "").lower()
        return status in ("ready", "scanning", "warming up")
