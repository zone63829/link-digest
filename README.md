# link-digest

[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![platform](https://img.shields.io/badge/platform-win%20%7C%20mac%20%7C%20linux-lightgrey.svg)](#requirements)
[![status](https://img.shields.io/badge/status-v0.1.0-brightgreen.svg)](CHANGELOG.md)

**Give it a link. Get back a local digest.** Metadata, transcript, key frames — everything an agent needs to tell you what a video or article actually says.

```bash
link-digest "https://www.douyin.com/video/7710972306511744291" --frames 6 --asr medium
```

```
out/7710972306511744291/
  meta.json        # platform, id, title, author, duration, cover
  media.mp4        # downloaded media (unless --no-download)
  frames/f_*.jpg   # key frames
  transcript.json  # ASR cues (with --asr)
  summary.md       # metadata + transcript + frame list, ready for an LLM
```

## Why

Videos are opaque to agents: no text, no search, no diff. `link-digest` turns one URL into a directory of plain files that any model (or human) can read — without uploading anything to a third-party service.

It is **not** a downloader for pirating content, and it never re-uploads media.

## Quick start

```bash
git clone https://github.com/zone63829/link-digest.git
cd link-digest
pip install -e ".[asr]"          # ASR is optional but recommended

link-digest "https://www.bilibili.com/video/BV1GJ411x7h7" --frames 6 --asr medium
```

Requirements:

- Python 3.10+
- `ffmpeg` on `PATH` (frames + ASR audio extraction)
- optional: Node.js + `playwright-core` for the Douyin adapter
- optional: `faster-whisper` via the `asr` extra

## Supported input

| Kind | How |
|---|---|
| Douyin `v.douyin.com/...`, `www.douyin.com/video/...` | headless Edge via Playwright, captures the detail JSON |
| Bilibili / YouTube / 1000+ sites | yt-dlp |
| any other page | HTML fetch + OG / JSON-LD / `<video>` extraction |

## Tested

| Input | Result |
|---|---|
| Douyin `7710972306511744291` | title + author + 178.3 s + media + 3 frames |
| Bilibili `BV1GJ411x7h7` | 212.4 s + media + 2 frames |
| YouTube `dQw4w9WgXcQ` | 213.0 s + 1080p media + 2 frames |
| `example.com` | title + body text |
| a blog post | title + full article text |

See [`examples/`](examples/) for a real digest.

## Agent skill

The repo ships a portable skill file at [`skills/link-digest/SKILL.md`](skills/link-digest/SKILL.md).
Drop it into your agent's skills directory (Claude Code, DeepSeek Harness, Codex…) and the agent
knows when and how to call the CLI — no extra prompt engineering.

## Compliance

Only use this on content you have the right to access, for personal study or research.
It does not bypass logins, paywalls or captchas, and it never re-uploads media.

## License

MIT © 2026 zone63829 — see [LICENSE](LICENSE).
