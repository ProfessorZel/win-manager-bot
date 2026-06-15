import logging

from telegram import Update
from telegram.ext import ContextTypes

from auth.perms_storage import check_perms, Permissions
from common.config import settings
from operations.get_pc_mac import get_computer_mac
from operations.send_magic_packet import send_wake_on_lan_simple


async def _is_support_chat_member(bot, user_id: int) -> bool:
    if not settings.support_chat_id:
        return False
    try:
        member = await bot.get_chat_member(chat_id=settings.support_chat_id, user_id=user_id)
        logging.info(f"WOL: user {user_id} status in support chat: {member.status}")
        return member.status in ('member', 'administrator', 'creator', 'restricted')
    except Exception as e:
        logging.warning(f"WOL: get_chat_member failed for {user_id}: {e}")
        return False


async def wolpc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_member = await _is_support_chat_member(context.bot, update.effective_user.id)
    if not is_member and not check_perms(update.effective_user.id, Permissions.WOLPCEXEC):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя компьютера: /wol PC1")
        return

    pc_name = context.args[0]
    result = get_computer_mac(pc_name)
    if result['success']:
        result = send_wake_on_lan_simple(result['mac'])
    await update.message.reply_text(("✅ Отправлен WOL." if result["success"] else "❌ Произошла ошибка")+"\n"+
                                       result["message"])
