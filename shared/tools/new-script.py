#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a new script file for a niche from the shared template.

Usage: python shared/tools/new-script.py <niche> "<title>" [--slug my-slug] [--date YYYY-MM-DD]
"""
import argparse
import datetime
import io
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE = os.path.join(ROOT, "shared", "templates", "script-template.md")

AR_MAP = {
    "ا": "a", "أ": "a", "إ": "a", "آ": "a", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "a",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "w", "ي": "y", "ى": "a", "ئ": "y", "ء": "", "ؤ": "w",
    "ة": "a", "َ": "", "ُ": "", "ِ": "", "ّ": "", "ْ": "", "ً": "", "ٌ": "", "ٍ": "",
}


def slugify(title):
    out = []
    for ch in title:
        if ch in AR_MAP:
            out.append(AR_MAP[ch])
        elif ch.isascii() and (ch.isalnum()):
            out.append(ch.lower())
        elif ch.isspace() or ch in "-_":
            out.append("-")
        elif unicodedata.category(ch).startswith("L"):
            out.append("")
        else:
            out.append("-")
    slug = re.sub(r"-{2,}", "-", "".join(out)).strip("-")
    return slug or "untitled"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("niche")
    ap.add_argument("title")
    ap.add_argument("--slug")
    ap.add_argument("--date")
    args = ap.parse_args()

    niche_dir = os.path.join(ROOT, "niches", args.niche)
    if not os.path.isdir(niche_dir):
        sys.exit("niche not found: niches/%s" % args.niche)

    date = args.date or datetime.date.today().isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        sys.exit("bad --date, expected YYYY-MM-DD")
    slug = args.slug or slugify(args.title)

    scripts_dir = os.path.join(niche_dir, "scripts")
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)
    target = os.path.join(scripts_dir, "%s-%s.md" % (date, slug))
    if os.path.exists(target):
        sys.exit("already exists: %s" % target)

    body = io.open(TEMPLATE, encoding="utf-8").read()
    body = body.replace("# <العنوان>", "# %s" % args.title, 1)
    body = body.replace("`<niche>`", "`%s`" % args.niche)
    body = body.replace("<niche>", args.niche)
    body = body.replace("YYYY-MM-DD", date)
    body = body.replace("`<slug>`", "`%s`" % slug)
    body = body.replace("<slug>", slug)

    io.open(target, "w", encoding="utf-8", newline="\n").write(body)
    print(os.path.relpath(target, ROOT).replace(os.sep, "/"))


if __name__ == "__main__":
    main()
