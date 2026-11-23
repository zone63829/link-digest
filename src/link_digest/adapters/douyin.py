"""Douyin adapter: drive the user's real Edge through Playwright and read
the aweme/detail JSON that the page itself requests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from ..model import MediaInfo

_HERE = Path(__file__).resolve().parent


def _node() -> str:
    for name in ("node", "node.exe"):
        exe = shutil.which(name)
        if exe:
            return exe
    raise RuntimeError("Douyin adapter needs Node.js on PATH (install Node 18+).")


def fetch(url: str, platform: str = "douyin", **opts) -> MediaInfo:
    env = dict(os.environ)
    env.setdefault("DY_URL", url)
    if opts.get("playwright_path"):
        base = Path(str(opts["playwright_path"]))
        env["NODE_PATH"] = str(base / "node_modules" if (base / "node_modules").is_dir() else base)
    if opts.get("edge_path"):
        env["EDGE_PATH"] = str(opts["edge_path"])
    if opts.get("profile"):
        env["DY_PROFILE"] = str(opts["profile"])

    # Playwright writes artifacts into the system temp dir; in restricted
    # environments that path is read-only, so redirect it next to the profile.
    profile_dir = Path(env.get("DY_PROFILE") or Path.cwd() / ".tools" / "edge-prof")
    tmp_dir = Path(os.environ.get("LINK_DIGEST_TMP") or (profile_dir.parent / "pw-tmp"))
    tmp_dir.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = env["TMP"] = str(tmp_dir)

    proc = subprocess.run(
        [_node(), str(_HERE / "douyin_browser.cjs"), url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError("Douyin adapter returned nothing.\n" + (proc.stderr or "")[-800:])
    try:
        data = json.loads(out.splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Douyin adapter returned non-JSON: {out[:400]}") from exc
    if data.get("error"):
        raise RuntimeError(f"Douyin adapter failed: {data['error']}")

    return MediaInfo(
        platform="douyin",
        id=str(data.get("id") or ""),
        url=url,
        title=data.get("title") or "",
        author=data.get("author") or "",
        duration=data.get("duration"),
        cover=data.get("cover") or "",
        media_url=data.get("media_url") or "",
        media_kind=data.get("media_kind") or "video",
        extra=data.get("extra") or {},
        source="douyin-browser",
    )
