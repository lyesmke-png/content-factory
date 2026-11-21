#!/usr/bin/env python3
"""Animate one shot: moving camera, blinking eyes, and mouth driven by the voice.

This is 2D puppet animation ("limited animation"), the technique kids cartoons
have always used: the drawing is cut into layers and only the mouth and eyes are
swapped, frame by frame, in time with the narration.

Why not an AI talking-head model: on this machine (4 GB VRAM) the photo-to-video
models either do not fit or are research/non-commercial licensed, which a
monetised channel cannot use. This runs on the CPU, needs no model download, and
the output is ours.

A shot folder holds transparent PNG layers plus shot.json:

    shot.json   {"size": [1080, 1920],
                 "mouth": {"pos": [520, 900], "level_db": [-40, -26, -16]},
                 "eyes":  {"pos": [500, 820], "blink_every": [2.5, 5.0]},
                 "camera": {"zoom": 1.12, "pan": "up"}}
    bg.png            background, covers the frame
    body.png          character without mouth or eyes
    mouth-0.png       closed   (silence)
    mouth-1.png       narrow   (quiet speech)
    mouth-2.png       open     (loud speech)
    mouth-3.png       wide     (optional, loudest)
    eyes-open.png / eyes-shut.png

Usage:
    python shared/tools/animate-shot.py <shot-dir> <audio> <out.mp4> [--fps 30]
"""
import argparse, json, math, os, pathlib, random, shutil, subprocess, sys, tempfile

from PIL import Image

W_DEFAULT, H_DEFAULT = 1080, 1920


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def audio_levels(ffmpeg, audio, fps):
    """Per-frame loudness in dBFS, measured from the narration itself."""
    import numpy as np
    sr = 16000
    raw = subprocess.run(
        [ffmpeg, "-v", "error", "-i", audio, "-ac", "1", "-ar", str(sr),
         "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
    if a.size == 0:
        raise SystemExit("no audio decoded from %s" % audio)
    step = sr / float(fps)
    n = int(math.ceil(a.size / step))
    out = []
    for i in range(n):
        chunk = a[int(i * step):int((i + 1) * step)]
        rms = float((chunk ** 2).mean() ** 0.5) if chunk.size else 0.0
        out.append(20 * math.log10(rms) if rms > 1e-6 else -120.0)
    return out, a.size / float(sr)


def pick_mouth(db, thresholds, count):
    """Map loudness to a mouth shape, clamped to the shapes that exist."""
    level = 0
    for t in thresholds:
        if db >= t:
            level += 1
    return min(level, count - 1)


def smooth(levels, hold):
    """A mouth that changes every single frame reads as a flicker, not speech."""
    out, last, held = [], levels[0], 0
    for v in levels:
        if v == last or held >= hold:
            last, held = v, 0
        else:
            held += 1
            v = last
        out.append(v)
    return out


def camera_box(w, h, t, dur, zoom, pan):
    """Slow push-in with a drift: the still never sits perfectly still."""
    k = 0.0 if dur <= 0 else min(1.0, t / dur)
    z = 1.0 + (zoom - 1.0) * k
    cw, ch = w / z, h / z
    dx = (w - cw)
    dy = (h - ch)
    if pan == "up":
        x, y = dx / 2, dy * (1.0 - k)
    elif pan == "down":
        x, y = dx / 2, dy * k
    elif pan == "left":
        x, y = dx * (1.0 - k), dy / 2
    elif pan == "right":
        x, y = dx * k, dy / 2
    else:
        x, y = dx / 2, dy / 2
    return (int(x), int(y), int(x + cw), int(y + ch))


def load(dirpath, name):
    p = pathlib.Path(dirpath) / name
    return Image.open(p).convert("RGBA") if p.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot_dir")
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7, help="fixed seed = repeatable blinks")
    ap.add_argument("--mouth", choices=["on", "off"], default="on",
                    help="off for a narrator line: the character on screen is "
                         "not the one speaking, so the lips must stay shut")
    a = ap.parse_args()

    ffmpeg = find_ffmpeg()
    cfg = {}
    cfgp = pathlib.Path(a.shot_dir) / "shot.json"
    if cfgp.exists():
        cfg = json.loads(cfgp.read_text(encoding="utf-8"))
    W, H = cfg.get("size", [W_DEFAULT, H_DEFAULT])

    bg = load(a.shot_dir, "bg.png")
    body = load(a.shot_dir, "body.png")
    if bg is None and body is None:
        raise SystemExit("need at least bg.png or body.png in %s" % a.shot_dir)

    mouths = [load(a.shot_dir, "mouth-%d.png" % i) for i in range(4)]
    mouths = [m for m in mouths if m is not None]
    if a.mouth == "off":
        mouths = mouths[:1]
    eyes_open = load(a.shot_dir, "eyes-open.png")
    eyes_shut = load(a.shot_dir, "eyes-shut.png")

    mcfg = cfg.get("mouth", {})
    mpos = tuple(mcfg.get("pos", [W // 2, int(H * 0.55)]))
    thresholds = mcfg.get("level_db", [-40, -26, -16])
    ecfg = cfg.get("eyes", {})
    epos = tuple(ecfg.get("pos", [W // 2, int(H * 0.45)]))
    blink_lo, blink_hi = ecfg.get("blink_every", [2.5, 5.0])
    cam = cfg.get("camera", {})
    zoom, pan = cam.get("zoom", 1.10), cam.get("pan", "up")

    db, dur = audio_levels(ffmpeg, a.audio, a.fps)
    frames = len(db)
    if mouths:
        seq = smooth([pick_mouth(x, thresholds, len(mouths)) for x in db], 2)
    else:
        seq = [0] * frames

    rnd = random.Random(a.seed)
    blinks = set()
    t = rnd.uniform(blink_lo, blink_hi)
    while t < dur:
        f = int(t * a.fps)
        blinks.update({f, f + 1, f + 2})           # ~100 ms, the real thing
        t += rnd.uniform(blink_lo, blink_hi)

    tmp = tempfile.mkdtemp(prefix="shot_")
    try:
        for i in range(frames):
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            if bg is not None:
                canvas.alpha_composite(bg.resize((W, H)))
            if body is not None:
                canvas.alpha_composite(body)
            eye = eyes_shut if (i in blinks and eyes_shut is not None) else eyes_open
            if eye is not None:
                canvas.alpha_composite(eye, (epos[0], epos[1]))
            if mouths:
                canvas.alpha_composite(mouths[seq[i]], (mpos[0], mpos[1]))
            box = camera_box(W, H, i / float(a.fps), dur, zoom, pan)
            canvas.convert("RGB").resize((W, H), Image.LANCZOS, box=box).save(
                os.path.join(tmp, "f%05d.png" % i))

        cmd = [ffmpeg, "-y", "-v", "error",
               "-framerate", str(a.fps), "-i", os.path.join(tmp, "f%05d.png"),
               "-i", a.audio,
               "-filter_complex", "[1:a]apad[a]", "-map", "0:v", "-map", "[a]",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-shortest", a.out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stderr[-800:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    talking = sum(1 for v in seq if v > 0)
    print("%s  %d frames  %.2fs  mouth open %d%% of frames"
          % (a.out, frames, dur, round(100.0 * talking / max(1, frames))))


if __name__ == "__main__":
    main()
