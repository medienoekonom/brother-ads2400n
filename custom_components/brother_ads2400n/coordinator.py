"""DataUpdateCoordinator for Brother ADS-2400N."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .scanner_client import BrotherADS2400NClient, ScannerConnectionError, ScannerAuthError

_LOGGER = logging.getLogger(__name__)


class BrotherADS2400NCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: BrotherADS2400NClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            return await self.client.async_fetch_all()
        except ScannerAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except ScannerConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
