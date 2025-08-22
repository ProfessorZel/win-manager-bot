from telegram import Update, helpers
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from auth.perms_storage import check_perms
from common.config import settings
from operations.change_pass import reset_password

async def resetpassword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "resetpassword"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Неверный формат, Использование: /resetpassword IvanovVP")
        return

    login = context.args[0]

    # Вызываем функцию сброса пароля
    result = reset_password(login)

    # Формируем ответное сообщение
    if result["success"]:
        message = f"✅ Пароль для пользователя '{login}' успешно сброшен\n"
        message += f"🔑 Новый пароль: ||{helpers.escape_markdown(result['new_password'], 2)}||\n"
        message += f"⚠️ Сообщение будет удалено через {settings.remove_new_password_msg_after} секунд"

        # Отправляем сообщение с паролем и устанавливаем таймер удаления
        sent_message = await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

        # Удаляем сообщение с паролем через N секунд
        await context.job_queue.run_once(
            delete_password_message,
            settings.remove_new_password_msg_after,
            data={'chat_id': update.effective_chat.id, 'message_id': sent_message.message_id}
        )
    else:
        message = f"❌ Не удалось сбросить пароль для пользователя '{login}'\n"
        message += f"Причина: {result['message']}"
        await update.message.reply_text(message)


async def delete_password_message(context: ContextTypes.DEFAULT_TYPE):
    """Удаляет сообщение с паролем через заданное время"""
    job_data = context.job.data
    try:
        await context.bot.delete_message(job_data['chat_id'], job_data['message_id'])
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Не удалось удалить сообщение с паролем: {e}")