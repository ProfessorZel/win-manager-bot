import os
import json

from dotenv import load_dotenv
from ldap3 import Connection
from ldap3.core.exceptions import LDAPException

from add_group import add_user_to_group
from translit import create_login_from_name

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

def create_user(server, display_name: str, user_type: str) -> dict:
    """
    Создает пользователя с временным паролем, требующим смены при следующем входе

    :param server:
    :param display_name: Отображаемое имя
    :param user_type: Тип пользователя
    :return: Результат операции
    """
    result = {
        'success': False,
        'message': '',
        'user_dn': None,
        'login': None,
        'ou': None,
        'groups_added': []
    }

    try:



        # Получаем OU и группы
        ou_path = user_ou_mapping.get(user_type)
        group_names = user_group_mapping.get(user_type, [])

        if not ou_path:
            result['message'] = f"Не найдено OU для роли {user_type}, возможные варианты {', '.join(user_ou_mapping.keys())}"
            return result


        result['ou'] = ou_path

        conn = Connection(
            server,
            user=f"{domain}\\{ad_bind_user}",
            password=ad_bind_pass,
            authentication="SIMPLE",
            auto_bind=True
        )
        username = None
        for i in range(1, 7, 2):
            username = create_login_from_name(display_name, name_chars=i)
            if username is None:
                result['message'] = f"Не удалось сгенерировать login для ФИО {display_name}"
                return result
            result['login'] = username

            # Проверяем существование пользователя
            search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
            conn.search(
                search_base=f"{base_dn}",
                search_filter=search_filter,
                attributes=['distinguishedName']
            )
            if not conn.entries:
                break

        if conn.entries:
            result['message'] = f"Не удалось сгенерировать login для ФИО {display_name}, все варианты заняты"
            result['user_dn'] = conn.entries[0].entry_dn
            return result

        # Создаем пользователя
        user_attributes = {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            "displayName": display_name,
            "sAMAccountName": username,
            "userPrincipalName": f"{username}@{mail_domain}",
            "name": username
        }
        user_dn = f"CN={username},{ou_path},{base_dn}"

        conn.add(user_dn, attributes=user_attributes)

        if not conn.result['result'] == 0:
            result['message'] = f"Ошибка создания: {conn.result['description']}"
            return result

        # Устанавливаем пароль и флаги
        try:
            # 1. Устанавливаем временный пароль
            conn.extend.microsoft.modify_password(user_dn, temp_password)
            result['temp_pass'] = temp_password
            modify_attrs = {
                'userAccountControl': [('MODIFY_REPLACE', 512)],
                'pwdLastSet': [('MODIFY_REPLACE', 0)],
            }
            conn.modify(user_dn, modify_attrs)

            if not conn.result['result'] == 0:
                raise LDAPException(f"Ошибка установки флагов: {conn.result['description']}")

        except Exception as e:
            conn.delete(user_dn)  # Откатываем создание пользователя при ошибке
            raise e

        result['user_dn'] = user_dn
        result['message'] = f"Пользователь {username} создан. Требуется смена пароля при входе."

        # Добавляем в группы
        for group_name in group_names:
            group_result = add_user_to_group(server, username, group_name)
            if group_result['success']:
                result['groups_added'].append(group_name)
            else:
                result['message'] += f"Ошибка добавления в {group_name}: {group_result['message']}"

        result['success'] = True

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result