"""Unit tests for generic X/Twitter ingestion. No live X requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pytest

from job_board_tool.ingestion.errors import XAuthError, XRateLimited
from job_board_tool.ingestion.mapping import tweet_to_raw_post
from job_board_tool.ingestion.models import RawPost
from job_board_tool.ingestion.x_source import XSourceConfig, XTwitterSource


class FakeUser:
    def __init__(
        self,
        screen_name: Optional[str] = "acme_hire",
        name: Optional[str] = "Acme Hiring",
        location: Optional[str] = "Remote",
        description: Optional[str] = "We post roles",
        user_id: Optional[str] = "u1",
    ) -> None:
        self.screen_name = screen_name
        self.name = name
        self.location = location
        self.description = description
        self.id = user_id


_MISSING = object()


class FakeTweet:
    def __init__(
        self,
        tweet_id: Optional[str] = "123",
        text: Optional[str] = "Apply here: https://example.com/jobs/123",
        created_at: Optional[str] = "Fri Feb 20 13:24:03 +0000 2026",
        user: Any = _MISSING,
        lang: str = "en",
        favorite_count: int = 4,
        retweet_count: int = 1,
        reply_count: int = 2,
    ) -> None:
        self.id = tweet_id
        self.text = text
        self.created_at = created_at
        self.user = FakeUser() if user is _MISSING else user
        self.lang = lang
        self.favorite_count = favorite_count
        self.retweet_count = retweet_count
        self.reply_count = reply_count


class FakeSearchPage:
    def __init__(self, tweets: list[FakeTweet], nxt: Optional["FakeSearchPage"] = None) -> None:
        self._tweets = tweets
        self._next = nxt

    def __iter__(self):
        return iter(self._tweets)

    def __bool__(self) -> bool:
        return bool(self._tweets)

    async def next(self) -> Optional["FakeSearchPage"]:
        return self._next


class FakeClient:
    def __init__(self) -> None:
        self.loaded_cookies: list[str] = []
        self.saved_cookies: list[str] = []
        self.login_calls: list[tuple[str, str, str]] = []
        self.search_calls: list[tuple[str, str, int]] = []
        self._pages_by_query: dict[str, FakeSearchPage] = {}
        self._search_errors: list[BaseException] = []
        self.login_error: Optional[BaseException] = None
        self.load_error: Optional[BaseException] = None

    def set_page(self, query: str, page: FakeSearchPage) -> None:
        self._pages_by_query[query] = page

    def queue_search_error(self, error: BaseException) -> None:
        self._search_errors.append(error)

    def load_cookies(self, path: str) -> None:
        if self.load_error:
            raise self.load_error
        self.loaded_cookies.append(path)

    def save_cookies(self, path: str) -> None:
        self.saved_cookies.append(path)

    async def login(self, username: str, email: str, password: str) -> None:
        if self.login_error:
            raise self.login_error
        self.login_calls.append((username, email, password))

    async def search(self, query: str, product: str, count: int) -> Optional[FakeSearchPage]:
        self.search_calls.append((query, product, count))
        if self._search_errors:
            raise self._search_errors.pop(0)
        return self._pages_by_query.get(query)


class RecordingSleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def _source(client: FakeClient, **kwargs: Any) -> XTwitterSource:
    config = XSourceConfig(
        rate_limit_sleep_seconds=9.0,
        retry_base_seconds=2.0,
        retry_max_seconds=8.0,
        max_retries=3,
        inter_query_delay_seconds=0.0,
        inter_page_delay_seconds=0.0,
        **kwargs,
    )
    sleeper = RecordingSleeper()
    source = XTwitterSource(client=client, config=config, sleep=sleeper)
    source._test_sleeper = sleeper  # type: ignore[attr-defined]
    return source


async def _collect(source: XTwitterSource, **kwargs: Any) -> list[RawPost]:
    return [post async for post in source.discover(**kwargs)]


def test_tweet_to_raw_post_preserves_id_text_url_and_provenance() -> None:
    tweet = FakeTweet()
    post = tweet_to_raw_post(tweet, discovered_via="example query 1")

    assert post.source == "x"
    assert post.source_id == "123"
    assert post.text == "Apply here: https://example.com/jobs/123"
    assert post.author_username == "acme_hire"
    assert post.author_display_name == "Acme Hiring"
    assert post.created_at == "Fri Feb 20 13:24:03 +0000 2026"
    assert post.url == "https://x.com/acme_hire/status/123"
    assert post.author_location == "Remote"
    assert post.author_bio == "We post roles"
    assert post.discovered_via == "example query 1"
    assert post.raw_data["id"] == "123"
    json.dumps(post.raw_data)


def test_tweet_to_raw_post_does_not_invent_url_without_username() -> None:
    tweet = FakeTweet(user=FakeUser(screen_name=None))
    post = tweet_to_raw_post(tweet, discovered_via="q")
    assert post.url is None
    assert post.author_username is None


def test_tweet_to_raw_post_handles_missing_user_and_fields() -> None:
    tweet = FakeTweet(tweet_id="99", text="hello", created_at=None, user=None)
    post = tweet_to_raw_post(tweet, discovered_via="q")
    assert post.source_id == "99"
    assert post.text == "hello"
    assert post.created_at is None
    assert post.author_username is None
    assert post.author_display_name is None
    assert post.author_location is None
    assert post.author_bio is None
    assert post.url is None


@pytest.mark.asyncio
async def test_authenticate_loads_cookies_when_file_exists(tmp_path: Path) -> None:
    cookies = tmp_path / "cookies.json"
    cookies.write_text("{}", encoding="utf-8")
    client = FakeClient()
    source = _source(client, cookies_path=cookies)

    await source.authenticate()

    assert client.loaded_cookies == [str(cookies)]
    assert client.login_calls == []
    assert client.search_calls == []


@pytest.mark.asyncio
async def test_authenticate_logs_in_when_cookies_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TWITTER_USERNAME", "demo_user")
    monkeypatch.setenv("TWITTER_EMAIL", "demo@example.com")
    monkeypatch.setenv("TWITTER_PASSWORD", "demo-pass")
    client = FakeClient()
    source = _source(client, cookies_path=tmp_path / "missing-cookies.json")

    await source.authenticate()

    assert client.login_calls == [("demo_user", "demo@example.com", "demo-pass")]
    assert client.saved_cookies == [str(tmp_path / "missing-cookies.json")]
    assert client.search_calls == []


@pytest.mark.asyncio
async def test_authenticate_raises_when_no_cookies_or_credentials(tmp_path: Path) -> None:
    client = FakeClient()
    source = _source(client, cookies_path=tmp_path / "missing-cookies.json")
    with pytest.raises(XAuthError):
        await source.authenticate()


@pytest.mark.asyncio
async def test_discover_maps_search_results_and_preserves_urls() -> None:
    client = FakeClient()
    client.set_page(
        "example query 1",
        FakeSearchPage([FakeTweet(text="Apply here: https://example.com/jobs/123")]),
    )
    source = _source(client)

    posts = await _collect(source, queries=["example query 1"], count=10, max_pages=1)

    assert len(posts) == 1
    assert posts[0].source == "x"
    assert posts[0].source_id == "123"
    assert "https://example.com/jobs/123" in posts[0].text
    assert posts[0].discovered_via == "example query 1"
    assert client.search_calls == [("example query 1", "Latest", 10)]


@pytest.mark.asyncio
async def test_discover_paginates_without_exposing_twikit_next() -> None:
    client = FakeClient()
    page2 = FakeSearchPage([FakeTweet(tweet_id="2", text="second")])
    page1 = FakeSearchPage([FakeTweet(tweet_id="1", text="first")], nxt=page2)
    client.set_page("q", page1)
    source = _source(client)

    posts = await _collect(source, queries=["q"], count=20, max_pages=5)

    assert [p.source_id for p in posts] == ["1", "2"]
    assert client.search_calls == [("q", "Latest", 20)]


@pytest.mark.asyncio
async def test_discover_runs_multiple_queries_in_order() -> None:
    client = FakeClient()
    client.set_page("example query 1", FakeSearchPage([FakeTweet(tweet_id="a", text="one")]))
    client.set_page("example query 2", FakeSearchPage([FakeTweet(tweet_id="b", text="two")]))
    source = _source(client)

    posts = await _collect(
        source,
        queries=["example query 1", "example query 2"],
        count=5,
        max_pages=1,
    )

    assert [p.source_id for p in posts] == ["a", "b"]
    assert [p.discovered_via for p in posts] == ["example query 1", "example query 2"]
    assert [call[0] for call in client.search_calls] == ["example query 1", "example query 2"]


@pytest.mark.asyncio
async def test_discover_skips_tweets_missing_id_or_text() -> None:
    client = FakeClient()
    client.set_page(
        "q",
        FakeSearchPage(
            [
                FakeTweet(tweet_id=None, text="no id"),
                FakeTweet(tweet_id="ok", text=None),
                FakeTweet(tweet_id="kept", text="valid post"),
            ]
        ),
    )
    source = _source(client)

    posts = await _collect(source, queries=["q"], max_pages=1)
    assert [p.source_id for p in posts] == ["kept"]


@pytest.mark.asyncio
async def test_rate_limit_sleeps_then_retries_search() -> None:
    client = FakeClient()
    client.queue_search_error(XRateLimited("limited"))
    client.set_page("q", FakeSearchPage([FakeTweet(tweet_id="after", text="ok")]))
    source = _source(client)

    posts = await _collect(source, queries=["q"], max_pages=1)

    assert [p.source_id for p in posts] == ["after"]
    assert source._test_sleeper.delays == [9.0]  # type: ignore[attr-defined]
    assert len(client.search_calls) == 2


@pytest.mark.asyncio
async def test_retry_backoff_then_succeeds() -> None:
    client = FakeClient()
    client.queue_search_error(RuntimeError("temporary"))
    client.queue_search_error(RuntimeError("still temporary"))
    client.set_page("q", FakeSearchPage([FakeTweet(tweet_id="ok", text="recovered")]))
    source = _source(client)

    posts = await _collect(source, queries=["q"], max_pages=1)

    assert posts[0].source_id == "ok"
    assert source._test_sleeper.delays == [2.0, 4.0]  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_retry_exhaustion_is_observable() -> None:
    client = FakeClient()
    client.queue_search_error(RuntimeError("boom1"))
    client.queue_search_error(RuntimeError("boom2"))
    client.queue_search_error(RuntimeError("boom3"))
    client.queue_search_error(RuntimeError("boom4"))
    source = _source(client)

    with pytest.raises(RuntimeError, match="boom4"):
        await _collect(source, queries=["q"], max_pages=1)


@pytest.mark.asyncio
async def test_health_check_is_explicit_and_not_run_during_authenticate(
    tmp_path: Path,
) -> None:
    cookies = tmp_path / "cookies.json"
    cookies.write_text("{}", encoding="utf-8")
    client = FakeClient()
    client.set_page("hello", FakeSearchPage([FakeTweet()]))
    source = _source(client, cookies_path=cookies)

    await source.authenticate()
    assert client.search_calls == []

    ok = await source.health_check(query="hello")
    assert ok is True
    assert client.search_calls == [("hello", "Latest", 1)]


@pytest.mark.asyncio
async def test_source_does_not_persist_or_dedupe() -> None:
    client = FakeClient()
    client.set_page(
        "q",
        FakeSearchPage(
            [
                FakeTweet(tweet_id="dup", text="same"),
                FakeTweet(tweet_id="dup", text="same"),
            ]
        ),
    )
    source = _source(client)
    posts = await _collect(source, queries=["q"], max_pages=1)
    assert [p.source_id for p in posts] == ["dup", "dup"]
