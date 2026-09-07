"""Tests for temporary Twikit 2.2.2 compatibility patches. No live X requests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.apply_twikit_compat_patches import PATCH_DIR, PATCHES, apply_patches

REPO_ROOT = Path(__file__).resolve().parents[1]
SHA_411 = "4a62e2895676398e5c2dcce697597abbddb07a2c"
SHA_419 = "de9c6f314f40a3c547ea4dea7cc87ed769b205bb"
PATCH_0001 = PATCH_DIR / "0001-4a62e28-transaction-ondemand-regex.patch"
PATCH_0002 = PATCH_DIR / "0002-de9c6f3-search-timeline.patch"
PATCH_0003 = PATCH_DIR / "0003-user-relocated-fields.patch"


def test_patch_files_exist_and_name_upstream_commits() -> None:
    assert PATCH_0001.is_file()
    assert PATCH_0002.is_file()
    assert PATCH_0003.is_file()
    text_411 = PATCH_0001.read_text(encoding="utf-8")
    text_419 = PATCH_0002.read_text(encoding="utf-8")
    text_user = PATCH_0003.read_text(encoding="utf-8")
    assert SHA_411 in text_411
    assert SHA_419 in text_419
    assert "x_client_transaction/transaction.py" in text_411
    assert "twikit/client/gql.py" in text_419
    assert "twikit/constants.py" in text_419
    assert "twikit/user.py" in text_user
    assert "_relocated_or_legacy" in text_user
    assert SHA_419 not in text_411
    assert SHA_411 not in text_419
    assert "twikit/user.py" not in text_411
    assert "twikit/user.py" not in text_419
    assert "gql.py" not in text_user
    assert "constants.py" not in text_user
    assert "transaction.py" not in text_user


def test_patches_apply_in_order_0001_0002_0003() -> None:
    names = [name for name, _relative, _marker in PATCHES]
    assert names == [
        "0001-4a62e28-transaction-ondemand-regex.patch",
        "0002-de9c6f3-search-timeline.patch",
        "0003-user-relocated-fields.patch",
    ]


def test_apply_script_refuses_wrong_twikit_version(tmp_path: Path) -> None:
    twikit_dir = tmp_path / "twikit"
    twikit_dir.mkdir()
    (twikit_dir / "__init__.py").write_text("__version__ = '2.3.3'\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="only for 2.2.2"):
        apply_patches(tmp_path)


def test_apply_script_is_noop_when_markers_already_present(tmp_path: Path) -> None:
    (tmp_path / "twikit").mkdir()
    (tmp_path / "twikit" / "__init__.py").write_text(
        "__version__ = '2.2.2'\n", encoding="utf-8"
    )
    before: dict[Path, bytes] = {}
    for _name, relative, marker in PATCHES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{marker} = 'present'\n", encoding="utf-8")
        before[relative] = path.read_bytes()

    assert apply_patches(tmp_path) == 0
    for _name, relative, _marker in PATCHES:
        assert (tmp_path / relative).read_bytes() == before[relative]


def test_apply_script_source_does_not_touch_secrets() -> None:
    source = (
        REPO_ROOT / "scripts" / "apply_twikit_compat_patches.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "cookies.json" not in lowered
    assert ".env" not in lowered
    assert "twitter_password" not in lowered
    assert "twitter_username" not in lowered
    assert "auth_token" not in lowered
    for patch_name, _relative, _marker in PATCHES:
        text = (PATCH_DIR / patch_name).read_text(encoding="utf-8").lower()
        assert "cookies.json" not in text
        assert ".env" not in text
        assert "twitter_password" not in text
        assert "auth_token" not in text
