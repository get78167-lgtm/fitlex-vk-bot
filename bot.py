import sys
import time

print("[DIAG-7] Start", flush=True)

try:
    print("[DIAG-7] Importing typing...", flush=True)
    import typing
    print("[DIAG-7] typing imported.", flush=True)
except BaseException as e:
    print(f"[DIAG-7] typing failed: {e}", flush=True)

try:
    print("[DIAG-7] Importing vkbottle_types.base_model...", flush=True)
    import vkbottle_types.base_model
    print("[DIAG-7] vkbottle_types.base_model imported.", flush=True)
except BaseException as e:
    print(f"[DIAG-7] vkbottle_types.base_model failed: {e}", flush=True)

try:
    print("[DIAG-7] Importing vkbottle_types.categories...", flush=True)
    import vkbottle_types.categories
    print("[DIAG-7] vkbottle_types.categories imported.", flush=True)
except BaseException as e:
    print(f"[DIAG-7] vkbottle_types.categories failed: {e}", flush=True)

try:
    print("[DIAG-7] Importing vkbottle_types.events...", flush=True)
    import vkbottle_types.events
    print("[DIAG-7] vkbottle_types.events imported.", flush=True)
except BaseException as e:
    print(f"[DIAG-7] vkbottle_types.events failed: {e}", flush=True)

print("[DIAG-7] Done. Sleeping...", flush=True)
time.sleep(3600)
