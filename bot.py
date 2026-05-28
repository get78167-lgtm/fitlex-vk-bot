import sys
import time

print("[DIAG-5] Start", flush=True)

test_imports = [
    "vkbottle_types",
    "vkbottle_types.events",
    "vkbottle_types.objects",
    "vkbottle_types.methods",
    "vkbottle.api",
    "vkbottle.dispatch",
    "vkbottle.exception_factory",
    "vkbottle.framework",
    "vkbottle.http",
    "vkbottle.polling",
    "vkbottle.tools",
]

for mod in test_imports:
    try:
        print(f"[DIAG-5] Importing {mod}...", flush=True)
        m = __import__(mod, fromlist=["*"] if "." in mod else [])
        print(f"[DIAG-5] {mod} imported successfully!", flush=True)
    except BaseException as e:
        print(f"[DIAG-5] Error importing {mod}: {type(e).__name__}: {e}", flush=True)

print("[DIAG-5] Done. Sleeping...", flush=True)
time.sleep(3600)
