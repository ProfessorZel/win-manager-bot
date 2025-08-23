from telegram import Update
from telegram.ext import ContextTypes

from auth.audit import writeAuditLog
from auth.perms_storage import check_perms, Permissions
from operations import disable_user
from operations.list_users import get_users_by_ou
from operations.unlockuser import unlock_user


async def unlockuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, Permissions.UNLOCKUSER):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        writeAuditLog()
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
    if not check_perms(update.effective_user.id, Permissions.BLOCKUSER):
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
    if not check_perms(update.effective_user.id, Permissions.LISTUSERS):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    """Команда для отображения пользователей по OU в виде таблицы"""
    result = get_users_by_ou()

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