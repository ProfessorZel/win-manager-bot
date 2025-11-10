from datetime import datetime, timedelta

from ldap3.core.exceptions import LDAPException

from common.config import settings
from common.ldap import get_connection

def get_computer_mac(computer_name: str) -> dict:
    """
    Получает атрибут pager для компьютерного аккаунта

    :param computer_name: Имя компьютера (без $)
    :return: Результат операции с информацией о pager
    """
    result = {
        'success': False,
        'message': '',
        'computer_name': computer_name,
        'mac': None,
        'computer_dn': None
    }

    try:
        conn = get_connection()

        # Поиск компьютерного аккаунта
        search_filter = f"(&(objectClass=computer)(sAMAccountName={computer_name}$))"
        attrs = [
            'pager',
            'distinguishedName'
        ]

        conn.search(
            search_base=f"{settings.base_dn}",
            search_filter=search_filter,
            attributes=attrs
        )

        if not conn.entries:
            result['message'] = f"Компьютерный аккаунт {computer_name} не найден"
            return result

        computer_entry = conn.entries[0]
        result['computer_dn'] = computer_entry.entry_dn

        # Получаем атрибут pager
        if hasattr(computer_entry, 'pager') and computer_entry['pager'].value:
            result['mac'] = str(computer_entry['pager'].value)
            result['message'] = 'Атрибут pager успешно получен'
            result['success'] = True
        else:
            result['message'] = 'Атрибут pager не найден или пуст'

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result