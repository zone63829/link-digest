# Examples

Real outputs from `link-digest`, kept small on purpose (no video files in this repo).

| Folder | Input | What it shows |
|---|---|---|
| `douyin-7710972306511744291/` | `https://www.douyin.com/video/7710972306511744291` | full pipeline: metadata + 2 key frames + an LLM-written summary |
| run it yourself | any URL | see the Quick start in the root README |

Each folder contains:

```
meta.json     # what link-digest extracted
summary.md    # what an agent wrote after reading meta + frames (+ transcript)
frames/       # 1-2 key frames, downscaled
```

## Reproduce

```bash
link-digest "https://www.douyin.com/video/7710972306511744291" --out out --frames 3 --asr medium
```

> The examples folder deliberately excludes `media.mp4`. Downloading and redistributing
> someone else's video is not something this repo does; the tool fetches it locally for you.
