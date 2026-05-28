import sys
import os
import time
import importlib.machinery

print("[DIAG-9] Start", flush=True)

paths = [
    ("base_model", "/usr/local/lib/python3.11/site-packages/vkbottle_types/base_model.py"),
    ("categories", "/usr/local/lib/python3.11/site-packages/vkbottle_types/categories.py"),
    ("events", "/usr/local/lib/python3.11/site-packages/vkbottle_types/events/__init__.py"),
]

for name, path in paths:
    try:
        print(f"[DIAG-9] Loading {name} from {path}...", flush=True)
        loader = importlib.machinery.SourceFileLoader(name, path)
        mod = loader.load_module()
        print(f"[DIAG-9] {name} loaded successfully!", flush=True)
    except BaseException as e:
        print(f"[DIAG-9] Error loading {name}: {type(e).__name__}: {e}", flush=True)

print("[DIAG-9] Done. Sleeping...", flush=True)
time.sleep(3600)
