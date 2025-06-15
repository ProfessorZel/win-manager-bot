import os
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL, MODIFY_DELETE

# load_dotenv()

ad_bind_user = os.getenv("AD_BIND_USER")
ad_bind_pass = os.getenv("AD_BIND_PASSWORD")
ldap_server = os.getenv("LDAP_SERVER")
domain = os.getenv("DOMAIN")
user_search_base = os.getenv("USER_SEARCH_BASE")
group_search_base = os.getenv("GROUP_SEARCH_BASE")


def remove_user_from_group(server, username: str, group_name: str) -> dict:
    """
    Удаляет пользователя из указанной группы Active Directory.

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
        conn = Connection(
            server,
            user=f"{domain}\\{ad_bind_user}",
            password=ad_bind_pass,
            authentication="SIMPLE",
            auto_bind=True
        )

        # 1. Находим пользователя
        user_search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        conn.search(
            search_base=user_search_base,
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
            search_base=group_search_base,
            search_filter=group_search_filter,
            attributes=['member']
        )

        if not conn.entries:
            result['message'] = f"Группа {group_name} не найдена"
            return result

        group_dn = conn.entries[0].entry_dn
        result['group_dn'] = group_dn

        # 3. Проверяем, состоит ли пользователь в группе
        current_members = conn.entries[0].member.values
        if user_dn not in current_members:
            result[
                'message'] = f"Пользователь {username} не состоит в группе {group_name}"
            result['success'] = True  # Технически это успех, так как желаемое состояние достигнуто
            return result

        # 4. Удаляем пользователя из группы
        conn.modify(
            group_dn,
            {'member': [(MODIFY_DELETE, [user_dn])]}
        )

        if conn.result['result'] == 0:
            result['success'] = True
            result['message'] = f"Пользователь {username} успешно удален из группы {group_name}"
        else:
            result['message'] = f"Ошибка при удалении из группы: {conn.result['description']}"

    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result