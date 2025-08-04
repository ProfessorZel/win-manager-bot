import json
import os

import ldap3
from ldap3 import Connection
from ldap3.core.exceptions import LDAPException

from common import ldap
from common.ldap import get_connection

ad_bind_user = os.getenv("AD_BIND_USER")
ad_bind_pass = os.getenv("AD_BIND_PASSWORD")
domain = os.getenv("DOMAIN")
base_dn = os.getenv("BASE_DN")
user_search_base = os.getenv("USER_SEARCH_BASE")
group_search_base = os.getenv("GROUP_SEARCH_BASE")
user_group_mapping = json.loads(os.getenv("USER_GROUP_MAPPING"))
user_ou_mapping = json.loads(os.getenv("USER_OU_MAPPING"))
mail_domain = os.getenv("MAIL_DOMAIN")
temp_password = os.getenv("NEW_USER_TEMP_PASS")

def get_users_by_ou() -> dict:
    """
    Возвращает словарь с пользователями, сгруппированными по подразделениям (OU)

    :param server: Сервер LDAP
    :return: Словарь вида {ou_path: [{'sAMAccountName': ..., 'displayName': ...}, ...]}
    """
    result = {
        'success': False,
        'message': '',
        'users_by_ou': {}
    }

    try:
        # Получаем уникальные OU из маппинга
        unique_ous = set(user_ou_mapping.values())

        # Инициализируем структуру для результатов
        result['users_by_ou'] = {ou: [] for ou in unique_ous}

        conn = get_connection()
        for ou_path in unique_ous:
            search_base = f"{ou_path},{base_dn}"

            # Ищем всех пользователей в текущем OU
            conn.search(
                search_base=search_base,
                search_filter="(&(objectClass=user)(objectCategory=person))",
                attributes=['sAMAccountName', 'displayName'],
                search_scope=ldap3.LEVEL,
            )

            for entry in conn.entries:
                user_info = {
                    'sAMAccountName': entry.sAMAccountName.value if 'sAMAccountName' in entry else None,
                    'displayName': entry.displayName.value if 'displayName' in entry else None
                }
                result['users_by_ou'][ou_path].append(user_info)

        result['success'] = True
        result['message'] = f"Найдено пользователей: {sum(len(users) for users in result['users_by_ou'].values())}"

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result