#!/usr/bin/env python3
"""Speak a scene's dialogue with edge-tts, one file per line.

edge-tts has no child voices in Arabic, so the two children are adult neural
voices with the pitch raised. That is a workaround, and whether it sounds like
a five-year-old or like a sped-up adult is a judgement only a listener can
make - so --candidates renders the same line in several voices for the owner
to choose between, instead of this file choosing for him.

The text is fully vocalised, which is a project rule and not a preference:
Arabic without diacritics is ambiguous, and a wrong vowel changes the word.
The marks are kept in the text handed to the engine.

    python shared/tools/make-voices.py \
        niches/kids-films/scripts/2026-11-21-grandmas-cup-s1.lines \
        --out-dir produced/audio/kd001

    python shared/tools/make-voices.py <lines> --candidates   # voice audition

A .lines file is one line per utterance, "<speaker>TAB<vocalised text>".
Speaker names map to voices in VOICES below.
"""
import argparse
import asyncio
import pathlib

import edge_tts

# ar-SA reads Modern Standard Arabic cleanly, which is what these scripts are
# written in; the dialect voices colour it. Pitch and rate are what turn an
# adult voice into a child one, and they are per character so the two are
# told apart by ear in the first second - the scripts have no narrator to say
# who is speaking.
VOICES = {
    "noor":   dict(voice="ar-SA-ZariyahNeural", pitch="+35Hz", rate="-5%"),
    "samsam": dict(voice="ar-EG-SalmaNeural",   pitch="+55Hz", rate="-10%"),
}

# Offered when the owner has not picked yet. Both children are small, so every
# candidate is pitched up; what differs is the voice underneath.
CANDIDATES = [
    ("ar-SA-ZariyahNeural", "+35Hz"),
    ("ar-SA-ZariyahNeural", "+55Hz"),
    ("ar-EG-SalmaNeural", "+55Hz"),
    ("ar-SA-HamedNeural", "+45Hz"),
    ("ar-EG-ShakirNeural", "+45Hz"),
    ("ar-JO-SanaNeural", "+45Hz"),
]


def read_lines(path):
    out = []
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        who, _, text = line.partition("\t")
        out.append((who.strip().lower(), text.strip()))
    return out


async def say(text, out, voice, pitch, rate):
    c = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
    await c.save(str(out))


async def run(lines, out_dir, candidates):
    out_dir.mkdir(parents=True, exist_ok=True)
    if candidates:
        text = lines[0][1]
        for i, (voice, pitch) in enumerate(CANDIDATES, 1):
            f = out_dir / ("candidate-%d-%s-%s.mp3" % (i, voice, pitch))
            await say(text, f, voice, pitch, "-5%")
            print("%d. %s %s  ->  %s" % (i, voice, pitch, f.name))
        print("\nSame line in every voice. Pick one per character and set "
              "VOICES in this file.")
        return
    for n, (who, text) in enumerate(lines, 1):
        if who not in VOICES:
            raise SystemExit("unknown speaker %r - add it to VOICES" % who)
        v = VOICES[who]
        f = out_dir / ("%02d-%s.mp3" % (n, who))
        await say(text, f, **v)
        print("%2d  %-7s %s" % (n, who, f.name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines_file")
    ap.add_argument("--out-dir", default="produced/audio")
    ap.add_argument("--candidates", action="store_true",
                    help="render line 1 in every candidate voice, to choose by ear")
    a = ap.parse_args()
    lines = read_lines(a.lines_file)
    asyncio.run(run(lines, pathlib.Path(a.out_dir), a.candidates))


if __name__ == "__main__":
    main()
