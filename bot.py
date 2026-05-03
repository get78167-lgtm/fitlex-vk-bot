"""
VK Bot для сообщества FITLEX — «Краски и грунтовки оптом и в розницу»

Функции: каталог товаров, корзина, оплата ЮКасса, FAQ, информация о компании.
"""

import asyncio
import json
import logging
import os
import uuid

from vkbottle import (
    Keyboard,
    KeyboardButtonColor,
    Text,
    Callback,
    GroupEventType,
    GroupTypes,
)
from vkbottle.bot import Bot, Message
from yookassa import Configuration, Payment

# ═══════════════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

VK_TOKEN = os.getenv("VK_TOKEN", "")

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

if not VK_TOKEN or not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
    raise RuntimeError(
        "Не заданы переменные окружения! Укажите VK_TOKEN, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY.\n"
        "См. файл .env.example"
    )

GROUP_ID = 215128871
PAYMENT_CURRENCY = "RUB"
POLL_INTERVAL_SEC = 5
POLL_MAX_ATTEMPTS = 60

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
#  КОРЗИНА (in-memory)
# ═══════════════════════════════════════════════════════════════

# {user_id: {product_id: quantity}}
user_carts: dict[int, dict[int, int]] = {}
# {payment_id: user_id}
pending_payments: dict[str, int] = {}


def get_cart(user_id: int) -> dict[int, int]:
    return user_carts.setdefault(user_id, {})


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
#  КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════════════


def kb_main_menu() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("🛒 Каталог"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("📦 Корзина"), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("❓ Консультация"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("ℹ️ О компании"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def kb_catalog() -> str:
    kb = Keyboard(inline=True)
    for p in CATALOG:
        # VK limit: button label ≤ 40 chars
        short = p["name"].replace("Грунтовка ", "").replace("глубокого проникновения", "глуб. проник.")
        label = f"{short} — {p['price']}₽"
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
            short = p["name"].replace("Грунтовка ", "").replace("глубокого проникновения", "глуб. проник.")
            kb.add(Callback(f"❌ {short}"[:40], payload={"c": "rm", "id": pid}))
            kb.row()
        kb.add(Callback("💳 Оплатить", payload={"c": "pay"}), color=KeyboardButtonColor.POSITIVE)
        kb.add(Callback("🗑 Очистить", payload={"c": "clr"}), color=KeyboardButtonColor.NEGATIVE)
    else:
        kb.add(Callback("🛒 Каталог", payload={"c": "cat"}), color=KeyboardButtonColor.PRIMARY)
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
#  ОПЛАТА ЮКасса
# ═══════════════════════════════════════════════════════════════


def create_payment(user_id: int) -> Payment | None:
    amount = cart_total(user_id)
    if amount <= 0:
        return None
    cart = get_cart(user_id)
    items = [f"{CATALOG_BY_ID[pid]['name']} ×{qty}" for pid, qty in cart.items()]
    description = "FITLEX: " + ", ".join(items)
    if len(description) > 128:
        description = description[:125] + "..."
    try:
        # Формируем чек (54-ФЗ)
        receipt_items = []
        for pid, qty in cart.items():
            p = CATALOG_BY_ID[pid]
            receipt_items.append({
                "description": p["name"][:128],
                "quantity": str(qty),
                "amount": {
                    "value": f"{p['price']}.00",
                    "currency": PAYMENT_CURRENCY,
                },
                "vat_code": 1,
                "payment_subject": "commodity",
                "payment_mode": "full_payment",
            })

        payment = Payment.create(
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


async def poll_payment_status(payment_id: str, user_id: int) -> None:
    logger.info("Отслеживание платежа %s для user=%s", payment_id, user_id)
    for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
        await asyncio.sleep(POLL_INTERVAL_SEC)
        try:
            payment = Payment.find_one(payment_id)
        except Exception as exc:
            logger.warning("Ошибка проверки %s (попытка %d): %s", payment_id, attempt, exc)
            continue

        if payment.status == "succeeded":
            logger.info("Платёж %s успешен!", payment_id)
            user_carts.pop(user_id, None)
            await bot.api.messages.send(
                user_id=user_id, random_id=0,
                message=(
                    f"✅ Оплата прошла успешно!\n\n"
                    f"💰 Сумма: {payment.amount.value} ₽\n"
                    f"🆔 Платёж: {payment_id}\n\n"
                    "Спасибо за покупку! Мы свяжемся с вами для уточнения доставки."
                ),
                keyboard=kb_main_menu(),
            )
            pending_payments.pop(payment_id, None)
            return

        if payment.status == "canceled":
            logger.info("Платёж %s отменён.", payment_id)
            await bot.api.messages.send(
                user_id=user_id, random_id=0,
                message="❌ Платёж отменён. Ваша корзина сохранена — попробуйте снова.",
                keyboard=kb_main_menu(),
            )
            pending_payments.pop(payment_id, None)
            return

    logger.warning("Таймаут для платежа %s", payment_id)
    await bot.api.messages.send(
        user_id=user_id, random_id=0,
        message="⏳ Время ожидания оплаты истекло. Корзина сохранена.",
        keyboard=kb_main_menu(),
    )
    pending_payments.pop(payment_id, None)


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

    # Acknowledge the callback (dismiss loading spinner)
    snackbar = None

    if cmd == "d" and pid:
        # Product detail
        product = CATALOG_BY_ID.get(pid)
        if product:
            await bot.api.messages.send(
                user_id=user_id, random_id=0,
                message=f"📋 {product['name']}\n💰 {product['price']} ₽\n\n{product['description']}",
                keyboard=kb_product(pid),
            )

    elif cmd == "a" and pid:
        # Add to cart
        cart = get_cart(user_id)
        cart[pid] = cart.get(pid, 0) + 1
        product = CATALOG_BY_ID.get(pid)
        snackbar = f"✅ {product['name']} добавлен в корзину"
        logger.info("user=%s добавил товар %s в корзину", user_id, pid)

    elif cmd == "rm" and pid:
        # Remove from cart
        cart = get_cart(user_id)
        cart.pop(pid, None)
        snackbar = "🗑 Товар удалён из корзины"
        await bot.api.messages.send(
            user_id=user_id, random_id=0,
            message=cart_text(user_id),
            keyboard=kb_cart(user_id),
        )

    elif cmd == "clr":
        # Clear cart
        user_carts.pop(user_id, None)
        snackbar = "🗑 Корзина очищена"
        await bot.api.messages.send(
            user_id=user_id, random_id=0,
            message="🛒 Корзина очищена.",
            keyboard=kb_main_menu(),
        )

    elif cmd == "cat":
        # Show catalog
        lines = ["📦 Каталог товаров FITLEX:\n"]
        for p in CATALOG:
            lines.append(f"• {p['name']} — {p['price']} ₽")
        lines.append("\nНажмите на товар для подробностей:")
        await bot.api.messages.send(
            user_id=user_id, random_id=0,
            message="\n".join(lines),
            keyboard=kb_catalog(),
        )

    elif cmd == "pay":
        # Create payment
        total = cart_total(user_id)
        if total < 2000:
            snackbar = f"⚠️ Минимальный заказ 2 000 ₽ (сейчас {total} ₽)"
        else:
            payment = create_payment(user_id)
            if payment:
                url = payment.confirmation.confirmation_url
                pending_payments[payment.id] = user_id
                await bot.api.messages.send(
                    user_id=user_id, random_id=0,
                    message=(
                        f"💳 Ссылка для оплаты:\n{url}\n\n"
                        f"💰 Сумма: {total} ₽\n"
                        "После оплаты я пришлю подтверждение."
                    ),
                )
                asyncio.create_task(poll_payment_status(payment.id, user_id))
            else:
                snackbar = "⚠️ Ошибка создания платежа"

    elif cmd == "faq" and pid:
        answer = FAQ_ITEMS.get(pid, "Информация не найдена.")
        await bot.api.messages.send(
            user_id=user_id, random_id=0,
            message=answer,
            keyboard=kb_faq(),
        )

    # Send callback answer (dismiss loading spinner)
    try:
        if snackbar:
            event_data = json.dumps({"type": "show_snackbar", "text": snackbar[:90]})
        else:
            event_data = json.dumps({"type": "show_snackbar", "text": "✅"})
        await bot.api.messages.send_message_event_answer(
            event_id=event_id, user_id=user_id, peer_id=peer_id,
            event_data=event_data,
        )
    except Exception as exc:
        logger.warning("Ошибка ответа на callback: %s", exc)


# ═══════════════════════════════════════════════════════════════
#  ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# ═══════════════════════════════════════════════════════════════


@bot.on.message(text=["Каталог", "🛒 Каталог", "каталог", "товары"])
async def handle_catalog(message: Message):
    logger.info("Каталог запрошен user=%s", message.from_id)
    lines = ["📦 Каталог товаров FITLEX:\n"]
    for p in CATALOG:
        lines.append(f"• {p['name']} — {p['price']} ₽")
    lines.append("\nНажмите на товар для подробностей:")
    await message.answer("\n".join(lines), keyboard=kb_catalog())


@bot.on.message(text=["Корзина", "📦 Корзина", "корзина"])
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


@bot.on.message()
async def handle_any(message: Message):
    text = message.text.lower()

    # Обработка шаблонного сообщения «Меня заинтересовал данный товар»
    # (отправляется VK, когда покупатель нажимает «Написать» в карточке товара)
    if "заинтересовал" in text:
        matched = None

        # 1) Ищем market-вложение (VK отправляет товар как attachment)
        if hasattr(message, "attachments") and message.attachments:
            for att in message.attachments:
                if hasattr(att, "market") and att.market:
                    market_title = att.market.title.lower()
                    market_price = getattr(att.market.price, "amount", None)
                    logger.info("Market attachment: title=%s, price=%s", att.market.title, market_price)

                    # Приоритет 1: по цене (уникальна для каждого товара)
                    if market_price:
                        price_rub = int(market_price) // 100
                        for p in CATALOG:
                            if p["price"] == price_rub:
                                matched = p
                                break

                    # Приоритет 2: по точному вхождению названия
                    if not matched:
                        for p in CATALOG:
                            if p["name"].lower() in market_title or market_title in p["name"].lower():
                                matched = p
                                break

        # 2) Если вложений нет — ищем в тексте
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
        else:
            # Товар не найден — показываем каталог
            logger.info("Запрос товара не распознан, показываем каталог, user=%s", message.from_id)
            lines = ["👋 Вас заинтересовал товар!\n\nВот наш каталог — выберите нужную позицию:\n"]
            for p in CATALOG:
                lines.append(f"• {p['name']} — {p['price']} ₽")
            await message.answer("\n".join(lines), keyboard=kb_catalog())
            return

    # Приветствие на любое другое сообщение
    user_info = await bot.api.users.get(user_ids=[message.from_id])
    first_name = user_info[0].first_name if user_info else "друг"
    logger.info("Приветствие для %s (id%s)", first_name, message.from_id)
    await message.answer(
        f"👋 Привет, {first_name}!\n\n"
        "Я бот магазина FITLEX — краски и грунтовки.\n"
        "Выбери, что тебя интересует 👇",
        keyboard=kb_main_menu(),
    )


# ═══════════════════════════════════════════════════════════════
#  ЗАПУСК
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Бот FITLEX запускается...")
    bot.run_forever()
