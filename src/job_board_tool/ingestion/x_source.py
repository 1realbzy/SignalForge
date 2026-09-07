from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from job_board_tool.ingestion.auth import (
    load_dotenv_if_present,
    resolve_cookies_path,
    twitter_credentials_from_env,
)
from job_board_tool.ingestion.errors import XAuthError, XRateLimited
from job_board_tool.ingestion.mapping import tweet_to_raw_post
from job_board_tool.ingestion.models import RawPost

logger = logging.getLogger(__name__)

SleepFn = Callable[[float], Awaitable[None]]


class SearchPage(Protocol):
    def __iter__(self): ...

    async def next(self) -> Optional["SearchPage"]: ...


class XClient(Protocol):
    def load_cookies(self, path: str) -> None: ...

    def save_cookies(self, path: str) -> None: ...

    async def login(self, username: str, email: str, password: str) -> None: ...

    async def search(self, query: str, product: str, count: int) -> Optional[SearchPage]: ...


@dataclass
class XSourceConfig:
    cookies_path: Path = Path("cookies.json")
    language: str = "en-US"
    rate_limit_sleep_seconds: float = 900.0
    retry_base_seconds: float = 30.0
    retry_max_seconds: float = 600.0
    max_retries: int = 5
    inter_query_delay_seconds: float = 0.0
    inter_page_delay_seconds: float = 0.0


class XTwitterSource:
    """Generic X/Twitter search source.

    Queries are supplied by the caller. This class does not perform job- or
    domain-specific filtering. It yields RawPost records.
    """

    def __init__(
        self,
        client: Optional[XClient] = None,
        config: Optional[XSourceConfig] = None,
        sleep: Optional[SleepFn] = None,
    ) -> None:
        self._client = client
        self.config = config or XSourceConfig()
        self._sleep = sleep or asyncio.sleep

    def _get_client(self) -> XClient:
        if self._client is None:
            from job_board_tool.ingestion.twikit_adapter import TwikitXClient

            self._client = TwikitXClient(language=self.config.language)
        return self._client

    async def authenticate(self) -> None:
        """Load cookies or log in. Does not perform a search probe."""
        load_dotenv_if_present()
        client = self._get_client()
        cookies_path = resolve_cookies_path(self.config.cookies_path)

        if cookies_path.exists():
            try:
                client.load_cookies(str(cookies_path))
                logger.info("Loaded X session cookies from configured cookies path.")
                return
            except Exception as exc:
                logger.warning("Could not load cookies; will try credential login if configured.")
                logger.debug("Cookie load failure: %s", type(exc).__name__)

        credentials = twitter_credentials_from_env()
        if credentials is None:
            raise XAuthError(
                "No X session cookies and no TWITTER_USERNAME/TWITTER_EMAIL/"
                "TWITTER_PASSWORD environment variables."
            )

        username, email, password = credentials
        try:
            await client.login(username, email, password)
            client.save_cookies(str(cookies_path))
            logger.info("X credential login succeeded; cookies saved to configured path.")
        except XAuthError:
            raise
        except Exception as exc:
            raise XAuthError("X credential login failed.") from exc

    async def health_check(self, query: str = "hello") -> bool:
        """Optional live check. Call explicitly; not invoked by authenticate()."""
        try:
            await self._search_with_retry(query, "Latest", 1)
            return True
        except Exception:
            logger.exception("X health check failed.")
            return False

    async def discover(
        self,
        queries: Sequence[str],
        *,
        count: int = 50,
        max_pages: int = 20,
        product: str = "Latest",
    ) -> AsyncIterator[RawPost]:
        """Yield RawPost records for caller-supplied search queries."""
        client = self._get_client()
        last_index = len(queries) - 1
        for index, query in enumerate(queries):
            logger.info("Searching X query %s/%s", index + 1, len(queries))
            page = await self._search_with_retry(query, product, count)
            pages_fetched = 0
            while page and pages_fetched < max_pages:
                pages_fetched += 1
                for tweet in page:
                    post = tweet_to_raw_post(tweet, discovered_via=query)
                    if post is None:
                        continue
                    yield post

                if pages_fetched >= max_pages:
                    break
                if self.config.inter_page_delay_seconds:
                    await self._sleep(self.config.inter_page_delay_seconds)
                page = await self._next_page(page)

            if index < last_index and self.config.inter_query_delay_seconds:
                await self._sleep(self.config.inter_query_delay_seconds)

    async def _search_with_retry(self, query: str, product: str, count: int) -> Optional[SearchPage]:
        client = self._get_client()
        consecutive_errors = 0
        while True:
            try:
                return await client.search(query, product, count)
            except XRateLimited:
                logger.warning(
                    "X search rate-limited; sleeping %.0f seconds before retry.",
                    self.config.rate_limit_sleep_seconds,
                )
                await self._sleep(self.config.rate_limit_sleep_seconds)
                consecutive_errors = 0
            except Exception as exc:
                consecutive_errors += 1
                if consecutive_errors > self.config.max_retries:
                    logger.error("X search failed after %s retries.", self.config.max_retries)
                    raise
                delay = min(
                    self.config.retry_base_seconds * (2 ** (consecutive_errors - 1)),
                    self.config.retry_max_seconds,
                )
                logger.error(
                    "X search error (%s); backing off for %.1f seconds.",
                    type(exc).__name__,
                    delay,
                )
                await self._sleep(delay)

    async def _next_page(self, page: SearchPage) -> Optional[SearchPage]:
        try:
            return await page.next()
        except XRateLimited:
            logger.warning(
                "X pagination rate-limited; sleeping %.0f seconds before retry.",
                self.config.rate_limit_sleep_seconds,
            )
            await self._sleep(self.config.rate_limit_sleep_seconds)
            try:
                return await page.next()
            except Exception:
                logger.exception("Pagination retry failed.")
                return None
        except Exception:
            logger.info("Stopping pagination for this query.")
            return None
