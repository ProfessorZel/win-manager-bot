import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.ext import ContextTypes, ConversationHandler

from auth.perms_storage import check_perms
from auth.sync_job import sync_perms_from_ad
from commands import laps
from commands.newuser import CHOOSING_GROUP, TYPING_FULL_NAME, cancel, newuser, group_chosen, full_name_received
from commands.resetpass import resetpassword
from commands.vpn import vpnenable, vpndisable
from common.config import settings
from operations import list_users, disable_user
from operations.unlockuser import unlock_user

logging.root.setLevel(logging.INFO)

async def unlockuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "unlockuser"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Неверный формат, Использование: /unlockuser IvanovVP")
        return

    login = context.args[0]
    result = unlock_user(login)  # Предполагается, что функция unlock_user импортирована
    await update.message.reply_text(
        ("✅ Учетная запись успешно разблокирована." if result["success"] else "❌ Произошла ошибка") + "\n" +
        result["message"])

async def disableuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "blockuser"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Неверный формат, Использование: /blockuser IvanovVP")
        return

    login = context.args[0]
    result = disable_user.disable_user(login)
    await update.message.reply_text(
        ("✅ Успешно отключен." if result["success"] else "❌ Произошла ошибка") + "\n" +
        result["message"])


async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "listusers"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    """Команда для отображения пользователей по OU в виде таблицы"""
    result = list_users.get_users_by_ou()

    if not result['success']:
        await update.message.reply_text(f"❌ Ошибка: {result['message']}")
        return

    # Формируем текстовый список
    message = "📋 <b>Список пользователей по подразделениям</b>\n\n"

    for ou, users in result['users_by_ou'].items():
        if not users:
            continue

        # Извлекаем название подразделения
        ou_name = ou.split(',')[0].replace('OU=', '')
        message += f"🏛 <b>{ou_name}</b>:\n"

        # Добавляем пользователей в список
        for i, user in enumerate(users, 1):
            login = user['sAMAccountName'] or "нет логина"
            name = user['displayName'] or "нет имени"
            message += f"{i}. <code>{login}</code> - {name}\n"

        message += "\n"  # Добавляем пустую строку между отделами

    # Отправляем сообщение с пагинацией, если слишком длинное
    max_length = 4000  # Лимит Telegram
    if len(message) > max_length:
        parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        for part in parts:
            await update.message.reply_text(part, parse_mode='HTML')
    else:
        await update.message.reply_text(message, parse_mode='HTML')


async def unknown(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Неизвестная команда. Ваш ID: {update.effective_user.id}")

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш ID: {update.effective_user.id}")


def main():
    logging.warning("BOT STARTING")
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
        ("resetpass", resetpassword),
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