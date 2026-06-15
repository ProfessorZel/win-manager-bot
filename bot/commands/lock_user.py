from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from auth.perms_storage import check_perms, Permissions
from operations.add_lock_user import create_lock_user

TYPING_LOCK_USER_NAME = 0


async def newlockuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, Permissions.ADMIN):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return ConversationHandler.END
    await update.message.reply_text("Введите ФИО нового пользователя замка:")
    return TYPING_LOCK_USER_NAME


async def lock_user_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    await update.message.reply_text("⏳ Добавляю пользователя...")
    result = await create_lock_user(name)
    if result['success']:
        await update.message.reply_text(
            f"✅ Пользователь добавлен\n\n"
            f"ФИО: {name}\n"
            f"Код для замка: {result['code']}"
        )
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END


async def cancel_lock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END
