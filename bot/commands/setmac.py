import re

from telegram import Update
from telegram.ext import ContextTypes

from auth.perms_storage import check_perms, Permissions
from operations.set_pc_mac import set_computer_mac

MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$')


async def setmac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, Permissions.WOLPCEXEC):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Формат: /setmac PC1 AA:BB:CC:DD:EE:FF")
        return

    pc_name, mac = context.args

    if not MAC_PATTERN.match(mac):
        await update.message.reply_text("⚠️ Неверный формат MAC-адреса. Используйте AA:BB:CC:DD:EE:FF")
        return

    result = set_computer_mac(pc_name, mac)
    await update.message.reply_text(("✅ " if result['success'] else "❌ ") + result['message'])
