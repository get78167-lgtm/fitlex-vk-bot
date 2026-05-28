import sys
import os
import time

print("[DIAG-4] Start", flush=True)

try:
    import importlib.util
    spec = importlib.util.find_spec("vkbottle.modules")
    if spec:
        print(f"[DIAG-4] spec.origin: {spec.origin}", flush=True)
        if spec.origin and os.path.exists(spec.origin):
            with open(spec.origin, "r", encoding="utf-8") as f:
                content = f.read()
            print("[DIAG-4] Content of vkbottle.modules:\n", content, flush=True)
        else:
            print("[DIAG-4] Origin does not exist or is empty", flush=True)
    else:
        print("[DIAG-4] Spec not found for vkbottle.modules", flush=True)
except Exception as e:
    print(f"[DIAG-4] Error: {type(e).__name__}: {e}", flush=True)

print("[DIAG-4] Done. Sleeping...", flush=True)
time.sleep(3600)
