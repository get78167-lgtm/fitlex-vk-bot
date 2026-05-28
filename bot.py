import sys
import os
import time

print("[DIAG-8] Start", flush=True)

try:
    import importlib.util
    spec = importlib.util.find_spec("vkbottle_types.base_model")
    if spec:
        print(f"[DIAG-8] spec.origin: {spec.origin}", flush=True)
        if spec.origin and os.path.exists(spec.origin):
            with open(spec.origin, "r", encoding="utf-8") as f:
                content = f.read()
            print("[DIAG-8] Content of vkbottle_types/base_model.py:\n", content, flush=True)
        else:
            print("[DIAG-8] Origin does not exist or is empty", flush=True)
    else:
        print("[DIAG-8] Spec not found for vkbottle_types.base_model", flush=True)
except Exception as e:
    print(f"[DIAG-8] Error: {type(e).__name__}: {e}", flush=True)

print("[DIAG-8] Done. Sleeping...", flush=True)
time.sleep(3600)
