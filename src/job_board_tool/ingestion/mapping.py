from __future__ import annotations

from typing import Any, Optional

from job_board_tool.ingestion.models import RawPost

_TWEET_SCALARS = (
    "id",
    "text",
    "created_at",
    "lang",
    "favorite_count",
    "retweet_count",
    "reply_count",
    "quote_count",
)
_USER_SCALARS = (
    "id",
    "screen_name",
    "name",
    "location",
    "description",
)


def _attr(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    return getattr(obj, name, None)


def _json_safe(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def tweet_to_raw_post(tweet: Any, discovered_via: Optional[str] = None) -> Optional[RawPost]:
    """Map a Twikit-like tweet object to RawPost.

    Original text is preserved. URLs inside the text are not stripped.
    A canonical X URL is built only when both tweet id and author screen_name exist.
    Missing fields become None. Returns None when id or text is absent.
    """
    source_id = _attr(tweet, "id")
    text = _attr(tweet, "text")
    if source_id is None or text is None or text == "":
        return None

    source_id = str(source_id)
    text = str(text)
    user = _attr(tweet, "user")
    username = _attr(user, "screen_name")
    username = str(username) if username else None
    display_name = _attr(user, "name")
    display_name = str(display_name) if display_name else None
    location = _attr(user, "location")
    location = str(location) if location else None
    bio = _attr(user, "description")
    bio = str(bio) if bio else None
    created_at = _attr(tweet, "created_at")
    created_at = str(created_at) if created_at else None

    url = None
    if username:
        url = f"https://x.com/{username}/status/{source_id}"

    raw_data: dict[str, Any] = {}
    for key in _TWEET_SCALARS:
        value = _attr(tweet, key)
        if _json_safe(value):
            raw_data[key] = value

    if user is not None:
        user_data: dict[str, Any] = {}
        for key in _USER_SCALARS:
            value = _attr(user, key)
            if _json_safe(value):
                user_data[key] = value
        raw_data["user"] = user_data

    return RawPost(
        source="x",
        source_id=source_id,
        text=text,
        author_username=username,
        author_display_name=display_name,
        created_at=created_at,
        url=url,
        author_location=location,
        author_bio=bio,
        discovered_via=discovered_via,
        raw_data=raw_data,
    )
