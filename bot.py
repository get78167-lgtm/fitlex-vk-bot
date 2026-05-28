import sys
import os
import time

print("[DIAG-12] Start", flush=True)

path = "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/bot_events.py"
try:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        print("[DIAG-12] Content of bot_events.py:\n", content, flush=True)
    else:
        print("[DIAG-12] File not found", flush=True)
except Exception as e:
    print(f"[DIAG-12] Error: {type(e).__name__}: {e}", flush=True)

print("[DIAG-12] Done. Sleeping...", flush=True)
time.sleep(3600)
