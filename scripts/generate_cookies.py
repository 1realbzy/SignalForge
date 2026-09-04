"""Open a real browser so you can log into X and save session cookies.

This is a manual login helper. It does not type credentials, spoof a
browser fingerprint, or perform searches.

Usage:
    python scripts/generate_cookies.py --browser msedge
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path


async def generate_cookies(browser_choice: str, output_path: Path) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright is not installed. pip install playwright")
        print("Then: python -m playwright install chromium")
        return

    async with async_playwright() as playwright:
        channel = browser_choice if browser_choice in ("msedge", "chrome") else None
        try:
            browser = await playwright.chromium.launch(headless=False, channel=channel)
        except Exception:
            print(f"{browser_choice} channel unavailable; using Chromium.")
            browser = await playwright.chromium.launch(headless=False)

        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
        print("Log in to X in the opened browser window.")
        input("Press ENTER after the home feed is visible...")

        cookies = await context.cookies()
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

        try:
            from twikit import Client

            client = Client("en-US")
            client.set_cookies(cookie_dict)
            client.save_cookies(str(output_path))
        except Exception:
            output_path.write_text(json.dumps(cookie_dict, indent=2), encoding="utf-8")

        print(f"Saved session cookies to {output_path} (values not displayed).")
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Save X cookies after a manual browser login")
    parser.add_argument("--browser", choices=["msedge", "chrome", "chromium"], default="msedge")
    parser.add_argument("--output", default="cookies.json")
    args = parser.parse_args()
    asyncio.run(generate_cookies(args.browser, Path(args.output)))


if __name__ == "__main__":
    main()
