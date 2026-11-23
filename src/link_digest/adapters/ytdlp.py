"""Generic yt-dlp adapter: covers Bilibili, YouTube and 1000+ other sites."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

from ..model import MediaInfo


def _cmd() -> list[str]:
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    return [sys.executable, "-m", "yt_dlp"]


def _js_runtime() -> list[str]:
    """YouTube needs a JS runtime for signature solving; node is usually present."""
    if shutil.which("node"):
        return ["--js-runtimes", "node"]
    return []


def fetch(url: str, platform: str = "web", **opts) -> MediaInfo:
    args = _cmd() + ["--no-warnings", "--no-playlist"] + _js_runtime() + ["-J", url]
    if opts.get("cookies"):
        args[1:1] = ["--cookies", str(opts["cookies"])]
    proc = subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240
    )
    if proc.returncode != 0:
        raise RuntimeError("yt-dlp failed: " + (proc.stderr or proc.stdout or "")[-900:])
    info = json.loads(proc.stdout)

    best = None
    for fmt in info.get("formats") or []:
        if not fmt.get("url"):
            continue
        has_v = fmt.get("vcodec") not in (None, "none")
        has_a = fmt.get("acodec") not in (None, "none")
        if has_v and has_a:
            if best is None or (fmt.get("height") or 0) > (best.get("height") or 0):
                best = fmt
    if best is None:
        with_url = [f for f in (info.get("formats") or []) if f.get("url")]
        best = max(with_url, key=lambda f: (f.get("height") or 0), default=None)

    subs = []
    for lang, items in (info.get("subtitles") or {}).items():
        for item in items[:2]:
            subs.append({"lang": lang, "ext": item.get("ext"), "url": item.get("url")})

    return MediaInfo(
        platform=platform,
        id=str(info.get("id") or ""),
        url=info.get("webpage_url") or url,
        title=info.get("title") or "",
        author=info.get("uploader") or info.get("channel") or "",
        duration=float(info["duration"]) if info.get("duration") else None,
        description=(info.get("description") or "")[:4000],
        cover=info.get("thumbnail") or "",
        media_url=(best or {}).get("url", ""),
        media_kind="video" if best else "",
        subtitles=subs,
        extra={
            "extractor": info.get("extractor"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
        },
        source="yt-dlp",
    )
def download(url: str, dest, **opts) -> "object":
    """Let yt-dlp fetch the media: it handles googlevideo headers, DASH merging
    and Referer requirements that a plain HTTP GET would miss."""
    from pathlib import Path as _P

    dest = _P(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    args = _cmd() + _js_runtime() + [
        "--no-warnings", "--no-playlist",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b", "--merge-output-format", "mp4",
        "-o", str(dest), url,
    ]
    if opts.get("cookies"):
        args[1:1] = ["--cookies", str(opts["cookies"])]
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=3600)
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError("yt-dlp download failed: " + (proc.stderr or "")[-600:])
    return dest
