import logging

import ldap3
from ldap3.core.exceptions import LDAPException
from datetime import datetime, timezone

from common.config import settings
from common.ldap import get_connection


def get_users_by_ou() -> dict:
    """
    Возвращает словарь с пользователями, сгруппированными по подразделениям (OU)

    :return: Словарь вида {ou_path: [{'sAMAccountName': ..., 'displayName': ...,
              'lastLogonTimestamp': ..., 'whenCreated': ...}, ...]}
    """
    result = {
        'success': False,
        'message': '',
        'users_by_ou': {}
    }

    try:
        conn = get_connection()
        for name, ou_path in dict(settings.user_ou_mapping).items():
            search_base = f"{ou_path},{settings.base_dn}"
            result['users_by_ou'][name] = []
            # Ищем всех пользователей в текущем OU
            conn.search(
                search_base=search_base,
                search_filter="(&(objectClass=user)(objectCategory=person))",
                attributes=['sAMAccountName', 'displayName', 'lastLogonTimestamp', 'whenCreated'],
                search_scope=ldap3.LEVEL,
            )

            for entry in conn.entries:
                # Преобразование lastLogonTimestamp в datetime
                last_logon_timestamp = None
                if 'lastLogonTimestamp' in entry and entry.lastLogonTimestamp.value not in (None, 0):
                    last_logon_timestamp = entry.lastLogonTimestamp.value

                # Преобразование whenCreated в datetime
                account_created = None
                if 'whenCreated' in entry and entry.whenCreated.value not in (None, ""):
                    account_created = entry.whenCreated.value

                user_info = {
                    'sAMAccountName': entry.sAMAccountName.value if 'sAMAccountName' in entry else None,
                    'displayName': entry.displayName.value if 'displayName' in entry else None,
                    'lastLogonTimestamp': last_logon_timestamp,
                    'whenCreated': account_created
                }
                result['users_by_ou'][name].append(user_info)

        result['success'] = True
        result['message'] = f"Найдено пользователей: {sum(len(users) for users in result['users_by_ou'].values())}"

    except LDAPException as e:
        logging.error(e, exc_info=True)
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        logging.error(e, exc_info=True)
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result