
import os
import random
from datetime import datetime
from collections import deque

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
PORT = int(os.getenv("PORT", "10000"))
EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

INITIAL_BALANCE = 10000.0
TRADE_AMOUNT = 1000.0

# أسعار اصطناعية للتدريب فقط
MARKETS = {
    "الذهب": {
        "price": 2000.0,
        "history": deque([2000.0] * 10, maxlen=20),
    },
    "الفضة": {
        "price": 25.0,
        "history": deque([25.0] * 10, maxlen=20),
    },
    "العملات الرقمية": {
        "price": 50000.0,
        "history": deque([50000.0] * 10, maxlen=20),
    },
    "الفوركس": {
        "price": 1.10,
        "history": deque([1.10] * 10, maxlen=20),
    },
}

# محفظة مستقلة لكل مستخدم
ACCOUNTS = {}


def get_account(user_id):
    if user_id not in ACCOUNTS:
        ACCOUNTS[user_id] = {
            "balance": INITIAL_BALANCE,
            "active": False,
            "positions": {},
            "trades": [],
        }

    return ACCOUNTS[user_id]


def record_trade(account, message):
    account["trades"].append(
        datetime.now().strftime("%Y-%m-%d %H:%M")
        + " | "
        + message
    )

    account["trades"] = account["trades"][-50:]


def calculate_equity(account):
    equity = account["balance"]

    for asset, position in account["positions"].items():
        current_price = MARKETS[asset]["price"]
        equity += position["quantity"] * current_price

    return equity


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا بك في Market Bot 📊\n\n"
        "منصة تعليمية لمحاكاة الأسواق.\n\n"
        "الأصول التجريبية:\n"
        "🥇 الذهب\n"
        "🥈 الفضة\n"
        "₿ العملات الرقمية\n"
        "💱 الفوركس\n\n"
        "استخدم /help لمعرفة الأوامر."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أوامر Market Bot:\n\n"
        "/sim_start - بدء المحاكاة التلقائية\n"
        "/sim_stop - إيقاف المحاكاة\n"
        "/wallet - عرض المحفظة\n"
        "/trades - سجل الصفقات\n"
        "/help - المساعدة\n\n"
        "كل العمليات افتراضية وتعليمية فقط."
    )


async def sim_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    account = get_account(user_id)

    account["active"] = True

    await update.message.reply_text(
        "تم تشغيل المحاكاة التلقائية بنجاح! ✅\n\n"
        f"الرصيد الافتراضي: {account['balance']:.2f}\n"
        "سيتم اختبار قواعد المتوسطات المتحركة "
        "على الأسعار الاصطناعية."
    )


async def sim_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    account = get_account(user_id)

    account["active"] = False

    await update.message.reply_text(
        "تم إيقاف المحاكاة. ⏸️\n"
        "يمكنك استئنافها باستخدام /sim_start"
    )


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    account = get_account(user_id)

    equity = calculate_equity(account)

    unrealized = equity - account["balance"]

    await update.message.reply_text(
        "💰 المحفظة الافتراضية\n\n"
        f"الرصيد النقدي: {account['balance']:.2f}\n"
        f"قيمة المحفظة: {equity:.2f}\n"
        f"الربح/الخسارة غير المحققة: {unrealized:.2f}\n"
        f"الصفقات المفتوحة: {len(account['positions'])}\n"
        f"حالة المحاكاة: "
        f"{'تعمل ✅' if account['active'] else 'متوقفة ⏸️'}"
    )


async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    account = get_account(user_id)

    if not account["trades"]:
        await update.message.reply_text(
            "لا توجد صفقات في السجل حتى الآن."
        )
        return

    history = "\n".join(account["trades"][-10:])

    await update.message.reply_text(
        "📋 آخر الصفقات التجريبية:\n\n" + history
    )


async def simulation_tick(context: ContextTypes.DEFAULT_TYPE):
    # تحديث الأسعار الاصطناعية
    for market in MARKETS.values():
        change = random.uniform(-0.012, 0.012)
        market["price"] *= (1 + change)
        market["history"].append(market["price"])

    # تطبيق قواعد المحاكاة على حسابات المستخدمين
    for account in ACCOUNTS.values():
        if not account["active"]:
            continue

        for asset, market in MARKETS.items():
            prices = list(market["history"])

            if len(prices) < 10:
                continue

            fast_average = sum(prices[-5:]) / 5
            slow_average = sum(prices[-10:]) / 10

            position = account["positions"].get(asset)

            # فتح صفقة افتراضية عند تحقق القاعدة التعليمية
            if position is None and fast_average > slow_average:
                if account["balance"] >= TRADE_AMOUNT:
                    price = market["price"]
                    quantity = TRADE_AMOUNT / price

                    account["balance"] -= TRADE_AMOUNT

                    account["positions"][asset] = {
                        "entry": price,
                        "quantity": quantity,
                    }

                    record_trade(
                        account,
                        f"فتح شراء تجريبي: {asset} بسعر {price:.4f}"
                    )

            # إغلاق الصفقة الافتراضية عند تحقق القاعدة العكسية
            elif position is not None and fast_average < slow_average:
                price = market["price"]
                proceeds = position["quantity"] * price
                profit = proceeds - (
                    position["quantity"] * position["entry"]
                )

                account["balance"] += proceeds
                del account["positions"][asset]

                record_trade(
                    account,
                    f"إغلاق تجريبي: {asset} | "
                    f"النتيجة: {profit:+.2f}"
                )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    if not WEBHOOK_SECRET:
        raise RuntimeError("WEBHOOK_SECRET is missing")

    if not EXTERNAL_URL:
        raise RuntimeError("RENDER_EXTERNAL_URL is missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sim_start", sim_start))
    app.add_handler(CommandHandler("sim_stop", sim_stop))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("trades", trades))

    app.job_queue.run_repeating(
        simulation_tick,
        interval=60,
        first=10,
    )

    print("Market Bot simulation is starting...")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=EXTERNAL_URL.rstrip("/") + "/telegram",
        secret_token=WEBHOOK_SECRET,
    )


if __name__ == "__main__":
    main()
