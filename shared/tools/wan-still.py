#!/usr/bin/env python3
"""Generate one still with Wan 2.1 1.3B through the ComfyUI HTTP API.

Stills, not video. Measured on this machine (GTX 1050 Ti, 4GB, 1.94 TFLOPS
and no tensor cores):

    768x768 x 33 frames  ->  1140 s    (553x real time: unusable)
    768x768 x  1 frame   ->   206 s    (8 shots = 27 min per video)

Run a whole scene list against ONE running server. 206 s is the steady state
with the models resident; the first shot after a restart costs ~150 s more.
Resolution is set by quality, not by speed: 640 and 512 are far cheaper and
both unusable (see the table in STACK_DECISION.md).

The server must be started by shared/tools/start-comfyui.sh - without
--disable-pinned-memory the run is killed by the OS memory guard.

COLOUR: the defaults below are not styling. Each character's colour is its
identity (shared/brand/characters.md), and this model drops a plain colour
word - a red scarf came out yellow in two independent runs. Fixing it took
four measured attempts, because the obvious fix breaks something else: naming
the colour twice corrects the colour but inflates the garment until it eats
the body, since the model weights a thing by how often it is repeated. The
template that holds both, and the one every shot in this project uses:

    a small narrow crimson red scarf tied neatly around its neck, scarlet red,
    full body visible, big dark glossy eyes
    --avoid "yellow, yellow scarf, orange scarf"      (cfg 7.0, the default)

A size qualifier and "full body visible" buy back the proportions that the
repetition costs.

    python shared/tools/wan-still.py \
        --prompt "close up of a small round grey kitten wearing a vivid
                  crimson red scarf, scarlet red fabric, one paw reaching" \
        --avoid "yellow, yellow scarf, orange scarf" \
        --out kd001-shot3
"""
import argparse
import json
import time
import urllib.request

HOST = "http://127.0.0.1:8188"

# The locked look from shared/brand/characters.md. Every shot carries it, so
# the whole series reads as one object even across separate generations.
STYLE = ("3D vinyl toy style, soft matte plastic surface, smooth rounded "
         "simple shapes, big dark glossy eyes, soft studio light, cute "
         "collectible figurine look, childrens animation, no text")
NEG = ("blurry, low quality, distorted, extra limbs, text, watermark, "
       "scary, dark, violent")


def node(ct, inp):
    return {"class_type": ct, "inputs": inp}


def build(pos, neg, w, h, steps, cfg, seed, prefix):
    return {
        "1": node("UNETLoader", {"unet_name": "wan2.1_t2v_1.3B_fp16.safetensors",
                                 "weight_dtype": "default"}),
        "2": node("CLIPLoader", {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                                 "type": "wan", "device": "default"}),
        "3": node("VAELoader", {"vae_name": "wan_2.1_vae.safetensors"}),
        "4": node("CLIPTextEncode", {"clip": ["2", 0], "text": pos}),
        "5": node("CLIPTextEncode", {"clip": ["2", 0], "text": neg}),
        "6": node("EmptyHunyuanLatentVideo", {"width": w, "height": h,
                                              "length": 1, "batch_size": 1}),
        "7": node("KSampler", {"model": ["1", 0], "positive": ["4", 0],
                               "negative": ["5", 0], "latent_image": ["6", 0],
                               "seed": seed, "steps": steps, "cfg": cfg,
                               "sampler_name": "uni_pc", "scheduler": "simple",
                               "denoise": 1.0}),
        "8": node("VAEDecode", {"samples": ["7", 0], "vae": ["3", 0]}),
        "9": node("SaveAnimatedWEBP", {"images": ["8", 0], "filename_prefix": prefix,
                                       "fps": 16.0, "lossless": False,
                                       "quality": 95, "method": "default"}),
    }


def post(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(HOST + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="the shot, without the style block")
    ap.add_argument("--avoid", default="",
                    help="colours that compete with the character's signature; "
                         "leaving this empty is what produced a yellow scarf twice")
    ap.add_argument("--out", default="still")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--cfg", type=float, default=7.0,
                    help="6.0 loses the colour, 8.5 holds it but squashes the "
                         "composition; 7.0 is the measured middle")
    ap.add_argument("--seed", type=int, default=20261121)
    a = ap.parse_args()

    neg = (a.avoid + ", " + NEG) if a.avoid else NEG
    wf = build(STYLE + ", " + a.prompt, neg, a.size, a.size,
               a.steps, a.cfg, a.seed, a.out)

    t0 = time.time()
    pid = post("/prompt", {"prompt": wf})["prompt_id"]
    print("submitted", pid, flush=True)
    while True:
        time.sleep(5)
        h = json.loads(urllib.request.urlopen(HOST + "/history/" + pid,
                                              timeout=30).read())
        if pid in h:
            break
    el = time.time() - t0
    st = h[pid]["status"]
    imgs = [i["filename"] for o in h[pid]["outputs"].values()
            for i in o.get("images", [])]
    print("status:", st.get("status_str"), "|", ", ".join(imgs))
    print("ELAPSED %.1f s  (%dx%d, %d steps, cfg %.1f)"
          % (el, a.size, a.size, a.steps, a.cfg))


if __name__ == "__main__":
    main()
