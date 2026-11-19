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
import argparse, json, pathlib, re, subprocess, sys, datetime

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


def ytdlp(args):
    return subprocess.run([sys.executable, "-m", "yt_dlp"] + args,
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


def search_top(queries, pool, top):
    """Resolve search queries to the highest-view-count videos.

    There is no public per-niche "most viral" ranking, so we rank candidates by
    YouTube's own view_count over a wider pool and keep the strongest few.
    """
    seen, rows = set(), []
    for q in queries:
        r = ytdlp(["--no-warnings", "--flat-playlist", "--dump-json",
                   "ytsearch%d:%s" % (pool, q)])
        if r.returncode != 0:
            print("search failed for %r: %s" % (q, (r.stderr or "").strip()[-200:]))
            continue
        for line in r.stdout.splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            vid, views = e.get("id"), e.get("view_count") or 0
            dur = e.get("duration") or 0
            if not vid or vid in seen or not views or dur > 180:
                continue
            seen.add(vid)
            rows.append((views, "https://www.youtube.com/watch?v=" + vid,
                         e.get("title") or ""))
    rows.sort(reverse=True)
    for views, url, title in rows[:top]:
        print("  %13s  %s" % ("{:,}".format(views), title[:70]))
    return [u for _, u, _ in rows[:top]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("niche", choices=NICHES)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--list", help="text file, one URL per line (# comments ok)")
    ap.add_argument("--search", help="text file, one search query per line")
    ap.add_argument("--top", type=int, default=5, help="how many to keep (--search)")
    ap.add_argument("--pool", type=int, default=20,
                    help="candidates fetched per query before ranking by views")
    ap.add_argument("--slug")
    ap.add_argument("--notes-only", action="store_true",
                    help="fetch metadata and write notes without downloading")
    a = ap.parse_args()

    urls = []
    if a.list:
        for line in pathlib.Path(a.list).read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                urls.append(line)
    if a.search:
        qs = [l.split("#")[0].strip()
              for l in pathlib.Path(a.search).read_text(encoding="utf-8").splitlines()]
        urls += search_top([q for q in qs if q], a.pool, a.top)
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
