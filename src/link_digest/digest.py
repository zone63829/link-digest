"""Media work: download, key frames, optional transcription."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import wave
from pathlib import Path

from .resolve import UA, ssl_context


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH (needed for frames and audio).")
    return exe


def download(url: str, dest: Path, referer: str = "") -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60, context=ssl_context()) as resp, open(dest, "wb") as fh:
        shutil.copyfileobj(resp, fh, 1024 * 512)
    return dest


def grab_frames(
    media: Path,
    out_dir: Path,
    count: int = 0,
    fps: str = "1/8",
    max_width: int = 720,
    duration: float | None = None,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("f_*.jpg"):
        old.unlink()
    rate = fps
    if count and duration and duration > 0:
        # count frames spread over the whole clip -> frames per second
        rate = f"{max(count / duration, 0.0001):.5f}"
    scale = f"scale='min({max_width},iw)':-2"
    cmd = [
        ffmpeg(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(media),
        "-vf",
        f"fps={rate},{scale}",
        "-q:v",
        "3",
        str(out_dir / "f_%03d.jpg"),
    ]
    subprocess.run(cmd, check=True, timeout=600)
    return sorted(out_dir.glob("f_*.jpg"))


def _audio_wav(media: Path, wav: Path) -> Path:
    cmd = [
        ffmpeg(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(media),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-af",
        "highpass=f=90,loudnorm=I=-16:TP=-1.5",
        str(wav),
    ]
    subprocess.run(cmd, check=True, timeout=900)
    return wav


def transcribe(media: Path, model: str = "medium", lang: str = "zh") -> list[dict]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install 'link-digest[asr]'"
        ) from exc

    import numpy as np  # type: ignore

    with tempfile.TemporaryDirectory() as tmp:
        wav = _audio_wav(media, Path(tmp) / "a.wav")
        with wave.open(str(wav), "rb") as fh:
            frames = fh.readframes(fh.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype("float32") / 32768.0
        asr = WhisperModel(model, device="cpu", compute_type="int8")
        segments, _info = asr.transcribe(audio, language=lang, vad_filter=True, beam_size=5)
        cues = []
        for seg in segments:
            text = (seg.text or "").strip()
            if text:
                cues.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": text})
        return cues


def write_outputs(out: Path, info, frames: list[Path], cues: list[dict] | None, media: Path | None):
    out.mkdir(parents=True, exist_ok=True)
    (out / "meta.json").write_text(json.dumps(info.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    if cues is not None:
        (out / "transcript.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        f"# {info.title or info.id}",
        "",
        f"- platform: {info.platform}",
        f"- author: {info.author or '-'}",
        f"- duration: {info.duration if info.duration is not None else '-'}",
        f"- url: {info.url}",
        f"- media: {media.name if media else '-'}",
        "",
    ]
    if frames:
        lines.append(f"## Frames ({len(frames)})")
        lines += [f"- {p.name}" for p in frames]
        lines.append("")
    if cues:
        lines.append(f"## Transcript ({len(cues)} cues)")
        lines.append("")
        lines += [f"[{c['start']:.1f}-{c['end']:.1f}] {c['text']}" for c in cues]
        lines.append("")
    elif info.text:
        lines.append("## Text")
        lines.append("")
        lines.append(info.text[:8000])
        lines.append("")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")

