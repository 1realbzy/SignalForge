from __future__ import annotations

import logging
from typing import Any, Optional

from job_board_tool.ingestion.errors import XRateLimited

logger = logging.getLogger(__name__)


class TwikitXClient:
    """Thin wrapper so XTwitterSource never depends on Twikit types directly."""

    def __init__(self, language: str = "en-US") -> None:
        from twikit import Client

        self._client = Client(language)

    def load_cookies(self, path: str) -> None:
        self._client.load_cookies(path)

    def save_cookies(self, path: str) -> None:
        self._client.save_cookies(path)

    def set_cookies(self, cookies: dict[str, str]) -> None:
        self._client.set_cookies(cookies)

    async def login(self, username: str, email: str, password: str) -> None:
        await self._client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password,
        )

    async def search(self, query: str, product: str, count: int) -> Optional["TwikitSearchPage"]:
        from twikit import TooManyRequests

        try:
            result = await self._client.search_tweet(query, product, count=count)
        except TooManyRequests as exc:
            raise XRateLimited("X search rate-limited") from exc
        if not result:
            return None
        return TwikitSearchPage(result)


class TwikitSearchPage:
    def __init__(self, result: Any) -> None:
        self._result = result

    def __iter__(self):
        return iter(self._result)

    def __bool__(self) -> bool:
        return bool(self._result)

    async def next(self) -> Optional["TwikitSearchPage"]:
        from twikit import TooManyRequests

        try:
            nxt = await self._result.next()
        except TooManyRequests as exc:
            raise XRateLimited("X pagination rate-limited") from exc
        except Exception:
            logger.info("No further search pages available.")
            return None
        if not nxt:
            return None
        return TwikitSearchPage(nxt)
