"""Fixture-only tests for Twikit 2.2.2 User payload compatibility.

No live X requests. Uses synthetic user/tweet shapes only.
"""

from __future__ import annotations

from twikit.tweet import tweet_from_data
from twikit.user import User

from job_board_tool.ingestion.mapping import tweet_to_raw_post

_CLIENT = object()

_LEGACY_REQUIRED = {
    "description": "legacy bio",
    "possibly_sensitive": False,
    "want_retweets": False,
    "default_profile": False,
    "default_profile_image": False,
    "has_custom_timelines": False,
    "followers_count": 1,
    "fast_followers_count": 0,
    "normal_followers_count": 1,
    "friends_count": 2,
    "favourites_count": 3,
    "listed_count": 4,
    "media_count": 5,
    "statuses_count": 6,
    "is_translator": False,
    "translator_type": "none",
}


def _legacy_user() -> dict:
    return {
        "rest_id": "u-legacy",
        "is_blue_verified": False,
        "legacy": {
            **_LEGACY_REQUIRED,
            "created_at": "Mon Jan 01 00:00:00 +0000 2020",
            "name": "Legacy Name",
            "screen_name": "legacy_user",
            "profile_image_url_https": "https://example.com/legacy.jpg",
            "location": "Accra",
            "entities": {"description": {"urls": ["https://legacy.example"]}},
            "pinned_tweet_ids_str": ["111"],
            "verified": True,
            "can_dm": True,
            "can_media_tag": True,
            "withheld_in_countries": ["xx"],
        },
    }


def _relocated_user() -> dict:
    return {
        "rest_id": "u-relocated",
        "is_blue_verified": False,
        "core": {
            "created_at": "Tue Jan 02 00:00:00 +0000 2020",
            "name": "Relocated Name",
            "screen_name": "relocated_user",
        },
        "avatar": {"image_url": "https://example.com/relocated.jpg"},
        "location": {"location": "Remote"},
        "verification": {"verified": False},
        "dm_permissions": {"can_dm": False},
        "media_permissions": {"can_media_tag": False},
        "legacy": {
            **_LEGACY_REQUIRED,
            "entities": {"description": {}},
        },
    }


def _tweet_legacy() -> dict:
    return {
        "created_at": "Fri Feb 20 13:24:03 +0000 2026",
        "full_text": "We are hiring a nurse https://example.com/jobs/1",
        "lang": "en",
        "is_quote_status": False,
        "quote_count": 0,
        "entities": {},
        "reply_count": 0,
        "favorite_count": 0,
        "favorited": False,
        "retweet_count": 0,
    }


def _tweet_item(user_data: dict) -> dict:
    return {
        "entryId": "tweet-99",
        "content": {
            "itemContent": {
                "tweet_results": {
                    "result": {
                        "__typename": "Tweet",
                        "rest_id": "99",
                        "legacy": _tweet_legacy(),
                        "edit_control": {},
                        "core": {"user_results": {"result": user_data}},
                    }
                }
            }
        },
    }


def test_legacy_user_payload_still_parses() -> None:
    user = User(_CLIENT, _legacy_user())
    assert user.id == "u-legacy"
    assert user.created_at == "Mon Jan 01 00:00:00 +0000 2020"
    assert user.name == "Legacy Name"
    assert user.screen_name == "legacy_user"
    assert user.profile_image_url == "https://example.com/legacy.jpg"
    assert user.location == "Accra"
    assert user.description_urls == ["https://legacy.example"]
    assert user.pinned_tweet_ids == ["111"]
    assert user.verified is True
    assert user.can_dm is True
    assert user.can_media_tag is True
    assert user.withheld_in_countries == ["xx"]


def test_relocated_user_payload_reads_new_fields() -> None:
    user = User(_CLIENT, _relocated_user())
    assert user.id == "u-relocated"
    assert user.created_at == "Tue Jan 02 00:00:00 +0000 2020"
    assert user.name == "Relocated Name"
    assert user.screen_name == "relocated_user"
    assert user.profile_image_url == "https://example.com/relocated.jpg"
    assert user.location == "Remote"
    assert user.verified is False
    assert user.can_dm is False
    assert user.can_media_tag is False
    assert user.description_urls == []
    assert user.pinned_tweet_ids == []
    assert user.withheld_in_countries == []


def test_relocated_field_is_used_when_present_even_if_legacy_exists() -> None:
    data = _legacy_user()
    data["core"] = {
        "created_at": "Wed Jan 03 00:00:00 +0000 2020",
        "name": "Core Name",
        "screen_name": "core_user",
    }
    user = User(_CLIENT, data)
    assert user.created_at == "Wed Jan 03 00:00:00 +0000 2020"
    assert user.name == "Core Name"
    assert user.screen_name == "core_user"
    assert user.location == "Accra"


def test_legacy_description_urls_preserved_when_present() -> None:
    data = _relocated_user()
    data["legacy"]["entities"] = {
        "description": {"urls": ["https://kept.example"]},
        "url": None,
    }
    user = User(_CLIENT, data)
    assert user.description_urls == ["https://kept.example"]
    assert user.urls is None


def test_relocated_search_item_maps_to_raw_post() -> None:
    tweet = tweet_from_data(_CLIENT, _tweet_item(_relocated_user()))
    assert tweet is not None
    assert tweet.id == "99"
    assert tweet.text == "We are hiring a nurse https://example.com/jobs/1"
    assert tweet.user.screen_name == "relocated_user"
    post = tweet_to_raw_post(tweet, discovered_via="we're hiring")
    assert post is not None
    assert post.source == "x"
    assert post.source_id == "99"
    assert post.author_username == "relocated_user"
    assert "https://example.com/jobs/1" in post.text
