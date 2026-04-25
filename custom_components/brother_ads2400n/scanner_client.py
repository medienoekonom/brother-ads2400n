"""HTTP client for Brother ADS-2400N web interface (async via aiohttp)."""
from __future__ import annotations

import re
import html
import logging
from typing import Any

import aiohttp

from .const import PATH_STATUS, PATH_INFO

_LOGGER = logging.getLogger(__name__)


class ScannerAuthError(Exception):
    pass


class ScannerConnectionError(Exception):
    pass


class BrotherADS2400NClient:
    def __init__(self, host: str, password: str, port: int = 80, timeout: int = 10) -> None:
        self._host = host
        self._password = password
        self._port = port
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._base_url = f"http://{host}:{port}"

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    @staticmethod
    def _texts(html_body: str) -> list[str]:
        raw = re.findall(r">([^<\n]{1,200})<", html_body)
        return [html.unescape(t).strip() for t in raw if t.strip()]

    @staticmethod
    def _find_after(texts: list[str], label: str) -> str | None:
        label_lower = label.lower()
        for i, t in enumerate(texts):
            if label_lower in t.lower() and i + 1 < len(texts):
                candidate = texts[i + 1].strip()
                if candidate:
                    return candidate
        return None

    @staticmethod
    def _parse_percent(value: str) -> float | None:
        m = re.search(r"([\d.]+)\s*%", value)
        return float(m.group(1)) if m else None

    @staticmethod
    def _parse_int(value: str) -> int | None:
        cleaned = value.replace(",", "")
        m = re.search(r"\d+", cleaned)
        return int(m.group(0)) if m else None

    async def _fetch_page(self, session: aiohttp.ClientSession, path: str) -> str:
        """Fetch a page after login; raises ScannerAuthError or ScannerConnectionError."""
        try:
            # Login
            login_data = {"B1264": self._password, "loginurl": PATH_STATUS}
            async with session.post(
                self._url(PATH_STATUS), data=login_data, timeout=self._timeout
            ) as resp:
                body = await resp.text(encoding="iso-8859-1")

            _LOGGER.debug("Login response length: %d", len(body))
            _LOGGER.debug("Logout in body: %s, B1265 in body: %s",
                          "logout" in body.lower(), "B1265" in body)

            if "logout" not in body.lower() and "B1265" not in body:
                raise ScannerAuthError("Login failed — wrong password?")

            # Fetch target page
            async with session.get(
                self._url(path), timeout=self._timeout
            ) as resp:
                return await resp.text(encoding="iso-8859-1")

        except ScannerAuthError:
            raise
        except aiohttp.ClientError as err:
            raise ScannerConnectionError(f"Connection error: {err}") from err
        except TimeoutError as err:
            raise ScannerConnectionError(f"Timeout: {err}") from err

    async def async_fetch_status(self) -> dict:
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
            body = await self._fetch_page(session, PATH_STATUS)
        texts = self._texts(body)
        status_raw = self._find_after(texts, "Device Status") or "unknown"
        return {"status": status_raw}

    async def async_fetch_info(self) -> dict:
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
            body = await self._fetch_page(session, PATH_INFO)
        texts = self._texts(body)

        data: dict[str, Any] = {}
        data["model"] = self._find_after(texts, "Model Name") or "Brother ADS-2400N"
        data["serial"] = self._find_after(texts, "Serial no.") or ""
        data["firmware"] = self._find_after(texts, "Main Firmware Version") or ""
        raw_mem = self._find_after(texts, "Memory Size")
        data["memory_mb"] = self._parse_int(raw_mem) if raw_mem else None

        pickup_pages = pickup_pct = None
        reverse_pages = reverse_pct = None
        maintenance_pages = maintenance_pct = None
        total_pages_1sided = total_pages_2sided = scan_page_count = None

        for i, t in enumerate(texts):
            tl = t.lower()
            if "pick up roller" in tl or "pickup roller" in tl:
                for j in range(i + 1, min(i + 8, len(texts))):
                    if pickup_pages is None:
                        n = self._parse_int(texts[j])
                        if n and n > 0:
                            pickup_pages = n
                    if pickup_pct is None:
                        p = self._parse_percent(texts[j])
                        if p is not None:
                            pickup_pct = p
            elif "reverse roller" in tl:
                for j in range(i + 1, min(i + 8, len(texts))):
                    if reverse_pages is None:
                        n = self._parse_int(texts[j])
                        if n and n > 0:
                            reverse_pages = n
                    if reverse_pct is None:
                        p = self._parse_percent(texts[j])
                        if p is not None:
                            reverse_pct = p
            elif "scheduled maintenance" in tl:
                for j in range(i + 1, min(i + 8, len(texts))):
                    if maintenance_pages is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            maintenance_pages = n
                    if maintenance_pct is None:
                        p = self._parse_percent(texts[j])
                        if p is not None:
                            maintenance_pct = p
            elif "adf(1-sided)" in tl:
                for j in range(i + 1, min(i + 4, len(texts))):
                    if total_pages_1sided is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            total_pages_1sided = n
            elif "adf(2-sided)" in tl:
                for j in range(i + 1, min(i + 4, len(texts))):
                    if total_pages_2sided is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            total_pages_2sided = n
            elif "scan page count" in tl:
                for j in range(i + 1, min(i + 4, len(texts))):
                    if scan_page_count is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            scan_page_count = n

        data.update({
            "pickup_roller_pages": pickup_pages,
            "pickup_roller_pct": pickup_pct,
            "reverse_roller_pages": reverse_pages,
            "reverse_roller_pct": reverse_pct,
            "maintenance_pages_remaining": maintenance_pages,
            "maintenance_pct": maintenance_pct,
            "total_pages_1sided": total_pages_1sided,
            "total_pages_2sided": total_pages_2sided,
            "scan_page_count": scan_page_count,
        })
        return data

    async def async_fetch_all(self) -> dict:
        """Fetch status + info in two requests (reuse session)."""
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
            status_body = await self._fetch_page(session, PATH_STATUS)
            info_body = await self._fetch_page(session, PATH_INFO)

        result: dict[str, Any] = {}

        # Parse status
        texts = self._texts(status_body)
        result["status"] = self._find_after(texts, "Device Status") or "unknown"

        # Parse info
        texts = self._texts(info_body)
        result["model"] = self._find_after(texts, "Model Name") or "Brother ADS-2400N"
        result["serial"] = self._find_after(texts, "Serial no.") or ""
        result["firmware"] = self._find_after(texts, "Main Firmware Version") or ""
        raw_mem = self._find_after(texts, "Memory Size")
        result["memory_mb"] = self._parse_int(raw_mem) if raw_mem else None

        pickup_pages = pickup_pct = None
        reverse_pages = reverse_pct = None
        maintenance_pages = maintenance_pct = None
        total_pages_1sided = total_pages_2sided = scan_page_count = None

        for i, t in enumerate(texts):
            tl = t.lower()
            if "pick up roller" in tl or "pickup roller" in tl:
                for j in range(i + 1, min(i + 8, len(texts))):
                    if pickup_pages is None:
                        n = self._parse_int(texts[j])
                        if n and n > 0:
                            pickup_pages = n
                    if pickup_pct is None:
                        p = self._parse_percent(texts[j])
                        if p is not None:
                            pickup_pct = p
            elif "reverse roller" in tl:
                for j in range(i + 1, min(i + 8, len(texts))):
                    if reverse_pages is None:
                        n = self._parse_int(texts[j])
                        if n and n > 0:
                            reverse_pages = n
                    if reverse_pct is None:
                        p = self._parse_percent(texts[j])
                        if p is not None:
                            reverse_pct = p
            elif "scheduled maintenance" in tl:
                for j in range(i + 1, min(i + 8, len(texts))):
                    if maintenance_pages is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            maintenance_pages = n
                    if maintenance_pct is None:
                        p = self._parse_percent(texts[j])
                        if p is not None:
                            maintenance_pct = p
            elif "adf(1-sided)" in tl:
                for j in range(i + 1, min(i + 4, len(texts))):
                    if total_pages_1sided is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            total_pages_1sided = n
            elif "adf(2-sided)" in tl:
                for j in range(i + 1, min(i + 4, len(texts))):
                    if total_pages_2sided is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            total_pages_2sided = n
            elif "scan page count" in tl:
                for j in range(i + 1, min(i + 4, len(texts))):
                    if scan_page_count is None:
                        n = self._parse_int(texts[j])
                        if n is not None:
                            scan_page_count = n

        result.update({
            "pickup_roller_pages": pickup_pages,
            "pickup_roller_pct": pickup_pct,
            "reverse_roller_pages": reverse_pages,
            "reverse_roller_pct": reverse_pct,
            "maintenance_pages_remaining": maintenance_pages,
            "maintenance_pct": maintenance_pct,
            "total_pages_1sided": total_pages_1sided,
            "total_pages_2sided": total_pages_2sided,
            "scan_page_count": scan_page_count,
        })
        return result
