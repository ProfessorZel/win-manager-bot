from ldap3 import MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException

from common.config import settings
from common.ldap import get_connection


def unlock_user(username: str) -> dict:
    """
    Разблокирует учетную запись пользователя, сбрасывая флаг блокировки

    :param username: Логин пользователя (sAMAccountName)
    :return: Результат операции
    """
    result = {
        'success': False,
        'message': '',
        'user_dn': None,
        'unlocked': False
    }

    try:
        conn = get_connection()

        # Поиск пользователя по логину
        search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        conn.search(
            search_base=f"{settings.user_search_base}",
            search_filter=search_filter,
            attributes=['lockoutTime', 'distinguishedName']
        )

        if not conn.entries:
            result['message'] = f"Пользователь с логином '{username}' не найден"
            return result

        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn
        result['user_dn'] = user_dn

        # Сбрасываем флаг блокировки (устанавливаем lockoutTime в 0)
        conn.modify(
            user_dn,
            {'lockoutTime': [(MODIFY_REPLACE, 0)]}
        )

        if conn.result['result'] == 0:
            result['unlocked'] = True
            result['success'] = True
            result['message'] = f"Учетная запись пользователя '{username}' успешно разблокирована"
        else:
            result['message'] = f"Ошибка при разблокировке: {conn.result['description']}"

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result