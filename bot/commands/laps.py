from telegram import Update, helpers
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from auth.perms_storage import check_perms
from operations.laps_pass import get_computer_laps_password


async def laps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "laps"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя компьюетра: /laps PC1")
        return
    pc_name = context.args[0]

    laps_info = get_computer_laps_password(pc_name)
    if laps_info['success']:
        await update.message.reply_text(f"✅ `{pc_name}`\n" +
                                        f"Логин: `"+helpers.escape_markdown(f"{pc_name}\\loc.admin", 2)+"`\n" +
                                        f"Пароль: ||{helpers.escape_markdown(laps_info['laps_password'], 2)}||\n"+
            f"Срок действия: {helpers.escape_markdown(laps_info['laps_expiry'], 2)} {helpers.escape_markdown(laps_info['laps_expiry_status'], 2)}\n"+
            (f"ОС: {helpers.escape_markdown(laps_info['os'], 2)}"  if 'os' in laps_info else "")+
            (f"LastLogon: {helpers.escape_markdown(laps_info['last_logon'], 2)}"  if 'last_logon' in laps_info else ""),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(f"❌ Произошла ошибка: {laps_info['message']}")

