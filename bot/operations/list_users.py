import ldap3
from ldap3.core.exceptions import LDAPException

from common.config import settings
from common.ldap import get_connection


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
        conn = get_connection()
        for name, ou_path in dict(settings.user_ou_mapping).items():
            search_base = f"{ou_path},{settings.base_dn}"
            result['users_by_ou'][name] = []
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
                result['users_by_ou'][name].append(user_info)

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