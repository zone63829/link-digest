---
name: link-digest
description: Turn any link (Douyin / Bilibili / YouTube / plain web page) into a local digest — metadata, transcript/subtitles, key frames — then write the summary. Use when the user pastes a link and asks "what is this about", "summarize it", or "turn it into text".
---

# link-digest skill

`link-digest` splits a link into **metadata + media/text + key frames + transcript**, so an agent can then read the frames and write a summary.

## When to use

- The user pastes a link (short video, video site, blog post) and asks what it says / to summarize it
- A video needs to become searchable text
- A few key frames are enough to judge what a clip is about

## Install

```bash
pip install -e .            # from the repo root
pip install -e ".[asr]"     # + faster-whisper for transcription
```

Requirements: Python 3.10+, `ffmpeg` on `PATH`. Douyin additionally needs Node.js + `playwright-core` and a local Edge/Chrome.

## Run

```bash
link-digest "<url>" --out out --frames 6
link-digest "<url>" --out out --frames 6 --asr medium   # + subtitles
link-digest "<url>" --no-download                        # metadata only, cheapest
link-digest "<url>" --json                               # machine-readable meta
```

Douyin needs the browser paths once:

```bash
link-digest "<url>" --out out --frames 6 \
  --playwright-path /path/to/node_modules \
  --edge-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

## Output

```
out/<id>/
  meta.json        # platform, id, title, author, duration, cover, media url
  media.mp4        # downloaded media (unless --no-download)
  frames/f_*.jpg   # key frames
  transcript.json  # ASR cues (with --asr)
  summary.md       # metadata + transcript + frame list
```

Then:

1. read `meta.json` for title / author / duration;
2. look at 3–6 frames (use a vision model or a vision tool);
3. if `transcript.json` exists, quote it; otherwise rely on frames;
4. output: one-sentence verdict + 3–6 bullets (+ optional quotes).

## Rules

- Prefer `--no-download` first: learn the platform and metadata before spending bandwidth.
- Frames: 6 for clips under 1 min, 8–10 for 3 min+; more is wasted tokens.
- Never invent content when a site is unreachable — say it failed.
- Do not bypass logins, paywalls or captchas; only public content the user may access.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `MODULE_NOT_FOUND playwright-core` | Node can't resolve the module | point `--playwright-path` at a dir containing `node_modules` |
| `EPERM mkdtemp` | temp dir is not writable | set `LINK_DIGEST_TMP` to a writable dir |
| `CERTIFICATE_VERIFY_FAILED` | Python has no CA bundle | `pip install certifi` (already used as fallback) |
| `Fresh cookies ... needed` | Douyin risk control | open Douyin once in the browser, then retry |
| console shows garbled Chinese | GBK console, UTF-8 files | trust the files, not the console |
