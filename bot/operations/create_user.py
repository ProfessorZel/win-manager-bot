from ldap3.core.exceptions import LDAPException

from common.config import settings
from common.ldap import get_connection
from common.translit import create_login_from_name
from operations.add_group import add_user_to_group


def create_user(display_name: str, user_type: str) -> dict:
    """
    Создает пользователя с временным паролем, требующим смены при следующем входе

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
        ou_path = settings.user_ou_mapping.get(user_type)
        group_names = settings.user_group_mapping.get(user_type, [])

        if not ou_path:
            result['message'] = f"Не найдено OU для роли {user_type}, возможные варианты {', '.join(settings.user_ou_mapping.keys())}"
            return result


        result['ou'] = ou_path

        conn = get_connection()
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
                search_base=f"{settings.base_dn}",
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
            "userPrincipalName": f"{username}@{settings.mail_domain}",
            "name": username
        }
        user_dn = f"CN={username},{ou_path},{settings.base_dn}"

        conn.add(user_dn, attributes=user_attributes)

        if not conn.result['result'] == 0:
            result['message'] = f"Ошибка создания: {conn.result['description']}"
            return result

        # Устанавливаем пароль и флаги
        try:
            # 1. Устанавливаем временный пароль
            conn.extend.microsoft.modify_password(user_dn, settings.temp_password)
            result['temp_pass'] = settings.temp_password
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
            group_result = add_user_to_group(username, group_name)
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