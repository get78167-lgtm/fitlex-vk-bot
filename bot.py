"""
VK Bot для сообщества FITLEX — «Краски и грунтовки оптом и в розницу»

Функции: каталог товаров, корзина, оплата ЮКасса, FAQ, информация о компании.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import threading
import uuid
from typing import Any

# Принудительно отключаем буферизацию вывода (для Docker/BotHost)
os.environ.setdefault("PYTHONUNBUFFERED", "1")

print("[STARTUP] bot.py загружается...", flush=True)

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[STARTUP] dotenv загружен", flush=True)
except Exception as e:
    print(f"[STARTUP] WARN dotenv: {type(e).__name__}: {e}", flush=True)

from vkbottle import (
    Callback,
    GroupEventType,
    GroupTypes,
    Keyboard,
    KeyboardButtonColor,
    OpenLink,
    Text,
)
from vkbottle.bot import Bot, Message
from yookassa import Configuration, Payment

print("[STARTUP] зависимости загружены", flush=True)

# ═══════════════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

VK_TOKEN = os.getenv("VK_TOKEN", "")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

if not VK_TOKEN or not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
    print("[STARTUP] FATAL: не заданы VK_TOKEN / YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY", flush=True)
    raise RuntimeError("Не заданы обязательные переменные окружения")

GROUP_ID = 215128871
PAYMENT_CURRENCY = "RUB"
POLL_INTERVAL_SEC = 5
POLL_MAX_ATTEMPTS = 60
GROUP_CHAT_PEER_OFFSET = 2_000_000_000  # VK прибавляет это к chat_id для бесед

COMPANY_INFO = (
    "🏭 ООО «АТА-групп» (FITLEX)\n"
    "ИНН: 5003166596\n"
    "📞 +7 (916) 876-84-24\n"
    "📍 Москва, Варшавское шоссе вл 248 с2\n"
    "🌐 https://dzen.ru/fitlex\n\n"
    "🚚 Доставка: курьер, СДЭК, Почта России, самовывоз\n"
    "💰 Минимальный заказ: 2 000 ₽\n"
    "🎁 Бесплатная доставка"
)

# ═══════════════════════════════════════════════════════════════
#  ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fitlex_bot")

# ═══════════════════════════════════════════════════════════════
#  ИНИЦИАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

bot = Bot(token=VK_TOKEN)

# Хранилище ссылок на фоновые задачи (защита от GC)
_background_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


# ═══════════════════════════════════════════════════════════════
#  КАТАЛОГ ТОВАРОВ
# ═══════════════════════════════════════════════════════════════

CATALOG = [
    {
        "id": 1,
        "name": "Грунтовка FITLEX Elite Edition 5л",
        "price": 670,
        "description": (
            "Профессиональная грунтовка глубокого проникновения FITLEX Elite Edition.\n\n"
            "📦 Объём: 5 литров\n"
            "🏗 Применение: внутренние и наружные работы по бетону, кирпичу, штукатурке\n"
            "📏 Расход: 100–200 мл/м²\n"
            "⭐ 5.0 (4 отзыва)"
        ),
    },
    {
        "id": 2,
        "name": "Грунтовка FITLEX Elite Edition 10л",
        "price": 1120,
        "description": (
            "Профессиональная грунтовка глубокого проникновения FITLEX Elite Edition.\n\n"
            "📦 Объём: 10 литров\n"
            "🏗 Применение: внутренние и наружные работы по бетону, кирпичу, штукатурке\n"
            "📏 Расход: 100–200 мл/м²\n"
            "⭐ 5.0 (1 отзыв)"
        ),
    },
    {
        "id": 3,
        "name": "Грунтовка FITLEX 10 литров",
        "price": 890,
        "description": (
            "Универсальная грунтовка FITLEX для подготовки поверхностей.\n\n"
            "📦 Объём: 10 литров\n"
            "🏗 Применение: бетон, кирпич, штукатурка, гипсокартон, цементные стяжки\n"
            "📏 Расход: 100–200 мл/м²\n"
            "⭐ 5.0 (1 отзыв)"
        ),
    },
    {
        "id": 4,
        "name": "Грунтовка глубокого проникновения 1л",
        "price": 170,
        "description": (
            "Грунтовка глубокого проникновения FITLEX для укрепления пористых оснований.\n\n"
            "📦 Объём: 1 литр\n"
            "🏗 Применение: рыхлые штукатурки, пористый бетон, старые основания\n"
            "📏 Расход: 100–200 мл/м²"
        ),
    },
    {
        "id": 5,
        "name": "Грунтовка глубокого проникновения 5л",
        "price": 440,
        "description": (
            "Грунтовка глубокого проникновения FITLEX для укрепления пористых оснований.\n\n"
            "📦 Объём: 5 литров\n"
            "🏗 Применение: рыхлые штукатурки, пористый бетон, старые основания\n"
            "📏 Расход: 100–200 мл/м²"
        ),
    },
]

CATALOG_BY_ID = {p["id"]: p for p in CATALOG}

# ═══════════════════════════════════════════════════════════════
#  FAQ
# ═══════════════════════════════════════════════════════════════

FAQ_ITEMS = {
    1: (
        "🔹 Для стандартных работ — Грунтовка FITLEX 10л (890 ₽)\n"
        "🔹 Для профессиональных — FITLEX Elite Edition (670/1120 ₽)\n"
        "🔹 Для рыхлых оснований — Глубокого проникновения (170/440 ₽)"
    ),
    2: (
        "📏 Расход: 100–200 мл/м²\n"
        "• Гладкий бетон — ~100 мл/м²\n"
        "• Штукатурка — ~150 мл/м²\n"
        "• Пористое основание — ~200 мл/м²\n"
        "Наносить 1–2 слоя, сушка 1–2 часа между слоями."
    ),
    3: (
        "🚚 Курьер по Москве, СДЭК и Почта России по всей РФ\n"
        "📍 Самовывоз: Варшавское шоссе вл 248 с2\n"
        "💰 Минимальный заказ: 2 000 ₽\n"
        "🎁 Есть бесплатная доставка"
    ),
    4: (
        "💳 Оплата через бота — безопасная оплата онлайн\n"
        "🏦 Также можно оплатить по реквизитам на расчётный счёт\n"
        "📱 VK Pay — оплата со счёта мобильного через ВК"
    ),
}

# ═══════════════════════════════════════════════════════════════
#  КОРЗИНА (атомарное файловое хранилище)
# ═══════════════════════════════════════════════════════════════

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CART_FILE = os.path.join(_DATA_DIR, "carts.json")
PENDING_FILE = os.path.join(_DATA_DIR, "pending_payments.json")

_carts_lock = threading.Lock()
_pending_lock = threading.Lock()


def _atomic_write_json(path: str, data: Any) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_cart(user_id: int) -> dict[int, int]:
    with _carts_lock:
        carts = _read_json(CART_FILE)
    raw = carts.get(str(user_id), {})
    return {int(k): v for k, v in raw.items()}


def set_cart(user_id: int, cart: dict[int, int]) -> None:
    with _carts_lock:
        carts = _read_json(CART_FILE)
        if cart:
            carts[str(user_id)] = {str(k): v for k, v in cart.items()}
        else:
            carts.pop(str(user_id), None)
        try:
            _atomic_write_json(CART_FILE, carts)
        except OSError as exc:
            logger.error("Ошибка сохранения корзин: %s", exc)


def clear_cart(user_id: int) -> None:
    set_cart(user_id, {})


def cart_total(user_id: int) -> int:
    cart = get_cart(user_id)
    return sum(CATALOG_BY_ID[pid]["price"] * qty for pid, qty in cart.items())


def cart_text(user_id: int) -> str:
    cart = get_cart(user_id)
    if not cart:
        return "🛒 Корзина пуста.\n\nОткройте каталог, чтобы добавить товары."
    lines = ["🛒 Ваша корзина:\n"]
    for i, (pid, qty) in enumerate(cart.items(), 1):
        p = CATALOG_BY_ID[pid]
        subtotal = p["price"] * qty
        lines.append(f"{i}. {p['name']} × {qty} = {subtotal} ₽")
    lines.append(f"\n💰 Итого: {cart_total(user_id)} ₽")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  PENDING PAYMENTS (переживает рестарт бота)
# ═══════════════════════════════════════════════════════════════


def _load_pending() -> dict[str, int]:
    with _pending_lock:
        raw = _read_json(PENDING_FILE)
    out: dict[str, int] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    return out


pending_payments: dict[str, int] = _load_pending()


def _persist_pending() -> None:
    with _pending_lock:
        try:
            _atomic_write_json(PENDING_FILE, pending_payments)
        except OSError as exc:
            logger.error("Ошибка сохранения pending_payments: %s", exc)


def add_pending(payment_id: str, user_id: int) -> None:
    pending_payments[payment_id] = user_id
    _persist_pending()


def remove_pending(payment_id: str) -> None:
    pending_payments.pop(payment_id, None)
    _persist_pending()


# ═══════════════════════════════════════════════════════════════
#  КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════════════


def kb_main_menu() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📦 Каталог"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("🛒 Корзина"), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("❓ Консультация"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("ℹ️ О компании"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def _short_name(name: str) -> str:
    return name.replace("Грунтовка ", "").replace("глубокого проникновения", "глуб. проник.")


def kb_catalog() -> str:
    kb = Keyboard(inline=True)
    for p in CATALOG:
        # VK limit: button label ≤ 40 chars
        label = f"{_short_name(p['name'])} — {p['price']}₽"
        kb.add(Callback(label[:40], payload={"c": "d", "id": p["id"]}))
        kb.row()
    return kb.get_json()


def kb_product(product_id: int) -> str:
    kb = Keyboard(inline=True)
    kb.add(Callback("🛒 В корзину", payload={"c": "a", "id": product_id}), color=KeyboardButtonColor.POSITIVE)
    kb.add(Callback("⬅️ Каталог", payload={"c": "cat"}))
    return kb.get_json()


def kb_cart(user_id: int) -> str:
    kb = Keyboard(inline=True)
    cart = get_cart(user_id)
    if cart:
        for pid in cart:
            p = CATALOG_BY_ID[pid]
            kb.add(Callback(f"❌ {_short_name(p['name'])}"[:40], payload={"c": "rm", "id": pid}))
            kb.row()
        kb.add(Callback("💳 Оплатить", payload={"c": "pay"}), color=KeyboardButtonColor.POSITIVE)
        kb.add(Callback("🗑 Очистить", payload={"c": "clr"}), color=KeyboardButtonColor.NEGATIVE)
    else:
        kb.add(Callback("📦 Каталог", payload={"c": "cat"}), color=KeyboardButtonColor.PRIMARY)
    return kb.get_json()


def kb_faq() -> str:
    kb = Keyboard(inline=True)
    kb.add(Callback("Какую грунтовку выбрать?", payload={"c": "faq", "id": 1}))
    kb.row()
    kb.add(Callback("Расход грунтовки", payload={"c": "faq", "id": 2}))
    kb.row()
    kb.add(Callback("Условия доставки", payload={"c": "faq", "id": 3}))
    kb.row()
    kb.add(Callback("Как оплатить?", payload={"c": "faq", "id": 4}))
    return kb.get_json()


# ═══════════════════════════════════════════════════════════════
#  ОПЛАТА ЮКасса (sync SDK — оборачиваем в to_thread)
# ═══════════════════════════════════════════════════════════════


async def _yk_create(payload: dict, idempotence_key: str):
    return await asyncio.to_thread(Payment.create, payload, idempotence_key)


async def _yk_find(payment_id: str):
    return await asyncio.to_thread(Payment.find_one, payment_id)


async def create_payment(user_id: int):
    amount = cart_total(user_id)
    if amount <= 0:
        return None
    cart = get_cart(user_id)
    items = [f"{CATALOG_BY_ID[pid]['name']} ×{qty}" for pid, qty in cart.items()]
    description = "FITLEX: " + ", ".join(items)
    if len(description) > 128:
        description = description[:125] + "..."

    receipt_items = []
    for pid, qty in cart.items():
        p = CATALOG_BY_ID[pid]
        receipt_items.append({
            "description": p["name"][:128],
            "quantity": str(qty),
            "amount": {"value": f"{p['price']}.00", "currency": PAYMENT_CURRENCY},
            "vat_code": 1,
            "payment_subject": "commodity",
            "payment_mode": "full_payment",
        })

    try:
        payment = await _yk_create(
            {
                "amount": {"value": f"{amount}.00", "currency": PAYMENT_CURRENCY},
                "confirmation": {"type": "redirect", "return_url": "https://vk.com/fitlex_group"},
                "capture": True,
                "description": description,
                "metadata": {"vk_user_id": str(user_id)},
                "receipt": {
                    "customer": {"email": "order@fitlex.ru"},
                    "items": receipt_items,
                },
            },
            str(uuid.uuid4()),
        )
        logger.info("Платёж создан: id=%s, user=%s, сумма=%s", payment.id, user_id, amount)
        return payment
    except Exception as exc:
        logger.error("Ошибка создания платежа для user=%s: %s", user_id, exc)
        return None


async def _safe_send(**kwargs) -> None:
    try:
        await bot.api.messages.send(random_id=0, **kwargs)
    except Exception as exc:
        logger.warning("messages.send failed: %s (kwargs=%s)", exc, list(kwargs))


async def poll_payment_status(payment_id: str, user_id: int) -> None:
    logger.info("Отслеживание платежа %s для user=%s", payment_id, user_id)
    for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
        await asyncio.sleep(POLL_INTERVAL_SEC)
        try:
            payment = await _yk_find(payment_id)
        except Exception as exc:
            logger.warning("Ошибка проверки %s (попытка %d): %s", payment_id, attempt, exc)
            continue

        if payment.status == "succeeded":
            logger.info("Платёж %s успешен!", payment_id)
            clear_cart(user_id)
            await _safe_send(
                user_id=user_id,
                message=(
                    f"✅ Оплата прошла успешно!\n\n"
                    f"💰 Сумма: {payment.amount.value} ₽\n"
                    f"🆔 Платёж: {payment_id}\n\n"
                    "Спасибо за покупку! Мы свяжемся с вами для уточнения доставки."
                ),
                keyboard=kb_main_menu(),
            )
            remove_pending(payment_id)
            return

        if payment.status == "canceled":
            logger.info("Платёж %s отменён.", payment_id)
            await _safe_send(
                user_id=user_id,
                message="❌ Платёж отменён. Попробуйте снова.",
                keyboard=kb_main_menu(),
            )
            remove_pending(payment_id)
            return

    logger.warning("Таймаут для платежа %s", payment_id)
    await _safe_send(
        user_id=user_id,
        message="⏳ Время ожидания оплаты истекло. Вернитесь в корзину и попробуйте снова.",
        keyboard=kb_main_menu(),
    )
    remove_pending(payment_id)


async def _get_first_name(user_id: int) -> str:
    try:
        users = await bot.api.users.get(user_ids=[user_id])
        if users:
            return users[0].first_name or "друг"
    except Exception as exc:
        logger.warning("users.get failed for %s: %s", user_id, exc)
    return "друг"


# ═══════════════════════════════════════════════════════════════
#  ОБРАБОТЧИК ЗАКАЗОВ VK MARKET
# ═══════════════════════════════════════════════════════════════


@bot.on.raw_event("market_order_new", dataclass=dict)
async def on_market_order(event: dict):
    """Обработка нового заказа из VK Market."""
    order = event.get("object", event)
    logger.info("MARKET ORDER RAW: %s", json.dumps(order, ensure_ascii=False, default=str)[:1000])

    order_id = order.get("id", "—")
    buyer_id = order.get("user_id") or order.get("buyer_id")
    total_price = order.get("total_price", {})

    amount = 0
    if isinstance(total_price, dict):
        amount = int(total_price.get("amount", 0))
        if amount > 10000:  # VK иногда отдаёт в копейках
            amount = amount // 100
    elif isinstance(total_price, (int, float)):
        amount = int(total_price)

    delivery = 0
    delivery_info = order.get("delivery", {})
    if isinstance(delivery_info, dict):
        delivery_price = delivery_info.get("price", {})
        if isinstance(delivery_price, dict):
            delivery = int(delivery_price.get("amount", 0))
            if delivery > 10000:
                delivery = delivery // 100
        elif isinstance(delivery_price, (int, float)):
            delivery = int(delivery_price)

    logger.info(
        "Заказ VK Market: id=%s, buyer=%s, amount=%s, delivery=%s",
        order_id, buyer_id, amount, delivery,
    )

    if not buyer_id:
        logger.warning("Не удалось определить покупателя для заказа %s", order_id)
        return

    kb = Keyboard(inline=True)
    order_url = f"https://vk.com/orders{buyer_id}_{order_id}"
    kb.add(OpenLink(order_url, label="💳 Оплатить через VK Pay"))
    kb.row()

    full_amount = amount + delivery if delivery > 0 else amount
    if full_amount > 0:
        kb.add(Callback(
            "💳 Оплатить через ЮКасса",
            payload={"c": "pay_order", "amount": full_amount, "order": str(order_id)},
        ))

    msg_text = f"✅ Заказ №{order_id} оформлен!\n\n💰 Сумма товаров: {amount} ₽\n"
    if delivery > 0:
        msg_text += f"🚚 Доставка: {delivery} ₽\n💵 Итого: {amount + delivery} ₽\n"
    msg_text += "\nВыберите способ оплаты:"

    await _safe_send(user_id=buyer_id, message=msg_text, keyboard=kb.get_json())
    logger.info("Кнопки оплаты отправлены покупателю %s", buyer_id)


# ═══════════════════════════════════════════════════════════════
#  ОБРАБОТЧИК CALLBACK-КНОПОК (inline)
# ═══════════════════════════════════════════════════════════════


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=GroupTypes.MessageEvent)
async def on_callback(event: GroupTypes.MessageEvent):
    payload = event.object.payload
    user_id = event.object.user_id
    peer_id = event.object.peer_id
    event_id = event.object.event_id

    if not payload:
        return

    cmd = payload.get("c")
    pid = payload.get("id")
    snackbar: str | None = None

    if cmd == "d" and pid:
        product = CATALOG_BY_ID.get(pid)
        if product:
            await _safe_send(
                user_id=user_id,
                message=f"📋 {product['name']}\n💰 {product['price']} ₽\n\n{product['description']}",
                keyboard=kb_product(pid),
            )

    elif cmd == "a" and pid:
        cart = get_cart(user_id)
        cart[pid] = cart.get(pid, 0) + 1
        set_cart(user_id, cart)
        product = CATALOG_BY_ID.get(pid)
        snackbar = f"✅ {product['name']} добавлен в корзину" if product else "✅ Добавлено"
        logger.info("user=%s добавил товар %s в корзину", user_id, pid)

    elif cmd == "rm" and pid:
        cart = get_cart(user_id)
        cart.pop(pid, None)
        set_cart(user_id, cart)
        snackbar = "🗑 Товар удалён из корзины"
        await _safe_send(
            user_id=user_id,
            message=cart_text(user_id),
            keyboard=kb_cart(user_id),
        )

    elif cmd == "clr":
        clear_cart(user_id)
        snackbar = "🗑 Корзина очищена"
        await _safe_send(
            user_id=user_id,
            message="🛒 Корзина очищена.",
            keyboard=kb_main_menu(),
        )

    elif cmd == "cat":
        lines = ["📦 Каталог товаров FITLEX:\n"]
        for p in CATALOG:
            lines.append(f"• {p['name']} — {p['price']} ₽")
        lines.append("\nНажмите на товар для подробностей:")
        await _safe_send(
            user_id=user_id,
            message="\n".join(lines),
            keyboard=kb_catalog(),
        )

    elif cmd == "pay":
        total = cart_total(user_id)
        if total < 2000:
            snackbar = f"⚠️ Минимальный заказ 2 000 ₽ (сейчас {total} ₽)"
        else:
            payment = await create_payment(user_id)
            if payment:
                url = payment.confirmation.confirmation_url
                pay_kb = Keyboard(inline=True)
                pay_kb.add(OpenLink(url, label="💳 Перейти к оплате"))

                add_pending(payment.id, user_id)
                await _safe_send(
                    user_id=user_id,
                    message=(
                        f"💰 Сумма: {total} ₽\n\n"
                        "Нажмите кнопку ниже для оплаты.\n"
                        "После оплаты я пришлю подтверждение."
                    ),
                    keyboard=pay_kb.get_json(),
                )
                _spawn(poll_payment_status(payment.id, user_id))
            else:
                snackbar = "⚠️ Ошибка создания платежа"

    elif cmd == "pay_order":
        order_amount = payload.get("amount", 0)
        order_num = payload.get("order", "—")
        if order_amount > 0:
            try:
                receipt_items = [{
                    "description": f"Оплата заказа №{order_num}"[:128],
                    "quantity": "1",
                    "amount": {"value": f"{order_amount}.00", "currency": PAYMENT_CURRENCY},
                    "vat_code": 1,
                    "payment_subject": "commodity",
                    "payment_mode": "full_payment",
                }]
                payment = await _yk_create(
                    {
                        "amount": {"value": f"{order_amount}.00", "currency": PAYMENT_CURRENCY},
                        "confirmation": {"type": "redirect", "return_url": "https://vk.com/fitlex_group"},
                        "capture": True,
                        "description": f"FITLEX заказ №{order_num}",
                        "metadata": {"vk_user_id": str(user_id), "order": order_num},
                        "receipt": {
                            "customer": {"email": "order@fitlex.ru"},
                            "items": receipt_items,
                        },
                    },
                    str(uuid.uuid4()),
                )
                url = payment.confirmation.confirmation_url
                pay_kb = Keyboard(inline=True)
                pay_kb.add(OpenLink(url, label=f"💳 Оплатить {order_amount} ₽"))

                add_pending(payment.id, user_id)
                await _safe_send(
                    user_id=user_id,
                    message=(
                        f"💳 Оплата заказа №{order_num} через ЮКасса\n\n"
                        f"💰 Сумма: {order_amount} ₽\n\n"
                        "Нажмите кнопку ниже для оплаты.\n"
                        "После оплаты я пришлю подтверждение."
                    ),
                    keyboard=pay_kb.get_json(),
                )
                _spawn(poll_payment_status(payment.id, user_id))
            except Exception as exc:
                logger.error("Ошибка оплаты заказа VK: %s", exc)
                snackbar = "⚠️ Ошибка создания платежа"
        else:
            snackbar = "⚠️ Не удалось определить сумму заказа"

    elif cmd == "faq" and pid:
        answer = FAQ_ITEMS.get(pid, "Информация не найдена.")
        await _safe_send(
            user_id=user_id,
            message=answer,
            keyboard=kb_faq(),
        )

    # Закрываем спиннер кнопки
    try:
        event_data = json.dumps({"type": "show_snackbar", "text": (snackbar or "✅")[:90]})
        await bot.api.messages.send_message_event_answer(
            event_id=event_id, user_id=user_id, peer_id=peer_id,
            event_data=event_data,
        )
    except Exception as exc:
        logger.warning("Ошибка ответа на callback: %s", exc)


# ═══════════════════════════════════════════════════════════════
#  ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# ═══════════════════════════════════════════════════════════════


async def _send_catalog(message: Message) -> None:
    lines = ["📦 Каталог товаров FITLEX:\n"]
    for p in CATALOG:
        lines.append(f"• {p['name']} — {p['price']} ₽")
    lines.append("\nНажмите на товар для подробностей:")
    await message.answer("\n".join(lines), keyboard=kb_catalog())


@bot.on.message(text=["Каталог", "📦 Каталог", "🛒 Каталог", "каталог", "товары"])
async def handle_catalog(message: Message):
    logger.info("Каталог запрошен user=%s", message.from_id)
    await _send_catalog(message)


@bot.on.message(text=["Корзина", "🛒 Корзина", "📦 Корзина", "корзина"])
async def handle_cart(message: Message):
    logger.info("Корзина запрошена user=%s", message.from_id)
    await message.answer(cart_text(message.from_id), keyboard=kb_cart(message.from_id))


@bot.on.message(text=["Консультация", "❓ Консультация", "консультация", "помощь", "faq"])
async def handle_faq(message: Message):
    logger.info("FAQ запрошен user=%s", message.from_id)
    await message.answer(
        "❓ Часто задаваемые вопросы:\n\nВыберите тему:",
        keyboard=kb_faq(),
    )


@bot.on.message(text=["О компании", "ℹ️ О компании", "о компании", "контакты", "инфо"])
async def handle_about(message: Message):
    logger.info("Инфо запрошено user=%s", message.from_id)
    await message.answer(COMPANY_INFO, keyboard=kb_main_menu())


_MENTION_RE = re.compile(
    r'\[club' + str(GROUP_ID) + r'\|[^\]]*\]\s*|@fitlex_group\s*',
    re.IGNORECASE,
)

_GROUP_CMD_MAP = {
    "каталог": "catalog",
    "📦 каталог": "catalog",
    "🛒 каталог": "catalog",
    "товары": "catalog",
    "корзина": "cart",
    "🛒 корзина": "cart",
    "📦 корзина": "cart",
    "консультация": "faq",
    "❓ консультация": "faq",
    "помощь": "faq",
    "о компании": "about",
    "ℹ️ о компании": "about",
    "контакты": "about",
}


@bot.on.message()
async def handle_any(message: Message):
    logger.info(
        "RAW MSG: from_id=%s, peer_id=%s, text=%r, attachments=%s",
        message.from_id, message.peer_id,
        (message.text or "")[:200],
        len(message.attachments) if message.attachments else 0,
    )

    raw_text = message.text or ""

    # VK кодирует беседы offset'ом 2_000_000_000 — это надёжнее, чем peer != from
    is_group_chat = message.peer_id > GROUP_CHAT_PEER_OFFSET

    if is_group_chat:
        if not _MENTION_RE.search(raw_text):
            return  # не упомянули — молчим
        raw_text = _MENTION_RE.sub('', raw_text).strip()

    text = raw_text.lower()

    if is_group_chat and text:
        cmd = _GROUP_CMD_MAP.get(text)
        if cmd == "catalog":
            await _send_catalog(message)
            return
        if cmd == "cart":
            await message.answer(cart_text(message.from_id), keyboard=kb_cart(message.from_id))
            return
        if cmd == "faq":
            await message.answer(
                "❓ Часто задаваемые вопросы:\n\nВыберите тему:",
                keyboard=kb_faq(),
            )
            return
        if cmd == "about":
            await message.answer(COMPANY_INFO, keyboard=kb_main_menu())
            return
        # неизвестная команда в чате — приветствие
        first_name = await _get_first_name(message.from_id)
        await message.answer(
            f"👋 Привет, {first_name}!\n\n"
            "Я бот магазина FITLEX — краски и грунтовки.\n"
            "Напишите мне в личные сообщения для оформления заказа 👇\n"
            "Или используйте команды: Каталог, Корзина, Консультация, О компании",
            keyboard=kb_main_menu(),
        )
        return

    # Уведомление о заказе VK Market (текстом)
    if "заказ успешно оформлен" in text or "номер заказа" in text:
        clean_text = raw_text.replace('\xa0', ' ')
        clean_lower = clean_text.lower()

        order_match = re.search(r'номер заказа\s+(\d+)', clean_lower)
        amount_match = re.search(r'стоимость заказа:\s*([\d\s,.]+)\s*руб', clean_lower)
        delivery_match = re.search(r'стоимость доставки:\s*([\d\s,.]+)\s*руб', clean_lower)
        order_url_match = re.search(r'(https://vk\.com/orders\S+)', clean_text)

        order_num = order_match.group(1) if order_match else "—"

        def parse_amount(match):
            if not match:
                return 0
            raw = match.group(1).replace(' ', '').replace(',', '').replace('.', '')
            return int(raw) if raw.isdigit() else 0

        total = parse_amount(amount_match)
        delivery = parse_amount(delivery_match)
        order_url = order_url_match.group(1) if order_url_match else ""

        buyer_id = None
        if order_url:
            buyer_match = re.search(r'/orders(\d+)_', order_url)
            if buyer_match:
                buyer_id = int(buyer_match.group(1))

        if buyer_id:
            reply_peer = buyer_id
        elif message.from_id > 0:
            reply_peer = message.from_id
        else:
            reply_peer = message.peer_id

        logger.info(
            "Заказ VK №%s: сумма=%s, доставка=%s, from_id=%s, peer_id=%s, buyer=%s, reply_to=%s",
            order_num, total, delivery, message.from_id, message.peer_id, buyer_id, reply_peer,
        )

        kb = Keyboard(inline=True)
        if order_url:
            kb.add(OpenLink(order_url, label="💳 Оплатить через VK Pay"))
            kb.row()
        full_amount = total + delivery if delivery > 0 else total
        if full_amount > 0:
            kb.add(Callback(
                "💳 Оплатить через ЮКасса",
                payload={"c": "pay_order", "amount": full_amount, "order": order_num},
            ))

        msg_text = f"✅ Заказ №{order_num} оформлен!\n\n💰 Сумма товаров: {total} ₽\n"
        if delivery > 0:
            msg_text += f"🚚 Доставка: {delivery} ₽\n💵 Итого: {total + delivery} ₽\n"
        msg_text += "\nВыберите способ оплаты:"

        await _safe_send(peer_id=reply_peer, message=msg_text, keyboard=kb.get_json())
        return

    # Игнорируем сообщения от сообщества (системные)
    if message.from_id <= 0:
        return

    # Системные уведомления о статусе заказа
    skip_phrases = ["заказ отменён", "заказ доставлен", "статус заказа"]
    if any(phrase in text for phrase in skip_phrases):
        return

    # Шаблон «Меня заинтересовал данный товар»
    if "заинтересовал" in text:
        matched = None

        # 1) Market-вложение
        if message.attachments:
            for att in message.attachments:
                market = getattr(att, "market", None)
                if not market:
                    continue
                market_title = (market.title or "").lower()
                market_price = getattr(getattr(market, "price", None), "amount", None)
                logger.info("Market attachment: title=%s, price=%s", market.title, market_price)

                if market_price:
                    price_rub = int(market_price) // 100
                    for p in CATALOG:
                        if p["price"] == price_rub:
                            matched = p
                            break

                if not matched and market_title:
                    for p in CATALOG:
                        if p["name"].lower() in market_title or market_title in p["name"].lower():
                            matched = p
                            break

                if matched:
                    break

        # 2) Поиск в тексте
        if not matched:
            for p in CATALOG:
                if p["name"].lower() in text:
                    matched = p
                    break
            if not matched:
                for p in CATALOG:
                    keywords = [w for w in p["name"].lower().split() if len(w) > 3]
                    hits = sum(1 for kw in keywords if kw in text)
                    if hits >= 2:
                        matched = p
                        break

        if matched:
            logger.info("Запрос товара из карточки: %s, user=%s", matched["name"], message.from_id)
            await message.answer(
                f"📋 {matched['name']}\n"
                f"💰 {matched['price']} ₽\n\n"
                f"{matched['description']}",
                keyboard=kb_product(matched["id"]),
            )
            return

        logger.info("Запрос товара не распознан, показываем каталог, user=%s", message.from_id)
        lines = ["👋 Вас заинтересовал товар!\n\nВот наш каталог — выберите нужную позицию:\n"]
        for p in CATALOG:
            lines.append(f"• {p['name']} — {p['price']} ₽")
        await message.answer("\n".join(lines), keyboard=kb_catalog())
        return

    # Приветствие на любое другое сообщение
    first_name = await _get_first_name(message.from_id)
    logger.info("Приветствие для %s (id%s)", first_name, message.from_id)
    await message.answer(
        f"👋 Привет, {first_name}!\n\n"
        "Я бот магазина FITLEX — краски и грунтовки.\n"
        "Выбери, что тебя интересует 👇",
        keyboard=kb_main_menu(),
    )


# ═══════════════════════════════════════════════════════════════
#  STARTUP: возобновление polling'а недооплаченных платежей
# ═══════════════════════════════════════════════════════════════


async def _resume_pending_payments() -> None:
    if not pending_payments:
        return
    logger.info("Возобновляем %d pending платежей", len(pending_payments))
    for payment_id, user_id in list(pending_payments.items()):
        _spawn(poll_payment_status(payment_id, user_id))


bot.loop_wrapper.on_startup.append(_resume_pending_payments())


# ═══════════════════════════════════════════════════════════════
#  ЗАПУСК
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Бот FITLEX запускается...")
    bot.run_forever()
