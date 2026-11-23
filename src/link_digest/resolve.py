"""URL resolution: follow short links, detect the platform, extract an id."""

from __future__ import annotations

import re
import ssl
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

_RULES = [
    ("douyin", re.compile(r"(?:^|//)(?:v|www)\.douyin\.com/")),
    ("bilibili", re.compile(r"(?:^|//)(?:www\.|m\.)?bilibili\.com/|(?:^|//)b23\.tv/")),
    ("youtube", re.compile(r"(?:^|//)(?:www\.|m\.)?(?:youtube\.com/|youtu\.be/)")),
]

_ID_RULES = [
    ("douyin", re.compile(r"/video/(\d{15,})")),
    ("bilibili", re.compile(r"/video/(BV[0-9A-Za-z]{10})")),
    ("youtube", re.compile(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})")),
]


def ssl_context() -> ssl.SSLContext:
    """Some standalone Python builds ship without a CA bundle; prefer certifi."""
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def detect(url: str) -> str:
    for name, rx in _RULES:
        if rx.search(url or ""):
            return name
    return "web"


def extract_id(url: str, platform: str) -> str:
    for name, rx in _ID_RULES:
        if name == platform:
            m = rx.search(url or "")
            if m:
                return m.group(1)
    return ""


def expand(url: str, timeout: float = 15.0) -> str:
    """Follow redirects without downloading the body when possible."""
    if not re.match(r"^https?://", url or ""):
        url = "https://" + url
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
            final = resp.geturl() or url
            resp.close()
            return final
    except Exception:
        return url
