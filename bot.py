import sys
import os
import faulthandler
import time

faulthandler.enable()

print("[DIAG-2] Start", flush=True)

try:
    print("[DIAG-2] Importing colorama...", flush=True)
    import colorama
    print("[DIAG-2] colorama imported successfully.", flush=True)
    
    print("[DIAG-2] Calling colorama.just_fix_windows_console()...", flush=True)
    colorama.just_fix_windows_console()
    print("[DIAG-2] colorama.just_fix_windows_console() succeeded!", flush=True)
except BaseException as e:
    print(f"[DIAG-2] colorama failure: {type(e).__name__}: {e}", flush=True)

try:
    print("[DIAG-2] Importing choicelib...", flush=True)
    from choicelib import choice_in_order
    print("[DIAG-2] choicelib imported successfully.", flush=True)
    
    print("[DIAG-2] Running choice_in_order for JSON...", flush=True)
    json = choice_in_order(["orjson", "ujson", "hyperjson"], do_import=True, default="json")
    print(f"[DIAG-2] choice_in_order for JSON succeeded: {json}", flush=True)
except BaseException as e:
    print(f"[DIAG-2] choicelib/json failure: {type(e).__name__}: {e}", flush=True)

try:
    print("[DIAG-2] Running choice_in_order for loguru...", flush=True)
    logging_module = choice_in_order(["loguru"], default="logging")
    print(f"[DIAG-2] choice_in_order for loguru succeeded: {logging_module}", flush=True)
except BaseException as e:
    print(f"[DIAG-2] loguru choice failure: {type(e).__name__}: {e}", flush=True)

print("[DIAG-2] Done. Sleeping...", flush=True)
time.sleep(3600)
