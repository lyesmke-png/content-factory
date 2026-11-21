#!/usr/bin/env python3
"""Render every shot of a scene against one running ComfyUI server.

Why one server and not one process per shot: the models cost about 150 s to
load, and with the cache on they are loaded once for the whole list. Measured
at 512x512 x 20 steps - 236 s for the first shot, then 85 s for each one
after. Restarting between shots would pay that 150 s eight times over.

Start the server with shared/tools/start-comfyui.sh first; without its flags
the run is killed by the OS memory guard before it generates anything.

    python shared/tools/render-shots.py \
        niches/kids-films/scripts/2026-11-21-grandmas-cup-s1.shots \
        --prefix kd001

The .shots file is one shot per line, "<prompt>TAB<colours to suppress>".
Blank lines and lines starting with # are skipped. The style block and the
base negative live in wan_still, so a .shots file carries only what differs
between shots.
"""
import argparse
import importlib.util
import json
import pathlib
import time
import urllib.request

# wan-still.py has a hyphen in its name (the repo convention is kebab-case
# filenames), so it cannot be imported by name and is loaded by path.
_spec = importlib.util.spec_from_file_location(
    "wan_still", pathlib.Path(__file__).resolve().with_name("wan-still.py"))
wan_still = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wan_still)


def read_shots(path):
    shots = []
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        prompt, _, avoid = line.partition("\t")
        shots.append((prompt.strip(), avoid.strip()))
    return shots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots_file")
    ap.add_argument("--prefix", required=True, help="output name stem, e.g. kd001")
    ap.add_argument("--size", type=int, default=768,
                    help="768 is the floor: 640 loses the style entirely and "
                         "512 loses the character's legs")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--cfg", type=float, default=7.0)
    ap.add_argument("--seed", type=int, default=20261121)
    ap.add_argument("--only", type=int, default=0,
                    help="render just this shot number, to redo one of them")
    a = ap.parse_args()

    shots = read_shots(a.shots_file)
    print("%d shots from %s" % (len(shots), a.shots_file))
    t0 = time.time()
    for n, (prompt, avoid) in enumerate(shots, 1):
        if a.only and n != a.only:
            continue
        neg = (avoid + ", " + wan_still.NEG) if avoid else wan_still.NEG
        wf = wan_still.build(wan_still.STYLE + ", " + prompt, neg,
                             a.size, a.size, a.steps, a.cfg,
                             a.seed + n, "%s-shot%d" % (a.prefix, n))
        t = time.time()
        pid = wan_still.post("/prompt", {"prompt": wf})["prompt_id"]
        while True:
            time.sleep(5)
            h = json.loads(urllib.request.urlopen(
                wan_still.HOST + "/history/" + pid, timeout=30).read())
            if pid in h:
                break
        names = [i["filename"] for o in h[pid]["outputs"].values()
                 for i in o.get("images", [])]
        print("shot %d/%d  %6.1f s  %s" % (n, len(shots), time.time() - t,
                                           ", ".join(names) or "NO OUTPUT"),
              flush=True)
    print("TOTAL %.1f min" % ((time.time() - t0) / 60))


if __name__ == "__main__":
    main()
