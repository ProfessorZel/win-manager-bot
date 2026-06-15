import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.request import HTTPXRequest

from auth.sync_job import sync_perms_from_ad
from commands.common_user import disableuser, listusers, unlockuser
from commands.laps import laps
from commands.newuser import CHOOSING_GROUP, TYPING_FULL_NAME, cancel, newuser, group_chosen, full_name_received
from commands.resetpass import resetpass
from commands.vpn import vpnenable, vpndisable
from commands.wol import wolpc
from commands.setmac import setmac
from commands.lock_user import newlockuser, lock_user_name_received, cancel_lock_user, TYPING_LOCK_USER_NAME
from operations.sync_macs import sync_macs_job
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

    builder = Application.builder().token(settings.bot_token)
    if settings.proxy_url:
        proxy_request = HTTPXRequest(proxy=settings.proxy_url)
        builder = builder.request(proxy_request).get_updates_request(proxy_request)
    application = builder.build()

    # Фильтр исключающий чат поддержки — туда команды не обрабатываем
    not_support = (
        ~filters.Chat(chat_id=settings.support_chat_id)
        if settings.support_chat_id else filters.ALL
    )

    # Регистрируем ConversationHandler для newuser
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('newuser', newuser, filters=not_support)],
        states={
            CHOOSING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_chosen)],
            TYPING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel, filters=not_support)]
    )
    application.add_handler(conv_handler)

    lock_user_handler = ConversationHandler(
        entry_points=[CommandHandler('newlockuser', newlockuser, filters=not_support)],
        states={
            TYPING_LOCK_USER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lock_user_name_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel_lock_user, filters=not_support)]
    )
    application.add_handler(lock_user_handler)

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
        ("wol", wolpc),
        ("setmac", setmac),
    ]

    for cmd, handler in commands:
        application.add_handler(CommandHandler(cmd, handler, filters=not_support))

    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND & not_support, unknown))

    # Добавляем задачу синхронизации
    application.job_queue.run_repeating(
        sync_perms_from_ad,
        interval=settings.group_perms_sync_interval_seconds,
        first=1,
    )

    application.job_queue.run_repeating(
        sync_macs_job,
        interval=settings.mac_sync_interval_seconds,
        first=60,
    )

    application.run_polling()


if __name__ == "__main__":
    main()