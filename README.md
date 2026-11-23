# link-digest

Give it a link. Get back a local digest.

```
link-digest <url> [--frames 6] [--asr medium] [--out ./out] [--json]
```

## What it produces

```
out/<id>/
  meta.json        # platform, id, title, author, duration, cover, media url
  media.mp4        # downloaded video/audio (when available)
  frames/f_001.jpg # key frames (fps=1/8 by default)
  transcript.json  # ASR cues (when faster-whisper is installed)
  summary.md       # metadata + transcript + frame list, ready for an LLM to summarize
```

## Supported input

| Kind | How |
|---|---|
| Douyin (`v.douyin.com/...`, `www.douyin.com/video/...`) | headless Edge via Playwright (`playwright-core`) |
| Bilibili / YouTube / 1000+ sites | yt-dlp |
| any other page | plain HTML fetch + OG / JSON-LD / `<video>` extraction |

## Requirements

- Python 3.10+
- `ffmpeg` on `PATH` (frames + ASR audio)
- optional: `faster-whisper` (`pip install link-digest[asr]`) for transcription
- optional: Node.js + `playwright-core` for the Douyin adapter

## Compliance

Only use this on content you have the right to access, for personal study.
It does not bypass logins, paywalls, or captchas, and it never re-uploads media.

## License

MIT
## Tested

| Input | Result |
|---|---|
| `https://www.douyin.com/video/<id>` | title, author, 178s duration, mp4 + frames |
| `https://www.bilibili.com/video/BV...` | title, author, 212s duration, mp4 + frames |
| any article page | title, og:image, cleaned body text |
| `https://www.youtube.com/watch?v=...` | needs a reachable network; otherwise reports the yt-dlp error clearly |

## Notes

- Douyin needs Node.js plus `playwright-core` (`npm i playwright-core`) and a local Microsoft Edge install. Point at them with `--playwright-path` and `--edge-path`.
- Behind a restricted network, YouTube and some hosts are unreachable; the CLI prints the underlying yt-dlp error instead of pretending to work.
- Transcription is optional: `pip install "link-digest[asr]"`, then `--asr medium`.
- Output is written under `out/<id>/`; `--json` prints the metadata to stdout.
