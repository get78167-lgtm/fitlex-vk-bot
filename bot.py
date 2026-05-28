import sys
import os
import faulthandler
import time

# Включаем отслеживание низкоуровневых ошибок (Segmentation Fault)
faulthandler.enable()

print("[STARTUP-DIAG] bot.py запущен в режиме диагностики!", flush=True)
print(f"[STARTUP-DIAG] Python version: {sys.version}", flush=True)
print(f"[STARTUP-DIAG] Working directory: {os.getcwd()}", flush=True)
print(f"[STARTUP-DIAG] sys.path: {sys.path}", flush=True)

# Выведем список всех установленных пакетов
try:
    import importlib.metadata
    dists = sorted([f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions() if d.metadata and 'Name' in d.metadata])
    print("[STARTUP-DIAG] Installed packages:", dists, flush=True)
except Exception as e:
    print(f"[STARTUP-DIAG] Failed to list packages: {type(e).__name__}: {e}", flush=True)

# Список модулей для тестирования импорта
modules_to_test = [
    "dotenv",
    "pydantic",
    "aiohttp",
    "yarl",
    "multidict",
    "choicelib",
    "vbml",
    "orjson",
    "ujson",
    "hyperjson",
    "loguru",
    "colorama",
    "msgpack",
    "vkbottle.modules",
    "vkbottle.exception",
    "vkbottle.http",
    "vkbottle.api",
    "vkbottle.tools",
    "vkbottle.dispatch",
    "vkbottle.framework",
    "vkbottle.bot",
    "vkbottle",
]

for mod in modules_to_test:
    try:
        print(f"[STARTUP-DIAG] Попытка импорта {mod}...", flush=True)
        m = __import__(mod, fromlist=["*"] if "." in mod else [])
        print(f"[STARTUP-DIAG] {mod} успешно импортирован! Путь: {getattr(m, '__file__', 'no __file__')}", flush=True)
    except BaseException as e:
        print(f"[STARTUP-DIAG] ОШИБКА при импорте {mod}: {type(e).__name__}: {e}", flush=True)

print("[STARTUP-DIAG] Диагностика завершена. Спим 1 час для сохранения логов.", flush=True)
time.sleep(3600)
