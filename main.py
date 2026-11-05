
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في Market Bot 📊\n\n"
        "بوت تحليل الأسواق المالية.\n\n"
        "الأسواق التي نعمل على دعمها:\n"
        "🥇 الذهب\n"
        "🥈 الفضة\n"
        "₿ العملات الرقمية\n"
        "💱 الفوركس\n\n"
        "استخدم /help لمعرفة الأوامر."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - تشغيل البوت\n"
        "/help - المساعدة\n"
        "قريباً: أدوات تحليل الأسواق."
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("Market Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
