import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.ext import ContextTypes, ConversationHandler

from auth.sync_job import sync_perms_from_ad
from commands.common_user import disableuser, listusers, unlockuser
from commands.laps import laps
from commands.newuser import CHOOSING_GROUP, TYPING_FULL_NAME, cancel, newuser, group_chosen, full_name_received
from commands.resetpass import resetpass
from commands.vpn import vpnenable, vpndisable
from common.config import settings

logging.root.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

async def unknown(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Неизвестная команда. Ваш ID: {update.effective_user.id}")

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш ID: {update.effective_user.id}")


def main():
    logging.info("BOT STARTING")
    if not settings.bot_token:
        raise ValueError("Не указан TOKEN в переменных окружения")

    application = Application.builder().token(settings.bot_token).build()

    # Регистрируем ConversationHandler для newuser
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('newuser', newuser)],
        states={
            CHOOSING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_chosen)],
            TYPING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    # Остальные обработчики...
    commands = [
        ("start", start),
        ("laps", laps),
        ("vpnenable", vpnenable),
        ("vpndisable", vpndisable),
        ("disableuser", disableuser),
        ("listusers", listusers),
        ("resetpass", resetpass),
        ("unlockuser", unlockuser),
    ]

    for cmd, handler in commands:
        application.add_handler(CommandHandler(cmd, handler))

    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Добавляем задачу синхронизации
    application.job_queue.run_repeating(
        sync_perms_from_ad,
        interval=settings.group_perms_sync_interval_seconds,  # Каждый час
        first=1,
    )

    application.run_polling()


if __name__ == "__main__":
    main()