import sys
import os
import time

print("[DIAG-6] Start", flush=True)

try:
    import importlib.util
    spec = importlib.util.find_spec("vkbottle_types")
    if spec:
        print(f"[DIAG-6] spec.origin: {spec.origin}", flush=True)
        if spec.origin and os.path.exists(spec.origin):
            with open(spec.origin, "r", encoding="utf-8") as f:
                content = f.read()
            print("[DIAG-6] Content of vkbottle_types/__init__.py:\n", content, flush=True)
            
            # Let's check directory contents of vkbottle_types
            dir_path = os.path.dirname(spec.origin)
            print(f"[DIAG-6] Directory contents of {dir_path}:", os.listdir(dir_path), flush=True)
        else:
            print("[DIAG-6] Origin does not exist or is empty", flush=True)
    else:
        print("[DIAG-6] Spec not found for vkbottle_types", flush=True)
except Exception as e:
    print(f"[DIAG-6] Error: {type(e).__name__}: {e}", flush=True)

print("[DIAG-6] Done. Sleeping...", flush=True)
time.sleep(3600)
