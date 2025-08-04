from ldap3 import MODIFY_ADD

from common.config import settings
from common.ldap import get_connection


def add_user_to_group(username: str, group_name: str) -> dict:
    """
    Добавляет пользователя в указанную группу Active Directory.

    Параметры:
        username (str): Логин пользователя (sAMAccountName)
        group_name (str): Название группы (cn)

    Возвращает:
        dict: {
            'success': bool,
            'message': str,
            'user_dn': str,
            'group_dn': str
        }
    """
    result = {
        'success': False,
        'message': '',
        'user_dn': None,
        'group_dn': None
    }

    try:
        # Подключение с аутентификацией
        conn = get_connection()

        # 1. Находим пользователя
        user_search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        conn.search(
            search_base=settings.user_search_base,
            search_filter=user_search_filter,
            attributes=['distinguishedName']
        )

        if not conn.entries:
            result['message'] = f"Пользователь {username} не найден"
            return result

        user_dn = conn.entries[0].entry_dn
        result['user_dn'] = user_dn

        # 2. Находим указанную группу
        group_search_filter = f"(&(objectClass=group)(cn={group_name}))"
        conn.search(
            search_base=settings.group_search_base,
            search_filter=group_search_filter,
            attributes=['member']
        )

        if not conn.entries:
            result['message'] = f"Группа {group_name} не найдена"
            return result

        group_dn = conn.entries[0].entry_dn
        result['group_dn'] = group_dn

        # 3. Проверяем, не состоит ли пользователь уже в группе
        current_members = conn.entries[0].member.values
        if user_dn in current_members:
            result['message'] = f"Пользователь {username} уже состоит в группе {group_name}"
            result['success'] = True  # Технически это успех, так как желаемое состояние достигнуто
            return result

        # 4. Добавляем пользователя в группу
        conn.modify(
            group_dn,
            {'member': [(MODIFY_ADD, [user_dn])]}
        )

        if conn.result['result'] == 0:
            result['success'] = True
            result['message'] = f"Пользователь {username} успешно добавлен в группу {group_name}"
        else:
            result['message'] = f"Ошибка при добавлении в группу: {conn.result['description']}"

    except Exception as e:
        result['message'] = f"Произошла ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result

# Пример использования:
# result = add_user_to_group("ivanov", "VPNUsers")
# if result['success']:
#     print(result['message'])
# else:
#     print(f"Ошибка: {result['message']}")