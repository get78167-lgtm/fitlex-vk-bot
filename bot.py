import sys
import os
import time

print("[DIAG-10] Start", flush=True)

path = "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/__init__.py"
try:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        print("[DIAG-10] Content of events/__init__.py:\n", content, flush=True)
        
        # Also print event directory files
        dir_path = os.path.dirname(path)
        print(f"[DIAG-10] Files in events folder: {os.listdir(dir_path)}", flush=True)
    else:
        print("[DIAG-10] File not found", flush=True)
except Exception as e:
    print(f"[DIAG-10] Error: {type(e).__name__}: {e}", flush=True)

print("[DIAG-10] Done. Sleeping...", flush=True)
time.sleep(3600)
