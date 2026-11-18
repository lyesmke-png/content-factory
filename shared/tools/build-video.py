#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a vertical 9:16 short video from still images, for free.

Each still gets a slow Ken Burns move (zoom + drift), the shots are concatenated,
and narration/music are mixed in. No paid generation service is involved.

Requires ffmpeg. Easiest free install (no admin rights):
    python -m pip install imageio-ffmpeg

Usage:
    python shared/tools/build-video.py --shots ./shots --out ./out.mp4 \
        --audio ./narration.mp3 --music ./music.mp3 --seconds-per-shot 5

Images are taken in sorted filename order, so name them 01-*.png, 02-*.png, ...
Arabic on-screen text is NOT burned in here (ffmpeg does not shape Arabic
correctly without extra libraries) — add it afterwards in CapCut Desktop (free).
See FREE_PIPELINE.md.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found. Install it with:  python -m pip install imageio-ffmpeg")


def kenburns_filter(index, frames):
    """Alternate the direction so consecutive shots do not feel identical."""
    moves = [
        "z='zoom+0.0012'",                       # slow push in
        "z='if(lte(zoom,1.0),1.25,max(1.001,zoom-0.0012))'",  # slow pull out
    ]
    pans = [
        ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),                 # centred
        ("iw/2-(iw/zoom/2)+(on/%d)*60" % frames, "ih/2-(ih/zoom/2)"),  # drift right
        ("iw/2-(iw/zoom/2)-(on/%d)*60" % frames, "ih/2-(ih/zoom/2)"),  # drift left
        ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+(on/%d)*60" % frames),  # drift down
    ]
    z = moves[index % len(moves)]
    x, y = pans[index % len(pans)]
    return (
        "scale=%d:-1:flags=lanczos,"
        "crop=%d:%d:(iw-%d)/2:(ih-%d)/2,"
        "zoompan=%s:x='%s':y='%s':d=%d:s=%dx%d:fps=%d,"
        "format=yuv420p" % (W * 2, W * 2, H * 2, W * 2, H * 2, z, x, y, frames, W, H, FPS)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", required=True, help="directory of still images")
    ap.add_argument("--out", required=True, help="output .mp4")
    ap.add_argument("--audio", help="narration audio (e.g. from edge-tts)")
    ap.add_argument("--music", help="background music (free-licensed only)")
    ap.add_argument("--seconds-per-shot", type=float, default=5.0)
    ap.add_argument("--music-db", type=float, default=-14.0,
                    help="music gain in dB; keep speech clearly above it")
    args = ap.parse_args()

    ffmpeg = find_ffmpeg()

    images = sorted(p for p in glob.glob(os.path.join(args.shots, "*"))
                    if p.lower().endswith(EXTS))
    if not images:
        sys.exit("no images found in %s" % args.shots)

    frames = max(1, int(round(args.seconds_per_shot * FPS)))
    tmp = tempfile.mkdtemp(prefix="shortbuild-")
    clips = []
    try:
        for i, img in enumerate(images):
            clip = os.path.join(tmp, "clip%03d.mp4" % i)
            cmd = [ffmpeg, "-y", "-loglevel", "error", "-loop", "1", "-i", img,
                   "-vf", kenburns_filter(i, frames),
                   "-t", "%.3f" % args.seconds_per_shot,
                   "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
                   "-crf", "18", "-pix_fmt", "yuv420p", clip]
            subprocess.run(cmd, check=True)
            clips.append(clip)
            print("shot %d/%d: %s" % (i + 1, len(images), os.path.basename(img)))

        listfile = os.path.join(tmp, "list.txt")
        with open(listfile, "w", encoding="utf-8") as fh:
            for c in clips:
                fh.write("file '%s'\n" % c.replace("\\", "/").replace("'", "'\''"))

        silent = os.path.join(tmp, "silent.mp4")
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat",
                        "-safe", "0", "-i", listfile, "-c", "copy", silent], check=True)

        tracks = [p for p in (args.audio, args.music) if p]
        if not tracks:
            shutil.move(silent, args.out)
        else:
            cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", silent]
            for t in tracks:
                cmd += ["-i", t]
            # Every branch pads the audio so a short narration can never cut
            # the picture off: -shortest then ends the file at the last shot.
            if args.audio and args.music:
                flt = ("[1:a]apad[n];[2:a]volume=%.1fdB,apad[m];"
                       "[n][m]amix=inputs=2:duration=longest:dropout_transition=0,"
                       "apad[a]" % args.music_db)
                cmd += ["-filter_complex", flt, "-map", "0:v", "-map", "[a]"]
            elif args.music:
                cmd += ["-filter_complex",
                        "[1:a]volume=%.1fdB,apad[a]" % args.music_db,
                        "-map", "0:v", "-map", "[a]"]
            else:
                cmd += ["-filter_complex", "[1:a]apad[a]",
                        "-map", "0:v", "-map", "[a]"]
            cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", args.out]
            subprocess.run(cmd, check=True)

        total = len(images) * args.seconds_per_shot
        print("\nwrote %s — %d shots, %.1fs, %dx%d @%dfps"
              % (args.out, len(images), total, W, H, FPS))
        if total >= 60:
            print("WARNING: %.1fs is 60s or longer — trim a shot for TikTok/Shorts."
                  % total)
        print("Next: add Arabic on-screen text and subtitles in CapCut Desktop (free).")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
