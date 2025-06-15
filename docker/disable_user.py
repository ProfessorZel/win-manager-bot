import json
import os
import string
import secrets

from dotenv import load_dotenv
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

def generate_random_password(length=32):
    """Генерирует случайный безопасный пароль заданной длины"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def disable_user(server, username: str) -> dict:
    """
    Отключает пользователя, перемещает в другую OU и устанавливает случайный пароль

    :param server: Сервер LDAP
    :param username: Логин пользователя (sAMAccountName)
    :return: Результат операции
    """
    result = {
        'success': False,
        'message': '',
        'user_dn': None,
        'disabled': False,
        'password_changed': False,
        'moved': False
    }

    # Получаем OU для отключенных пользователей из .en
    if not disabled_ou:
        result['message'] = "Переменная DISABLED_OU не задана в .env"
        return result

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
            attributes=['userAccountControl', 'distinguishedName']
        )

        if not conn.entries:
            result['message'] = f"Пользователь с логином '{username}' не найден или уже выключен или не принадлежит {user_search_base}"
            return result

        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn
        current_flags = int(user_entry.userAccountControl.value)
        result['user_dn'] = user_dn

        # Проверяем, не отключен ли уже пользователь
        if current_flags & 2:
            result['message'] += f"Пользователь '{username}' уже отключен. "
            result['disabled'] = True
        else:
            # Устанавливаем флаг ACCOUNTDISABLE
            new_flags = current_flags | 2
            conn.modify(
                user_dn,
                {'userAccountControl': [(MODIFY_REPLACE, new_flags)]}
            )
            result['disabled'] = True
            result['message'] += f"Пользователь '{username}' отключен. "

        # Генерируем и устанавливаем случайный пароль
        new_password = generate_random_password()
        conn.extend.microsoft.modify_password(user_dn, new_password)
        if conn.result['result'] == 0:
            result['password_changed'] = True
            result['message'] += f"Пароль сменен. "
        else:
            result['message'] += f"Ошибка при смене пароля: {conn.result['description']} "

        # Устанавливаем флаг смены пароля при следующем входе
        conn.modify(
            user_dn,
            {'pwdLastSet': [(MODIFY_REPLACE, 0)]}
        )


        # Перемещаем пользователя в DISABLED_OU
        new_rdn = f"CN={username}"
        conn.modify_dn(user_dn, new_rdn, new_superior=f"{disabled_ou},{base_dn}")
        if conn.result['result'] == 0:
            result['user_dn'] = f"{new_rdn},{disabled_ou},{base_dn}"
            result['moved'] = True
            result['message'] += f"Перемещен в {disabled_ou}. "
        else:
            result['message'] += f"Ошибка при перемещение: {conn.result['description']}"


        result['success'] = True


    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result