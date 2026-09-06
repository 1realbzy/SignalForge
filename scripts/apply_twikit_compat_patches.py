"""Apply temporary Twikit 2.2.2 compatibility patches to an installed package.

Does not import SignalForge ingestion or detection code.
Does not read session files or credentials.
Does not talk to X.

Usage:
    python -m scripts.apply_twikit_compat_patches
    python -m scripts.apply_twikit_compat_patches --target-root <site-packages>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PATCH_DIR = REPO_ROOT / "patches" / "twikit" / "2.2.2"
REQUIRED_VERSION = "2.2.2"

PATCHES: tuple[tuple[str, Path, str], ...] = (
    (
        "0001-4a62e28-transaction-ondemand-regex.patch",
        Path("twikit") / "x_client_transaction" / "transaction.py",
        "ON_DEMAND_HASH_PATTERN",
    ),
    (
        "0002-de9c6f3-search-timeline.patch",
        Path("twikit") / "client" / "gql.py",
        "R0u1RWRf748KzyGBXvOYRA",
    ),
)

_VERSION_RE = re.compile(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)


def _read_version(twikit_init: Path) -> str:
    text = twikit_init.read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    if match is None:
        raise SystemExit(f"Could not read Twikit version from {twikit_init}")
    return match.group(1)


def _resolve_target_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    import twikit

    return Path(twikit.__file__).resolve().parent.parent


def _already_applied(target_root: Path, relative: Path, marker: str) -> bool:
    path = target_root / relative
    if not path.is_file():
        return False
    return marker in path.read_text(encoding="utf-8")


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if data != normalized:
        path.write_bytes(normalized)


def _files_for_patch(name: str) -> tuple[Path, ...]:
    if name.startswith("0001-"):
        return (Path("twikit") / "x_client_transaction" / "transaction.py",)
    return (
        Path("twikit") / "client" / "gql.py",
        Path("twikit") / "constants.py",
    )


def _apply_patch(target_root: Path, patch_path: Path) -> None:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "apply",
            str(patch_path),
        ],
        cwd=target_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise SystemExit(
            f"Failed to apply {patch_path.name} with core.autocrlf=false.\n{detail}"
        )


def apply_patches(target_root: Path) -> int:
    twikit_init = target_root / "twikit" / "__init__.py"
    if not twikit_init.is_file():
        raise SystemExit(f"No twikit package at {target_root / 'twikit'}")

    version = _read_version(twikit_init)
    if version != REQUIRED_VERSION:
        raise SystemExit(
            f"Refusing to patch Twikit {version}; these patches are only for {REQUIRED_VERSION}."
        )

    applied = 0
    skipped = 0
    for name, relative, marker in PATCHES:
        patch_path = PATCH_DIR / name
        if not patch_path.is_file():
            raise SystemExit(f"Missing patch file: {patch_path}")
        if _already_applied(target_root, relative, marker):
            print(f"ALREADY_APPLIED {name}")
            skipped += 1
            continue
        for rel in _files_for_patch(name):
            target = target_root / rel
            if not target.is_file():
                raise SystemExit(f"Missing file for {name}: {target}")
            _normalize_lf(target)
        _apply_patch(target_root, patch_path)
        print(f"APPLIED {name} -> {relative.as_posix()}")
        applied += 1

    if applied == 0:
        print("NOOP all compatibility patches already present")
    else:
        print(f"DONE applied={applied} skipped={skipped}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply temporary twikit==2.2.2 compatibility patches."
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=None,
        help="Directory that contains the twikit package (site-packages). "
        "Defaults to the imported twikit location.",
    )
    args = parser.parse_args(argv)
    return apply_patches(_resolve_target_root(args.target_root))


if __name__ == "__main__":
    raise SystemExit(main())
