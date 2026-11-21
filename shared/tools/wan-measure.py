"""First real local Wan generation: submit one shot and measure the wall clock.

The point of this run is a number, not a picture. Every estimate in
STACK_DECISION.md about generation time is a guess until this prints.
"""
import json, sys, time, urllib.request, uuid

HOST = "http://127.0.0.1:8188"
POS = ("3D vinyl toy style, close up of a small round grey kitten wearing a "
       "bright red scarf, big dark glossy eyes, one paw slowly reaching "
       "forward, bright simple kitchen, warm cream walls, soft studio light, "
       "cute collectible figurine look, childrens animation")
NEG = ("blurry, low quality, distorted, extra limbs, text, watermark, "
       "scary, dark, violent")

W, H, FRAMES, STEPS = 480, 480, 33, 20   # 33 frames @16fps ~ 2.1s


def node(ct, inputs):
    return {"class_type": ct, "inputs": inputs}


wf = {
    "1": node("UNETLoader", {"unet_name": "wan2.1_t2v_1.3B_fp16.safetensors",
                             "weight_dtype": "default"}),
    "2": node("CLIPLoader", {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                             "type": "wan", "device": "default"}),
    "3": node("VAELoader", {"vae_name": "wan_2.1_vae.safetensors"}),
    "4": node("CLIPTextEncode", {"clip": ["2", 0], "text": POS}),
    "5": node("CLIPTextEncode", {"clip": ["2", 0], "text": NEG}),
    "6": node("EmptyHunyuanLatentVideo", {"width": W, "height": H,
                                          "length": FRAMES, "batch_size": 1}),
    "7": node("KSampler", {"model": ["1", 0], "positive": ["4", 0],
                           "negative": ["5", 0], "latent_image": ["6", 0],
                           "seed": 20261121, "steps": STEPS, "cfg": 6.0,
                           "sampler_name": "uni_pc", "scheduler": "simple",
                           "denoise": 1.0}),
    "8": node("VAEDecode", {"samples": ["7", 0], "vae": ["3", 0]}),
    "9": node("SaveAnimatedWEBP", {"images": ["8", 0], "filename_prefix": "kd001-shot3",
                                   "fps": 16.0, "lossless": False, "quality": 90,
                                   "method": "default"}),
}

cid = str(uuid.uuid4())
body = json.dumps({"prompt": wf, "client_id": cid}).encode()
req = urllib.request.Request(HOST + "/prompt", body,
                             {"Content-Type": "application/json"})
t0 = time.time()
try:
    pid = json.load(urllib.request.urlopen(req))["prompt_id"]
except urllib.error.HTTPError as e:
    print("REJECTED:", e.read().decode()[:2000]); sys.exit(1)
print("submitted", pid, flush=True)

while True:
    time.sleep(5)
    h = json.load(urllib.request.urlopen(HOST + "/history/" + pid))
    if pid in h:
        el = time.time() - t0
        st = h[pid]["status"]
        print(json.dumps(h[pid]["outputs"], ensure_ascii=False)[:600])
        print("status:", st.get("status_str"))
        print("ELAPSED %.1f s for %dx%d x %d frames x %d steps"
              % (el, W, H, FRAMES, STEPS))
        print("=> %.2f s per frame | a 41s video needs %d such shots"
              % (el / FRAMES, 8))
        break
    if time.time() - t0 > 3600:
        print("TIMEOUT after 60 min"); break
