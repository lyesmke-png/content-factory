#!/usr/bin/env python3
"""Assemble one finished scene from stills, dialogue and a timing sheet.

The stills do not move, so the camera does. That is not a workaround for weak
hardware - it is the measured pattern `#camera-move-instead-of-cut`, taken
from a reference that held 120k views with ONE cut in 36 seconds. A slow push
on a still reads as a shot; a hard cut every two seconds reads as a slideshow.

The published frame is 1080x1920 with the picture filling the middle square,
measured off the strongest reference we have with cropdetect. The band above
carries the series title and the scene number, so a viewer arriving at scene 5
knows what this is and that there is more. The band below carries the spoken
line in vocalised Arabic - all five children's references we measured are
unreadable with the sound off, which is the gap this fills.

    python shared/tools/build-scene.py \
        niches/kids-films/scripts/2026-11-21-grandmas-cup-s1.scene \
        --stills produced/stills/kd001 --audio produced/audio/kd001 \
        --out produced/kd001.mp4

A .scene file is one row per shot:
    start TAB end TAB shot TAB move TAB caption TAB audio-file
`move` is one of in, out, left, right, up, down, still.
An empty caption or audio field is a dash.
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import tempfile

W, H = 1080, 1920
PIC = 1080           # the picture is square and fills the middle of the frame
PIC_Y = 420
FPS = 25
OVERSCAN = 2         # render the move from a 2x image so the pan has room
FONT_DIR = pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"


def find_ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def font(*names):
    for n in names:
        p = FONT_DIR / n
        if p.exists():
            return str(p).replace("\\", "/").replace(":", "\\:")
    raise SystemExit("no Arabic font found in %s" % FONT_DIR)


def esc(text):
    return (text.replace("\\", "\\\\").replace(":", "\\:")
                .replace("'", "\\'").replace("%", "\\%"))


# Each move is a zoom expression plus a centre, in zoompan's variables. `on`
# is the output frame index, so every expression is written against the shot's
# own length and the speed does not change with the shot's duration.
def move_filter(move, frames):
    z_in = "1+0.18*on/%d" % frames
    z_out = "1.18-0.18*on/%d" % frames
    centre_x = "iw/2-(iw/zoom/2)"
    centre_y = "ih/2-(ih/zoom/2)"
    edge = "(iw-iw/zoom)"
    moves = {
        "in":    (z_in, centre_x, centre_y),
        "out":   (z_out, centre_x, centre_y),
        "left":  ("1.18", "%s*(1-on/%d)" % (edge, frames), centre_y),
        "right": ("1.18", "%s*on/%d" % (edge, frames), centre_y),
        "up":    ("1.18", centre_x, "(ih-ih/zoom)*(1-on/%d)" % frames),
        "down":  ("1.18", centre_x, "(ih-ih/zoom)*on/%d" % frames),
        "still": ("1.0", centre_x, centre_y),
    }
    if move not in moves:
        raise SystemExit("unknown move %r" % move)
    z, x, y = moves[move]
    return ("scale=%d:%d,zoompan=z='%s':x='%s':y='%s':d=1:s=%dx%d:fps=%d"
            % (PIC * OVERSCAN, PIC * OVERSCAN, z, x, y, PIC, PIC, FPS))


def read_scene(path):
    rows = []
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < 6:
            raise SystemExit("row needs 6 tab-separated fields: %r" % line)
        rows.append(dict(start=float(f[0]), end=float(f[1]), shot=f[2].strip(),
                         move=f[3].strip(), caption=f[4].strip(),
                         audio=f[5].strip()))
    return rows


def build_shot(ff, src, row, title, scene_label, bold, reg, grade, bg, out):
    dur = row["end"] - row["start"]
    frames = max(int(dur * FPS), 1)
    chain = [
        "[0:v]%s,%s[pic]" % (move_filter(row["move"], frames), grade),
        "color=c=%s:s=%dx%d:d=%.3f:r=%d[bg]" % (bg, W, H, dur, FPS),
        "[bg][pic]overlay=0:%d[v0]" % PIC_Y,
        "[v0]drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=62:"
        "x=(w-text_w)/2:y=190[v1]" % (bold, esc(title)),
        "[v1]drawtext=fontfile='%s':text='%s':fontcolor=0xE8C87A:fontsize=46:"
        "x=(w-text_w)/2:y=280[v2]" % (reg, esc(scene_label)),
    ]
    last = "v2"
    if row["caption"] and row["caption"] != "-":
        chain.append(
            "[%s]drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=58:"
            "box=1:boxcolor=0x000000AA:boxborderw=28:x=(w-text_w)/2:y=%d[v3]"
            % (last, reg, esc(row["caption"]), PIC_Y + PIC + 90))
        last = "v3"
    cmd = [ff, "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS),
           "-t", "%.3f" % dur, "-i", src,
           "-filter_complex", ";".join(chain), "-map", "[%s]" % last,
           "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene_file")
    ap.add_argument("--stills", required=True, help="directory of shot images")
    ap.add_argument("--audio", default="", help="directory of dialogue files")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--scene-label", default="")
    ap.add_argument("--grade", default="warm", choices=["warm", "cool", "none"],
                    help="one grade per series: it unifies the look and hides "
                         "the cuts, and it is free because ffmpeg does it")
    ap.add_argument("--bg", default="0x141018")
    a = ap.parse_args()

    ff = find_ffmpeg()
    bold, reg = font("tahomabd.ttf", "tahoma.ttf"), font("tahoma.ttf", "tahomabd.ttf")
    grade = {
        "warm": "eq=saturation=1.08:contrast=1.06,"
                "colorbalance=rs=0.05:gs=0.01:bs=-0.05",
        "cool": "eq=saturation=1.02:contrast=1.08,"
                "colorbalance=rs=-0.04:gs=0.00:bs=0.06",
        "none": "null",
    }[a.grade]

    rows = read_scene(a.scene_file)
    stills = pathlib.Path(a.stills)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="scene-"))
    segs = []
    for i, row in enumerate(rows, 1):
        found = sorted(stills.glob(row["shot"] + ".*"))
        if not found:
            raise SystemExit("no still matching %r in %s" % (row["shot"], stills))
        seg = tmp / ("seg%02d.mp4" % i)
        build_shot(ff, str(found[0]), row, a.title, a.scene_label,
                   bold, reg, grade, a.bg, str(seg))
        segs.append(seg)
        print("shot %d/%d  %.1fs  %-5s  %s"
              % (i, len(rows), row["end"] - row["start"], row["move"],
                 found[0].name), flush=True)

    lst = tmp / "list.txt"
    lst.write_text("".join("file '%s'\n" % s.as_posix() for s in segs),
                   encoding="utf-8")
    silent = tmp / "silent.mp4"
    subprocess.run([ff, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(silent)], check=True)

    # Dialogue is placed at the absolute time its row starts, so the sound
    # cannot drift out of step with the picture however the shots are retimed.
    clips = [(r, pathlib.Path(a.audio) / r["audio"]) for r in rows
             if a.audio and r["audio"] and r["audio"] != "-"]
    missing = [str(p) for _, p in clips if not p.exists()]
    if missing:
        raise SystemExit("missing audio: " + ", ".join(missing))
    if not clips:
        shutil.copy(str(silent), a.out)
    else:
        cmd = [ff, "-y", "-v", "error", "-i", str(silent)]
        for _, p in clips:
            cmd += ["-i", str(p)]
        parts = ["[%d:a]adelay=%d|%d[a%d]"
                 % (n, int(r["start"] * 1000), int(r["start"] * 1000), n)
                 for n, (r, _) in enumerate(clips, 1)]
        mix = "".join("[a%d]" % n for n in range(1, len(clips) + 1))
        parts.append("%samix=inputs=%d:dropout_transition=0:normalize=0[aout]"
                     % (mix, len(clips)))
        # No -shortest here. The mix ends with the last line of dialogue, and
        # -shortest would trim the picture to match it, eating the tail of the
        # final shot - measured, it cost 0.95 s of shot 8. The timing sheet is
        # what decides how long the scene runs, so the video stream is.
        cmd += ["-filter_complex", ";".join(parts),
                "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", a.out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stderr[-1500:])

    shutil.rmtree(tmp, ignore_errors=True)
    total = rows[-1]["end"] if rows else 0
    print("%s  %dx%d  %.1fs  %d shots" % (a.out, W, H, total, len(rows)))


if __name__ == "__main__":
    main()
