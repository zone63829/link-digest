// Douyin page reader: opens the video page in the locally installed Edge,
// waits for the page's own aweme/detail call, prints a compact JSON line.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const URL_ARG = process.argv[2];
const EDGE = process.env.EDGE_PATH || "C:\\\\Program Files (x86)\\\\Microsoft\\\\Edge\\\\Application\\\\msedge.exe";
const PROFILE = process.env.DY_PROFILE || path.join(process.cwd(), ".tools", "edge-prof");

async function main() {
  if (!URL_ARG) throw new Error("missing url");
  fs.mkdirSync(PROFILE, { recursive: true });
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    executablePath: EDGE,
    headless: true,
    viewport: { width: 1280, height: 800 },
    args: ["--disable-blink-features=AutomationControlled", "--no-first-run"],
  });

  const page = await ctx.newPage();
  let detail = null;
  const pending = new Promise((resolve) => {
    page.on("response", async (resp) => {
      const u = resp.url();
      if (!/aweme\/detail/.test(u)) return;
      try {
        const j = await resp.json();
        if (j && j.aweme_detail) {
          detail = j.aweme_detail;
          resolve(true);
        }
      } catch (_) {
        /* ignore non-JSON */
      }
    });
    setTimeout(() => resolve(false), 45000);
  });

  await page.goto(URL_ARG, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await pending;

  if (!detail) {
    // last resort: read title/description straight from the DOM
    const fallback = await page.evaluate(() => {
      const t = document.querySelector('meta[property="og:title"]');
      const d = document.querySelector('meta[property="og:description"]');
      return {
        title: t ? t.content : document.title,
        description: d ? d.content : "",
      };
    }).catch(() => ({}));
    console.log(JSON.stringify({ error: "detail not captured", fallback }));
    await ctx.close();
    return;
  }

  const v = detail.video || {};
  const urls =
    (v.play_addr && v.play_addr.url_list) ||
    (v.bit_rate && v.bit_rate[0] && v.bit_rate[0].play_addr && v.bit_rate[0].play_addr.url_list) ||
    [];
  console.log(
    JSON.stringify({
      id: detail.aweme_id,
      title: detail.desc || "",
      author: (detail.author && detail.author.nickname) || "",
      duration: (v.duration || 0) / 1000,
      cover: (v.cover && v.cover.url_list && v.cover.url_list[0]) || "",
      media_url: urls[0] || "",
      media_kind: "video",
      extra: {
        like: (detail.statistics && detail.statistics.digg_count) || 0,
        comment: (detail.statistics && detail.statistics.comment_count) || 0,
        share: (detail.statistics && detail.statistics.share_count) || 0,
      },
    })
  );
  await ctx.close();
}

main().catch((err) => {
  console.log(JSON.stringify({ error: String(err && err.message ? err.message : err) }));
  process.exit(0);
});
