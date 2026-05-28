import sys
import os
import faulthandler
import time
import asyncio
import inspect
import warnings
from typing import Any, Protocol

faulthandler.enable()

print("[DIAG-3] Start", flush=True)

from choicelib import choice_in_order

print("[DIAG-3] choicelib imported", flush=True)

class JSONModule(Protocol):
    def loads(self, s: str) -> Any: ...
    def dumps(self, o: Any) -> str: ...
    def load(self, f: str) -> Any: ...
    def dump(self, o: Any, f: str) -> None: ...

print("[DIAG-3] JSONModule Protocol defined", flush=True)

print("[DIAG-3] Running choice_in_order for JSON...", flush=True)
json_mod = choice_in_order(
    ["orjson", "ujson", "hyperjson"],
    do_import=True,
    default="json",
)
print(f"[DIAG-3] json_mod: {json_mod}", flush=True)

def showwarning(message, category, filename, lineno, file=None, line=None):
    pass

logging_module = choice_in_order(["loguru"], default="logging")
print(f"[DIAG-3] logging_module: {logging_module}", flush=True)

if logging_module == "logging":
    import logging
    import colorama
    print("[DIAG-3] colorama imported", flush=True)
    colorama.just_fix_windows_console()
    print("[DIAG-3] just_fix_windows_console done", flush=True)

    LEVEL_COLORS = {
        "DEBUG": colorama.Style.BRIGHT + colorama.Fore.BLUE,
        "INFO": colorama.Style.BRIGHT + colorama.Fore.GREEN,
        "WARNING": colorama.Fore.YELLOW,
        "ERROR": colorama.Fore.RED,
        "CRITICAL": colorama.Style.BRIGHT + colorama.Fore.RED,
    }
    
    class ColorFormatter(logging.Formatter):
        def format(self, record):
            return super().format(record)

    class StyleAdapter(logging.LoggerAdapter):
        def __init__(self, logger, extra=None):
            super().__init__(logger, extra or {})
            print("[DIAG-3] inspect.getfullargspec check start", flush=True)
            self.log_arg_names = frozenset(inspect.getfullargspec(self.logger._log).args[1:])
            print("[DIAG-3] inspect.getfullargspec check end", flush=True)

    warnings.showwarning = showwarning
    _logger = logging.getLogger("vkbottle")
    
    if not _logger.handlers:
        console_handler = logging.StreamHandler()
        _logger.addHandler(console_handler)
        print("[DIAG-3] StreamHandler added", flush=True)
        
    _logger.handlers[0].setFormatter(ColorFormatter())
    print("[DIAG-3] Formatter set", flush=True)
    logger = StyleAdapter(_logger)
    print("[DIAG-3] StyleAdapter instantiated", flush=True)

print("[DIAG-3] Checking asyncio WindowsProactorEventLoopPolicy...", flush=True)
if hasattr(asyncio, "WindowsProactorEventLoopPolicy") and isinstance(
    asyncio.get_event_loop_policy(),
    asyncio.WindowsProactorEventLoopPolicy,
):
    print("[DIAG-3] WindowsProactorEventLoopPolicy workaround active (should not happen on Linux)", flush=True)

print("[DIAG-3] Attempting actual import of vkbottle.modules...", flush=True)
import vkbottle.modules
print("[DIAG-3] vkbottle.modules imported successfully!!!", flush=True)

print("[DIAG-3] Done. Sleeping...", flush=True)
time.sleep(3600)
