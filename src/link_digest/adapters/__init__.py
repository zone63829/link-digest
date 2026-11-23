"""Adapter registry: platform name -> fetch(url, **opts) -> MediaInfo."""

from __future__ import annotations

from typing import Callable

from ..model import MediaInfo
from . import douyin, web, ytdlp

_ADAPTERS: dict[str, Callable[..., MediaInfo]] = {
    "douyin": douyin.fetch,
    "bilibili": ytdlp.fetch,
    "youtube": ytdlp.fetch,
    "web": web.fetch,
}

_DOWNLOADERS: dict[str, Callable[..., object]] = {
    "bilibili": ytdlp.download,
    "youtube": ytdlp.download,
}


def pick(platform: str) -> Callable[..., MediaInfo]:
    return _ADAPTERS.get(platform, web.fetch)


def pick_downloader(platform: str):
    """Platforms whose media must be fetched by yt-dlp itself."""
    return _DOWNLOADERS.get(platform)


__all__ = ["pick", "pick_downloader", "douyin", "web", "ytdlp"]
