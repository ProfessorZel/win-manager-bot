import json
import os

from ldap3 import MODIFY_REPLACE, Connection
from ldap3.core.exceptions import LDAPException

# load_dotenv()

# Конфигурация из .env
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
disabled_ou = os.getenv("DISABLED_OU")


def unlock_user(server, username: str) -> dict:
    """
    Разблокирует пользователя, заблокированного из-за неверных попыток входа

    :param server: Сервер LDAP
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
        conn = Connection(
            server,
            user=f"{domain}\\{ad_bind_user}",
            password=ad_bind_pass,
            authentication="SIMPLE",
            auto_bind=True
        )

        # Поиск пользователя по логину
        search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        conn.search(
            search_base=f"{user_search_base}",
            search_filter=search_filter,
            attributes=['lockoutTime', 'distinguishedName']
        )

        if not conn.entries:
            result['message'] = f"Пользователь '{username}' не найден"
            return result

        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn
        result['user_dn'] = user_dn

        # Проверка блокировки
        lockout_time = getattr(user_entry, 'lockoutTime', 0)
        if lockout_time.value == 0:
            result['message'] = f"Пользователь '{username}' не заблокирован"
            result['unlocked'] = True
            result['success'] = True
            return result

        # Сброс блокировки
        conn.modify(
            user_dn,
            {'lockoutTime': [(MODIFY_REPLACE, 0)]}
        )

        if conn.result['result'] == 0:
            result['unlocked'] = True
            result['success'] = True
            result['message'] = f"Пользователь '{username}' успешно разблокирован"
        else:
            result['message'] = f"Ошибка разблокировки: {conn.result['description']}"

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result