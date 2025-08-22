import logging

from telegram.ext import ContextTypes

from common.config import settings
from auth.perms_storage import set_perms_to_user, clear_all_perms
from operations.get_group_members import get_group_members


async def sync_perms_from_ad(context: ContextTypes.DEFAULT_TYPE):
    """Задача синхронизации прав из AD групп"""
    logging.info("Starting AD permissions sync.")

    # Собираем все полномочия из маппинга
    all_perms = {}
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
                        if tg_id not in all_perms:
                            all_perms[tg_id] = set()
                        all_perms[tg_id].update(perms)
                        logging.info(f"Synced {tg_id} ({user.sAMAccountName}) with perms {','.join(perms)}")
                    except (ValueError, TypeError):
                        logging.warn(f"Invalid Telegram ID for {user.sAMAccountName}: {user.pager}")
                else:
                    logging.info(f"Skipped ({user.sAMAccountName}) no pager value")
        except Exception as e:
            logging.warn(f"Error processing group {group_dn}: {str(e)}")

    # Обновляем права в хранилище
    clear_all_perms()
    for tg_id, perms_set in all_perms.items():
        set_perms_to_user(tg_id, list(perms_set))

    logging.info(f"Permissions synced for {len(all_perms)} users")