#!/usr/bin/env python3
"""Download a reference video for private study and scaffold its notes file.

The video file lands in research/raw-videos/<niche>/media/ which is git-ignored.
Only the generated notes file (with the original URL and real metadata) is
committed, so the repo stays light and we never republish someone else's work.

Usage:
    python shared/tools/fetch-reference.py <niche> <url> [--slug my-name]
    python shared/tools/fetch-reference.py <niche> --list urls.txt
    python shared/tools/fetch-reference.py <niche> <url> --notes-only
    python shared/tools/fetch-reference.py <niche> --search queries.txt --top 5
"""
import argparse, json, pathlib, re, subprocess, sys, datetime, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
NICHES = ("ai-short-films", "kids-films")

AR = {"ا":"a","أ":"a","إ":"i","آ":"a","ب":"b","ت":"t","ث":"th","ج":"j","ح":"h",
      "خ":"kh","د":"d","ذ":"dh","ر":"r","ز":"z","س":"s","ش":"sh","ص":"s","ض":"d",
      "ط":"t","ظ":"z","ع":"a","غ":"gh","ف":"f","ق":"q","ك":"k","ل":"l","م":"m",
      "ن":"n","ه":"h","و":"w","ي":"y","ى":"a","ة":"a","ء":"","ئ":"","ؤ":"",
      " ":"-"}


def slugify(text):
    out = "".join(AR.get(c, c) for c in (text or "").lower())
    out = re.sub(r"[^a-z0-9-]+", "-", out).strip("-")
    out = re.sub(r"-{2,}", "-", out)
    return (out[:60].strip("-") or "reference")


# YouTube refuses the default web client for many videos ("This video is not
# available"); the android client is the one that answers reliably here.
CLIENT = ["--extractor-args", "youtube:player_client=android"]


def ytdlp(args):
    return subprocess.run([sys.executable, "-m", "yt_dlp"] + CLIENT + args,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def probe(url):
    r = ytdlp(["--no-warnings", "--dump-single-json", url])
    if r.returncode != 0:
        raise SystemExit("yt-dlp failed:\n" + (r.stderr or "").strip()[-800:])
    return json.loads(r.stdout)


def hms(sec):
    sec = int(sec or 0)
    return "%d:%02d" % (sec // 60, sec % 60)


NOTE = """# دراسة فيديو مرجعي — {title}

- **الرابط:** {url}
- **النيش:** {niche}
- **المنصة:** {platform}
- **القناة:** {uploader}
- **المدة:** {duration}
- **المشاهدات (قراءة {today}):** {views}
- **الإعجابات:** {likes}
- **تاريخ النشر:** {upload_date}
- **الملف المحلي:** `research/raw-videos/{niche}/media/{filename}` (غير مُلتزم في Git)
- **تاريخ الدراسة:** —

## الخط الزمني بالثواني
| الثانية | ما يحدث على الشاشة | الصوت | لماذا يُبقي المشاهد |
|---|---|---|---|
| 0:00 |  |  |  |

## الـ Hook
- نوعه: سؤال | صدمة بصرية | وعد | تحوّل | توتر
- متى يكتمل: —
- هل يُفهم بلا صوت؟ —

## البناء
- عدد اللقطات: —
- متوسط طول اللقطة: —
- نقطة التحوّل: —
- النهاية: حلقة مغلقة | حلقة مفتوحة | انعكاس | سؤال

## ما نستلهمه (هيكل/إيقاع فقط)
-

## ما لا نلمسه (قصة/شخصيات/مشاهد)
-

## النمط المستخرج
`#` — أُضيف إلى `patterns.md`؟ لا
"""


def handle(niche, url, slug=None, notes_only=False):
    media = ROOT / "research" / "raw-videos" / niche / "media"
    notes = ROOT / "research" / "raw-videos" / niche / "notes"
    media.mkdir(parents=True, exist_ok=True)
    notes.mkdir(parents=True, exist_ok=True)

    info = probe(url)
    name = slug or slugify(info.get("title"))
    filename = name + ".mp4"

    if not notes_only:
        r = ytdlp(["--no-warnings", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
                   "--merge-output-format", "mp4", "-o", str(media / filename), url])
        if r.returncode != 0:
            print("  download failed: " + (r.stderr or "").strip()[-400:])

    d = info.get("upload_date") or ""
    out = notes / (name + ".md")
    out.write_text(NOTE.format(
        title=info.get("title") or "—", url=url, niche=niche,
        platform=info.get("extractor_key") or "—",
        uploader=info.get("uploader") or "—",
        duration=hms(info.get("duration")),
        views="{:,}".format(info["view_count"]) if info.get("view_count") else "—",
        likes="{:,}".format(info["like_count"]) if info.get("like_count") else "—",
        upload_date="%s-%s-%s" % (d[:4], d[4:6], d[6:]) if len(d) == 8 else "—",
        today=datetime.date.today().isoformat(), filename=filename,
    ), encoding="utf-8")
    print("  notes: %s" % out.relative_to(ROOT))


# YouTube's own "short (< 4 minutes)" search filter. Plain ytsearch: returns
# long-form films and ignores "#shorts" in the query, so text queries go
# through the results page with this filter instead; our own --max-duration
# then narrows it to real short-form.
SHORT_FILTER = "EgIYAQ%253D%253D"


def _flat(target, pool):
    """Flat-list a search query or a channel/playlist URL -> [(id, views, dur)]."""
    if target.startswith("http"):
        spec = target
    else:
        spec = ("https://www.youtube.com/results?search_query=%s&sp=%s"
                % (urllib.parse.quote_plus(target), SHORT_FILTER))
    args = ["--no-warnings", "--flat-playlist", "--dump-json",
            "--playlist-end", str(pool)]
    r = ytdlp(args + [spec])
    if r.returncode != 0:
        print("  listing failed for %r: %s" % (target, (r.stderr or "").strip()[-200:]))
        return []
    out = []
    for line in r.stdout.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("id"):
            out.append((e["id"], e.get("view_count") or 0, e.get("duration")))
    return out


def search_top(targets, pool, top, max_dur, per_channel=2):
    """Pick the strongest vertical short-form references.

    No public per-niche "most viral" ranking exists, so we rank by YouTube's own
    view_count. A plain line is a search query; a URL line is a channel or
    playlist (a channel's /shorts tab is the reliable way to get real
    short-form, since YouTube search ignores "#shorts" and returns long videos).
    Flat listings sometimes omit view_count, so anything unranked is probed.
    """
    pool_rows, seen = [], set()
    for t in targets:
        for vid, views, dur in _flat(t, pool):
            if vid in seen or (dur and dur > max_dur):
                continue
            seen.add(vid)
            pool_rows.append((views, vid))

    # probe the most promising first; a flat row with no view_count sorts last
    pool_rows.sort(reverse=True)
    vert, land, checked = [], [], 0
    for _, vid in pool_rows:
        if len(vert) >= top and checked >= top * 3:
            break
        checked += 1
        try:
            info = probe("https://www.youtube.com/watch?v=" + vid)
        except SystemExit:
            continue
        dur = info.get("duration") or 0
        views = info.get("view_count") or 0
        if not dur or dur > max_dur or not views:
            continue
        w, h = info.get("width") or 0, info.get("height") or 0
        row = (views, "https://www.youtube.com/watch?v=" + vid,
               info.get("title") or "", dur, "%dx%d" % (w, h),
               info.get("channel") or "—")
        (vert if h > w else land).append(row)

    vert.sort(reverse=True)
    land.sort(reverse=True)

    def spread(rows, limit, per_channel):
        """One channel's back-catalogue is not five references: cap it."""
        out, count = [], {}
        for r in rows:
            ch = r[5]
            if count.get(ch, 0) >= per_channel:
                continue
            count[ch] = count.get(ch, 0) + 1
            out.append(r)
            if len(out) >= limit:
                break
        return out

    picked = spread(vert, top, per_channel)
    picked += spread(land, top - len(picked), per_channel)
    for views, url, title, dur, res, ch in picked:
        print("  %13s  %5s  %-9s  %-22s %s"
              % ("{:,}".format(views), hms(dur), res, ch[:22], title[:45]))
    if len(vert) < top:
        print("  note: only %d vertical candidates; filled with landscape" % len(vert))
    return [u for _, u, _, _, _, _ in picked]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("niche", choices=NICHES)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--list", help="text file, one URL per line (# comments ok)")
    ap.add_argument("--search", help="text file, one search query per line")
    ap.add_argument("--top", type=int, default=5, help="how many to keep (--search)")
    ap.add_argument("--pool", type=int, default=25,
                    help="candidates fetched per query before ranking by views")
    ap.add_argument("--per-channel", type=int, default=2,
                    help="max references kept from one channel")
    ap.add_argument("--max-duration", type=int, default=60,
                    help="our format is vertical short-form: skip anything longer")
    ap.add_argument("--slug")
    ap.add_argument("--notes-only", action="store_true",
                    help="fetch metadata and write notes without downloading")
    a = ap.parse_args()

    urls = []
    if a.list:
        for line in pathlib.Path(a.list).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    if a.search:
        qs = [l.strip()
              for l in pathlib.Path(a.search).read_text(encoding="utf-8").splitlines()]
        # a query may itself be "#shorts ..."; only other #-lines are comments
        qs = [q for q in qs
              if q and (q.startswith("#shorts") or not q.startswith("#"))]
        urls += search_top(qs, a.pool, a.top, a.max_duration, a.per_channel)
    if a.url:
        urls.append(a.url)
    if not urls:
        ap.error("give a URL or --list")

    for u in urls:
        print(u)
        try:
            handle(a.niche, u, a.slug if len(urls) == 1 else None, a.notes_only)
        except SystemExit as e:
            print("  skipped: %s" % e)


if __name__ == "__main__":
    main()
