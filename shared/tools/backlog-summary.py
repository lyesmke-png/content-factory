#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarise a niche idea backlog, sorted by priority (highest first).

Usage: python shared/tools/backlog-summary.py <niche> [--top N] [--status new]
"""
import argparse
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLS = ["id", "idea", "angle", "pattern", "source", "trend", "difficulty", "priority", "status"]


def parse_rows(path):
    rows = []
    for line in io.open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or set("".join(cells)) <= set("-: "):
            continue
        if cells[0].lower() in ("id", "ID".lower()):
            continue
        while len(cells) < len(COLS):
            cells.append("")
        rows.append(dict(zip(COLS, cells[: len(COLS)])))
    return rows


def as_num(value):
    try:
        return float(str(value).split("/")[0].strip())
    except (TypeError, ValueError):
        return -1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("niche")
    ap.add_argument("--top", type=int, default=0)
    ap.add_argument("--status")
    args = ap.parse_args()

    path = os.path.join(ROOT, "niches", args.niche, "ideas", "backlog.md")
    if not os.path.isfile(path):
        sys.exit("backlog not found: %s" % path)

    rows = parse_rows(path)
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    if not rows:
        print("no ideas matched.")
        return
    rows.sort(key=lambda r: (as_num(r["priority"]), as_num(r["trend"])), reverse=True)
    if args.top:
        rows = rows[: args.top]

    print("%-6s %-5s %-5s %-5s %-11s %s" % ("ID", "prio", "trend", "diff", "status", "idea"))
    print("-" * 78)
    for r in rows:
        print("%-6s %-5s %-5s %-5s %-11s %s" % (
            r["id"], r["priority"] or "-", r["trend"] or "-",
            r["difficulty"] or "-", r["status"] or "-", r["idea"]))
    print("\n%d idea(s)." % len(rows))


if __name__ == "__main__":
    main()
