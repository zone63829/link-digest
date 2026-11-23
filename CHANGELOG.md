# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

## [0.1.0] - 2026-11-23

### Added

- CLI `link-digest <url>` producing `meta.json`, `media.mp4`, `frames/`, `transcript.json`, `summary.md`
- Platform adapters:
  - **Douyin** — headless Edge (Playwright) captures the detail JSON, no cookies needed
  - **Bilibili / YouTube / 1000+ sites** — yt-dlp (`-J` metadata, capped at 1080p)
  - **Web** — OG / JSON-LD / article body / `<video>` extraction
- Key frames via ffmpeg (`--frames`, `--fps`)
- Optional transcription via faster-whisper (`--asr tiny|small|medium|large-v3`, `--lang`)
- `--no-download` (metadata only) and `--json` (machine-readable) modes
- Portable agent skill at `skills/link-digest/SKILL.md`
- Example digest under `examples/`

### Fixed

- Playwright temp dir EPERM on read-only temp locations (`LINK_DIGEST_TMP`, auto fallback)
- `CERTIFICATE_VERIFY_FAILED` on standalone Python builds (certifi fallback)
- Frame-count math reversed (N frames used to produce thousands of files)
- Line endings normalized to LF (`.gitattributes`)
