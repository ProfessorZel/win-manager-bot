# Добавляем состояния для ConversationHandler
from telegram import helpers, ReplyKeyboardRemove, Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, ContextTypes

from auth.perms_storage import check_perms, Permissions
from common.config import settings
from operations import create_user

CHOOSING_GROUP = "newuser.1"
TYPING_FULL_NAME = "newuser.2"

async def newuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_perms(update.effective_user.id, Permissions.NEWUSER):
        await update.message.reply_text(f"⚠️ Требуются права администратора. Ваш ID: {update.effective_user.id}")
        return ConversationHandler.END

    # Если есть аргументы - работаем в старом режиме
    if context.args:
        if len(context.args) < 2:
            await update.message.reply_text("⚠️ Неверный формат, Использование: /newuser <role> <ФИО>")
            return ConversationHandler.END

        group, *full_name = context.args

        # Проверяем существование группы
        if group not in settings.user_ou_mapping.keys():
            await update.message.reply_text(
                f"❌ Группа '{group}' не найдена. Доступные группы: {', '.join(settings.user_ou_mapping.keys())}")
            return ConversationHandler.END

        result = create_user.create_user(' '.join(full_name), group)

        if result['success']:
            await update.message.reply_text(
                helpers.escape_markdown("✅ Добро пожаловать в домен.\n", 2) +
                helpers.escape_markdown("Логин: ", 2) + "`" + helpers.escape_markdown(result['login'], 2) + "`\n" +
                helpers.escape_markdown("Временный пароль: ", 2) + "||" + helpers.escape_markdown(result['temp_pass'],
                                                                                                  2) + "||\n" +
                helpers.escape_markdown(f"Подразделение: {result['ou']}\n", 2) +
                helpers.escape_markdown(f"Группы: {','.join(result['groups_added'])}", 2),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text(f"❌ Произошла ошибка: {result['message']}")
        return ConversationHandler.END

    # Если аргументов нет - показываем кнопки с группами
    groups = list(settings.user_ou_mapping.keys())
    # Добавляем кнопку отмены
    keyboard = [groups[i:i + 2] for i in range(0, len(groups), 2)]  # Разбиваем на ряды по 2 кнопки
    keyboard.append(["❌ Отмена"])  # Добавляем кнопку отмены

    await update.message.reply_text(
        "Выберите группу:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_GROUP


async def group_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Проверяем, не нажата ли кнопка отмены
    if user_input == "❌ Отмена":
        await update.message.reply_text(
            "Создание пользователя отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    # Проверяем существование группы
    if user_input not in settings.user_ou_mapping.keys():
        # Показываем сообщение об ошибке и снова отображаем клавиатуру
        groups = list(settings.user_ou_mapping.keys())
        keyboard = [groups[i:i + 2] for i in range(0, len(groups), 2)]
        keyboard.append(["❌ Отмена"])

        await update.message.reply_text(
            f"❌ Группа '{user_input}' не найдена. Пожалуйста, выберите одну из доступных групп:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_GROUP

    context.user_data['group'] = user_input

    # Создаем клавиатуру для ввода ФИО с кнопкой отмены
    cancel_keyboard = [["❌ Отмена"]]

    await update.message.reply_text(
        "Теперь введите ФИО нового пользователя:",
        reply_markup=ReplyKeyboardMarkup(cancel_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TYPING_FULL_NAME


async def full_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Проверяем, не нажата ли кнопка отмены
    if user_input == "❌ Отмена":
        await update.message.reply_text(
            "Создание пользователя отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    full_name = user_input
    group = context.user_data['group']

    result = create_user.create_user(full_name, group)

    if result['success']:
        await update.message.reply_text(
            helpers.escape_markdown("✅ Добро пожаловать в домен.\n", 2) +
            helpers.escape_markdown("Логин: ", 2) + "`" + helpers.escape_markdown(result['login'], 2) + "`\n" +
            helpers.escape_markdown("Временный пароль: ", 2) + "||" + helpers.escape_markdown(result['temp_pass'],
                                                                                              2) + "||\n" +
            helpers.escape_markdown(f"Подразделение: {result['ou']}\n", 2) +
            helpers.escape_markdown(f"Группы: {','.join(result['groups_added'])}", 2),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            f"❌ Произошла ошибка: {result['message']}",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Создание пользователя отменено",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END