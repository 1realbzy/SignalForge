"""Source-level errors. The rest of the app should not import Twikit exceptions."""


class XAuthError(Exception):
    """Authentication material is missing, invalid, or login failed."""


class XRateLimited(Exception):
    """The X client reported a rate-limit response."""
