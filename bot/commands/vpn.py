from telegram import Update
from telegram.ext import ContextTypes

from auth.perms_storage import check_perms
from common.config import settings
from operations.add_group import add_user_to_group
from operations.remove_group import remove_user_from_group


async def vpnenable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "vpnenable"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя пользователя: /vpnenable IvanovVP")
        return

    login = context.args[0]
    result = add_user_to_group(login, settings.vpn_access_group)
    await update.message.reply_text(("✅ Открыт доступ к VPN." if result["success"] else "❌ Произошла ошибка")+"\n"+
                                       result["message"])


async def vpndisable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "vpndisable"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя пользователя: /vpndisable IvanovVP")
        return

    login = context.args[0]
    result = remove_user_from_group(login, settings.vpn_access_group)
    await update.message.reply_text(("✅ Отозван доступ к VPN." if result["success"] else "❌ Произошла ошибка") + "\n" +
                                    result["message"])
