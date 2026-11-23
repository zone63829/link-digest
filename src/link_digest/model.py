"""Unified data model shared by every adapter."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MediaInfo:
    platform: str = "web"
    id: str = ""
    url: str = ""
    title: str = ""
    author: str = ""
    duration: float | None = None
    description: str = ""
    cover: str = ""
    media_url: str = ""
    media_kind: str = ""  # video | audio | page
    subtitles: list[dict[str, Any]] = field(default_factory=list)
    text: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def safe_id(self) -> str:
        raw = (self.id or "item").strip()
        keep = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in raw)
        return (keep or "item")[:80]
