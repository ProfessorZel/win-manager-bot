import logging

from telegram import Update, helpers
from telegram.constants import (
    ParseMode
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from auth.perms_storage import check_perms
from auth.sync_job import sync_perms_from_ad
from operations import ldap_pass, list_users, create_user, add_group, disable_user, remove_group
from common.config import settings

logging.root.setLevel(logging.INFO)

async def laps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "laps"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя компьюетра: /laps PC1")
        return
    pc_name = context.args[0]

    laps_info = ldap_pass.get_computer_laps_password(pc_name)
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


async def vpnenable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "vpnenable"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text(f"⚠️ Неверный формат, необходимо передать имя пользователя: /vpnenable IvanovVP")
        return

    login = context.args[0]
    result = add_group.add_user_to_group(login, settings.vpn_access_group)
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
    result = remove_group.remove_user_from_group(login, settings.vpn_access_group)
    await update.message.reply_text(("✅ Отозван доступ к VPN." if result["success"] else "❌ Произошла ошибка") + "\n" +
                                    result["message"])


async def newuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "newuser"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Неверный формат, Использование: /newuser <role> <ФИО>")
        return

    group, *full_name = context.args
    result = create_user.create_user(' '.join(full_name), group)


    if result['success']:
        await update.message.reply_text(
            helpers.escape_markdown("✅ Добро пожаловать в домен.\n", 2) +
            helpers.escape_markdown("Логин: ", 2) + "`" + helpers.escape_markdown(result['login'], 2) + "`\n" +
            helpers.escape_markdown("Временный пароль: ", 2) + "||" + helpers.escape_markdown(result['temp_pass'], 2) + "||\n" +
            helpers.escape_markdown(f"Подразделение: {result['ou']}\n", 2) +
            helpers.escape_markdown(f"Группы: {','.join(result['groups_added'])}", 2),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        await update.message.reply_text(f"Статус создания: {result["message"]}")
    else:
        await update.message.reply_text(f"❌ Произошла ошибка: {result["message"]}")



async def blockuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def resetpassword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, "resetpassword"):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Неверный формат, Использование: /resetpass IvanovVP")
        return

    login = context.args[0]
    result = disable_user.disable_user(login)
    await update.message.reply_text(
        ("✅ Успешно отключен." if result["success"] else "❌ Произошла ошибка") + "\n" +
        result["message"])

async def unknown(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Неизвестная команда. Ваш ID: {update.effective_user.id}")

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш ID: {update.effective_user.id}")


def main():
    # Проверка наличия обязательных переменных окружения
    if not settings.bot_token:
        raise ValueError("Не указан TOKEN в переменных окружения")
    if not settings.admin_ids:
        raise ValueError("Не указаны ADMINS в переменных окружения")

    application = Application.builder().token(settings.bot_token).build()

    #application.create_task()

    # Регистрация обработчиков команд
    commands = [
        ("start", start),
        ("laps", laps),
        ("vpnenable", vpnenable),
        ("vpndisable", vpndisable),
        ("newuser", newuser),
        ("blockuser", blockuser),
        ("listusers", listusers),
        ("resetpass", resetpassword)
    ]

    for cmd, handler in commands:
        application.add_handler(CommandHandler(cmd, handler))

    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # # Инициализация JobQueue
    # job_queue = application.job_queue
    # if job_queue is None:
    #     job_queue = JobQueue()
    #     job_queue.set_application(application)
    #     application.job_queue = job_queue

    # Добавляем задачу синхронизации
    if hasattr(settings, 'group_perm_mapping') and settings.group_perm_mapping:
        application.job_queue.run_repeating(
            sync_perms_from_ad,
            interval=3600,  # Каждый час
            first=1  # Первый запуск через 10 сек
        )

    logging.info(f"Бот запущен. ID администраторов: {settings.admin_ids}")
    application.run_polling()


if __name__ == "__main__":
    main()