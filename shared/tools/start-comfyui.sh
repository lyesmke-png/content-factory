#!/usr/bin/env bash
# Start ComfyUI with the only flag set that survives on this machine.
#
# Without --disable-pinned-memory the text encoder is staged as 6419MB of
# PINNED memory, which cannot be paged out, so the OS memory guard kills the
# process even with 10.4GB free. Measured: killed four times at that exact
# line, started first try with these flags.
#
# --mmap-torch-files maps the weights from disk, so their pages stay
# file-backed and reclaimable instead of being read into anonymous RAM.
exec python "${COMFYUI_DIR:-D:/AI/ComfyUI}/main.py" \
    --lowvram --cache-none \
    --disable-pinned-memory --mmap-torch-files --disable-async-offload "$@"
