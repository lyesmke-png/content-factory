#!/usr/bin/env bash
# Start ComfyUI with the only flag set that survives on this machine.
#
# Without --disable-pinned-memory the text encoder is staged as 6419MB of
# PINNED memory, which cannot be paged out, so the OS memory guard kills the
# process even with 10.4GB free. Measured: killed four times at that exact
# line, started first try with these flags.
#
# --cache-none is deliberately NOT passed. It was, and it cost 154 s on every
# single shot: the models were evicted after each one and reloaded for the
# next. Measured at 512x512 x 20 steps: 236 s for the first shot, then 85 s
# for every shot after it. Leave the cache on and generate a whole scene
# list against one running server.
#
# --mmap-torch-files maps the weights from disk, so their pages stay
# file-backed and reclaimable instead of being read into anonymous RAM.
exec python "${COMFYUI_DIR:-D:/AI/ComfyUI}/main.py" \
    --lowvram \
    --disable-pinned-memory --mmap-torch-files --disable-async-offload "$@"
