"""Manual cookie export for the X source adapter.

Paste auth_token and ct0 from a logged-in browser. Values are not printed back.
This script does not perform opportunity discovery.

Usage:
    python scripts/export_cookies.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _prompt(label: str, required: bool = True) -> str:
    value = input(label).strip()
    if required and not value:
        print("Value cannot be empty.", file=sys.stderr)
        sys.exit(1)
    return value


def export_cookies(output_path: Path = Path("cookies.json")) -> None:
    print("Export X cookies from a browser that is already logged in at https://x.com")
    print("DevTools -> Application -> Cookies -> https://x.com")
    print()
    auth_token = _prompt("Paste auth_token: ")
    ct0 = _prompt("Paste ct0: ")
    twid = _prompt("Paste twid (optional, Enter to skip): ", required=False)

    cookie_dict = {"auth_token": auth_token, "ct0": ct0}
    if twid:
        cookie_dict["twid"] = twid

    try:
        from twikit import Client

        client = Client("en-US")
        client.set_cookies(cookie_dict)
        client.save_cookies(str(output_path))
    except Exception:
        output_path.write_text(json.dumps(cookie_dict, indent=2), encoding="utf-8")

    print(f"Saved session cookies to {output_path} (values not displayed).")


if __name__ == "__main__":
    export_cookies()
