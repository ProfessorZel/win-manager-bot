import logging

from telegram.ext import ContextTypes

from common.config import settings
from auth.perms_storage import get_user, clear_all_users
from operations.get_group_members import get_group_members


async def sync_perms_from_ad(context: ContextTypes.DEFAULT_TYPE):
    """Задача синхронизации прав из AD групп"""
    logging.info("Starting AD permissions sync.")

    # Собираем все полномочия из маппинга
    clear_all_users()
    for group_dn, perms in settings.group_perm_mapping.items():
        try:
            # Получаем пользователей группы
            members = get_group_members(group_dn,
                                        ['pager', 'sAMAccountName', 'userAccountControl'],
                                        actve_only=True)
            # Собираем полномочия по Telegram ID
            for user in members:
                if 'pager' in user and user.pager.value:
                    try:
                        tg_id = int(user.pager.value)
                        user_obj = get_user(tg_id)
                        user_obj.add_perms(perms)
                        user_obj.set_login(user.sAMAccountName.value)
                        logging.info(f"Synced {tg_id} ({user.sAMAccountName}) with perms {','.join(perms)}")
                    except (ValueError, TypeError):
                        logging.warn(f"Invalid Telegram ID for {user.sAMAccountName}: {user.pager}")
                else:
                    logging.info(f"Skipped ({user.sAMAccountName}) no pager value")
        except Exception as e:
            logging.warn(f"Error processing group {group_dn}: {str(e)}")

    logging.info(f"Permissions synced")