import sys
import os
import time
import importlib.machinery

print("[DIAG-11] Start", flush=True)

paths = [
    ("bot_events", "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/bot_events.py"),
    ("bot_typings", "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/bot_typings.py"),
    ("enums", "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/enums/__init__.py"),
    ("user_events", "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/user_events.py"),
    ("user_typings", "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/user_typings.py"),
]

for name, path in paths:
    try:
        print(f"[DIAG-11] Loading {name} from {path}...", flush=True)
        loader = importlib.machinery.SourceFileLoader(name, path)
        mod = loader.load_module()
        print(f"[DIAG-11] {name} loaded successfully!", flush=True)
    except BaseException as e:
        print(f"[DIAG-11] Error loading {name}: {type(e).__name__}: {e}", flush=True)

print("[DIAG-11] Done. Sleeping...", flush=True)
time.sleep(3600)
