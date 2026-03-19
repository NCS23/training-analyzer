"""Basis-HTTP-Client fuer externe APIs mit Retry und Rate Limiting."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class ExternalAPIClient:
    """Async HTTP-Client mit Rate Limiting und Retry-Logik."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        rate_limit_delay: float = 0.0,
        user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        headers = {"User-Agent": user_agent} if user_agent else {}
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
        )
        self._lock = asyncio.Lock() if rate_limit_delay > 0 else None

    async def get(self, path: str, params: dict | None = None) -> dict | None:
        """GET-Request mit 1x Retry. Gibt None zurück bei Fehler."""
        for attempt in range(2):
            try:
                if self._lock:
                    async with self._lock:
                        response = await self._client.get(path, params=params)
                        await asyncio.sleep(self.rate_limit_delay)
                else:
                    response = await self._client.get(path, params=params)

                if response.status_code == 200:
                    return response.json()

                if response.status_code >= 500 and attempt == 0:
                    logger.warning(
                        "External API %s%s returned %s, retrying...",
                        self.base_url,
                        path,
                        response.status_code,
                    )
                    await asyncio.sleep(1.0)
                    continue

                logger.warning(
                    "External API %s%s returned %s",
                    self.base_url,
                    path,
                    response.status_code,
                )
                return None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == 0:
                    logger.warning(
                        "External API %s%s timeout/error: %s, retrying...",
                        self.base_url,
                        path,
                        e,
                    )
                    await asyncio.sleep(1.0)
                    continue
                logger.warning(
                    "External API %s%s failed after retry: %s",
                    self.base_url,
                    path,
                    e,
                )
                return None

        return None

    async def post_form(self, path: str, data: dict | None = None) -> dict | None:
        """POST mit Form-Data (fuer Overpass API). 1x Retry."""
        for attempt in range(2):
            try:
                response = await self._client.post(path, data=data)
                if response.status_code == 200:
                    return response.json()
                if response.status_code >= 500 and attempt == 0:
                    await asyncio.sleep(2.0)
                    continue
                logger.warning(
                    "External API POST %s%s returned %s",
                    self.base_url,
                    path,
                    response.status_code,
                )
                return None
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == 0:
                    await asyncio.sleep(2.0)
                    continue
                logger.warning("External API POST %s%s failed: %s", self.base_url, path, e)
                return None
        return None

    async def close(self) -> None:
        await self._client.aclose()
