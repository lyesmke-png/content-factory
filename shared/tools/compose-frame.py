#!/usr/bin/env python3
"""Put a generated clip into the published 1080x1920 frame.

The format comes from measuring the strongest reference we have (8.4M views):
its picture fills only half the height of a vertical frame, and the black band
above carries the series title and the part number. Measured with cropdetect:
crop=360:322:0:130 inside 360x640.

That measurement is the reason this pipeline fits a 4GB card at all: a picture
band of 1080x966 can be generated at 640x576 and upscaled, instead of
generating a full 1080x1920 frame.

The frame does three jobs at once:
  * the top band states the series and the scene number, so a viewer who
    arrives at scene 5 knows what this is and that there is more;
  * the bottom band carries the vocalised Arabic line, which every one of the
    five kids references was missing - they are unreadable with the sound off;
  * the smaller picture is what makes the whole thing renderable on this GPU.

Arabic is shaped by ffmpeg itself (built with libharfbuzz and libfribidi), so
no reshaper library is needed.

Usage:
    python shared/tools/compose-frame.py in.mp4 out.mp4 \
        --title "كُوبُ الجَدَّة" --scene "المشهد ١" \
        --caption "سَمْسَمْ، مَاذَا فَعَلْتَ؟"
"""
import argparse
import os
import pathlib
import shutil
import subprocess

W, H = 1080, 1920
PIC_H = 966          # the picture band, from the measured reference
PIC_Y = 390
FONT_DIR = pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def font(*names):
    for n in names:
        p = FONT_DIR / n
        if p.exists():
            return str(p).replace("\\", "/").replace(":", "\\:")
    raise SystemExit("no Arabic font found in %s" % FONT_DIR)


def esc(text):
    """drawtext eats these characters; hand them over escaped."""
    return (text.replace("\\", "\\\\").replace(":", "\\:")
                .replace("'", "\\'").replace("%", "\\%"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--title", default="")
    ap.add_argument("--scene", default="")
    ap.add_argument("--caption", default="")
    ap.add_argument("--grade", default="warm",
                    choices=["warm", "cool", "none"],
                    help="one grade per series: it unifies the look and hides "
                         "the cuts, the way the top reference does")
    ap.add_argument("--bg", default="0x141018")
    a = ap.parse_args()

    ff = find_ffmpeg()
    # Tahoma first, and it is not a style preference: rendered side by side,
    # Dubai and Arabic Typesetting drop vocalised glyphs (بُ ة ذ came out as
    # empty boxes) and Traditional Arabic silently loses diacritics. Since
    # every spoken line we write is vocalised, a font that cannot draw the
    # marks would quietly corrupt the meaning on screen.
    bold = font("tahomabd.ttf", "tahoma.ttf")
    reg = font("tahoma.ttf", "tahomabd.ttf")

    grade = {
        "warm": "eq=saturation=1.08:contrast=1.06,"
                "colorbalance=rs=0.05:gs=0.01:bs=-0.05",
        "cool": "eq=saturation=1.02:contrast=1.08,"
                "colorbalance=rs=-0.04:gs=0.00:bs=0.06",
        "none": "null",
    }[a.grade]

    chain = [
        "[0:v]scale=%d:%d:force_original_aspect_ratio=increase,"
        "crop=%d:%d,%s[pic]" % (W, PIC_H, W, PIC_H, grade),
        # no duration on the colour source: it runs for ever and `shortest`
        # below ends the output with the picture, not after one second
        "color=c=%s:s=%dx%d[bg]" % (a.bg, W, H),
        "[bg][pic]overlay=0:%d:shortest=1[v0]" % PIC_Y,
    ]
    last = "v0"

    if a.title:
        chain.append(
            "[%s]drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=62:"
            "x=(w-text_w)/2:y=190[v1]" % (last, bold, esc(a.title)))
        last = "v1"
    if a.scene:
        chain.append(
            "[%s]drawtext=fontfile='%s':text='%s':fontcolor=0xE8C87A:"
            "fontsize=46:x=(w-text_w)/2:y=280[v2]" % (last, reg, esc(a.scene)))
        last = "v2"
    if a.caption:
        chain.append(
            "[%s]drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=58:"
            "line_spacing=18:box=1:boxcolor=0x000000AA:boxborderw=28:"
            "x=(w-text_w)/2:y=%d[v3]" % (last, reg, esc(a.caption), PIC_Y + PIC_H + 90))
        last = "v3"

    cmd = [ff, "-y", "-v", "error", "-i", a.src,
           "-filter_complex", ";".join(chain), "-map", "[%s]" % last]
    probe = subprocess.run([ff, "-hide_banner", "-i", a.src],
                           capture_output=True, text=True).stderr
    if "Audio:" in probe:
        cmd += ["-map", "0:a", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", a.out]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1200:])
    print("%s  %dx%d  picture band %dx%d at y=%d" % (a.out, W, H, W, PIC_H, PIC_Y))


if __name__ == "__main__":
    main()
