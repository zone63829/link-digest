"""Fallback adapter for ordinary pages: OG / JSON-LD / <video> / body text."""

from __future__ import annotations

import html as html_mod
import json
import re
import urllib.request

from ..model import MediaInfo
from ..resolve import UA, ssl_context

_SCRIPT_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_VIDEO_RE = re.compile(r"<video[^>]+src=[\"']([^\"']+)[\"']", re.I)
_META_RE = re.compile(
    r"<meta[^>]+(?:property|name)=[\"']([^\"']+)[\"'][^>]+content=[\"']([^\"']*)[\"']", re.I
)
_JSONLD_RE = re.compile(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)


def _meta(html: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for key, value in _META_RE.findall(html):
        found.setdefault(key.lower(), html_mod.unescape(value))
    return found


def _jsonld(html: str) -> dict:
    for blob in _JSONLD_RE.findall(html):
        try:
            data = json.loads(blob.strip())
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and (item.get("@type") in ("VideoObject", "Article", "NewsArticle")):
                return item
    return {}


def _text(html: str) -> str:
    body = _SCRIPT_RE.sub(" ", html)
    text = html_mod.unescape(_TAG_RE.sub(" ", body))
    text = _WS_RE.sub(" ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def fetch(url: str, platform: str = "web", **opts) -> MediaInfo:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25, context=ssl_context()) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read(4_000_000)
        final_url = resp.geturl() or url
    page = raw.decode(charset, errors="replace")

    meta = _meta(page)
    ld = _jsonld(page)
    text = _text(page)
    video = _VIDEO_RE.search(page)

    title = meta.get("og:title") or ld.get("name") or ""
    if not title:
        m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
        title = html_mod.unescape(m.group(1)).strip() if m else ""
    author = meta.get("author") or (ld.get("author") or {}).get("name") if isinstance(ld.get("author"), dict) else meta.get("author") or ""

    media_url = (
        (video.group(1) if video else "")
        or meta.get("og:video")
        or meta.get("og:video:url")
        or (ld.get("contentUrl") if isinstance(ld.get("contentUrl"), str) else "")
    )
    if media_url.startswith("//"):
        media_url = "https:" + media_url
    elif media_url.startswith("/"):
        from urllib.parse import urljoin

        media_url = urljoin(final_url, media_url)

    return MediaInfo(
        platform="web",
        id=re.sub(r"\W+", "-", final_url.split("//")[-1])[:60],
        url=final_url,
        title=title,
        author=author or "",
        duration=float(ld["duration"]) if isinstance(ld.get("duration"), (int, float)) else None,
        description=meta.get("og:description") or meta.get("description") or "",
        cover=meta.get("og:image") or "",
        media_url=media_url,
        media_kind="page",
        text=text[:20000],
        source="web",
    )

