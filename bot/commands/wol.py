from telegram import Update
from telegram.ext import ContextTypes

from auth.perms_storage import check_perms, Permissions
from operations.get_pc_mac import get_computer_mac
from operations.send_magic_packet import send_wake_on_lan_simple


async def wolpc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id,  Permissions.WOLPCEXEC):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя компьюетра: /wol PC1")
        return

    pc_name = context.args[0]
    result = get_computer_mac(pc_name)
    if result['success']:
        result = send_wake_on_lan_simple(result['mac'])
    await update.message.reply_text(("✅ Отправлен WOL." if result["success"] else "❌ Произошла ошибка")+"\n"+
                                       result["message"])
