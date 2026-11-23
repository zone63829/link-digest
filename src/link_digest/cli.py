"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .adapters import pick, pick_downloader
from .digest import download, grab_frames, transcribe, write_outputs
from .resolve import detect, expand, extract_id


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="link-digest",
        description="Turn a link into a local digest: metadata, transcript, key frames.",
    )
    p.add_argument("url", help="any link (short links are expanded)")
    p.add_argument("--out", default="out", help="output root directory (default: out)")
    p.add_argument("--frames", type=int, default=0, help="how many frames to keep (0 = every 8s)")
    p.add_argument("--fps", default="1/8", help="frame sampling rate when --frames is 0")
    p.add_argument("--asr", default="off", help="ASR model: off | tiny | base | small | medium | large-v3")
    p.add_argument("--lang", default="zh", help="ASR language (default: zh)")
    p.add_argument("--no-download", action="store_true", help="metadata only, do not fetch media")
    p.add_argument("--json", action="store_true", help="print the metadata JSON to stdout")
    p.add_argument("--edge-path", default="", help="path to msedge.exe (Douyin adapter)")
    p.add_argument("--playwright-path", default="", help="dir containing node_modules/playwright-core")
    p.add_argument("--cookies", default="", help="cookies.txt for yt-dlp")
    p.add_argument("--version", action="version", version=f"link-digest {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    final_url = expand(args.url)
    platform = detect(final_url)
    vid = extract_id(final_url, platform)

    adapter = pick(platform)
    opts = {
        "edge_path": args.edge_path or None,
        "playwright_path": args.playwright_path or None,
        "cookies": args.cookies or None,
    }
    info = adapter(final_url, platform=platform, **opts)
    info.url = info.url or final_url
    info.id = info.id or vid or "item"

    out = Path(args.out).resolve() / info.safe_id
    out.mkdir(parents=True, exist_ok=True)

    media: Path | None = None
    if not args.no_download:
        suffix = ".mp4" if info.media_kind == "video" else ".bin"
        target = out / f"media{suffix}"
        dl = pick_downloader(platform)
        try:
            if dl is not None:
                media = dl(final_url, target, cookies=args.cookies or None)
            elif info.media_url:
                media = download(info.media_url, target, referer=final_url)
        except Exception as exc:
            print(f"[warn] media download failed: {exc}", file=sys.stderr)

    frames: list[Path] = []
    if media:
        try:
            frames = grab_frames(
                media, out / "frames", count=args.frames, fps=args.fps,
                duration=info.duration,
            )
        except Exception as exc:
            print(f"[warn] frame extraction failed: {exc}", file=sys.stderr)

    cues = None
    if media and args.asr and args.asr != "off":
        try:
            cues = transcribe(media, model=args.asr, lang=args.lang)
        except Exception as exc:
            print(f"[warn] ASR failed: {exc}", file=sys.stderr)

    write_outputs(out, info, frames, cues, media)

    if args.json:
        print(json.dumps(info.to_dict(), ensure_ascii=False, indent=1))
    else:
        print(f"platform : {info.platform}")
        print(f"id       : {info.id}")
        print(f"title    : {info.title}")
        print(f"author   : {info.author or '-'}")
        print(f"duration : {info.duration if info.duration is not None else '-'}")
        print(f"media    : {'yes' if media else 'no'}")
        print(f"frames   : {len(frames)}")
        print(f"cues     : {len(cues) if cues else 0}")
        print(f"out      : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

