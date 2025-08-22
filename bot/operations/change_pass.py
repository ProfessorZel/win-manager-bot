import random
import secrets
import string

from ldap3.core.exceptions import LDAPException
from common.config import settings
from common.ldap import get_connection


def generate_random_password(length=8):
    """Генерирует случайный безопасный пароль заданной длины"""
    chars = list(secrets.token_urlsafe(length - 4) +
         random.choice(string.ascii_lowercase) +
         random.choice(string.ascii_uppercase) +
         random.choice(string.digits) +
         random.choice(string.punctuation))
    random.shuffle(chars)

    return ''.join(chars)


def reset_password(username: str, new_password: str = None) -> dict:
    """
    Сбрасывает пароль пользователя без установки флага смены пароля при следующем входе

    :param username: Логин пользователя (sAMAccountName)
    :param new_password: Новый пароль (опционально, генерируется автоматически если не указан)
    :return: Результат операции
    """
    result = {
        'success': False,
        'message': '',
        'user_dn': None,
        'password_changed': False,
        'new_password': new_password
    }

    try:
        conn = get_connection()

        # Поиск пользователя по логину
        search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        conn.search(
            search_base=f"{settings.user_search_base}",
            search_filter=search_filter,
            attributes=['distinguishedName']
        )

        if not conn.entries:
            result['message'] = f"Пользователь с логином '{username}' не найден"
            return result

        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn
        result['user_dn'] = user_dn

        # Генерируем пароль если не был предоставлен
        if new_password is None:
            new_password = generate_random_password()
            result['new_password'] = new_password

        # Устанавливаем новый пароль
        conn.extend.microsoft.modify_password(user_dn, new_password)

        if conn.result['result'] == 0:
            result['password_changed'] = True
            result['message'] = f"Пароль для пользователя '{username}' успешно сброшен"
            result['success'] = True
        else:
            result['message'] = f"Ошибка при смене пароля: {conn.result['description']}"

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result