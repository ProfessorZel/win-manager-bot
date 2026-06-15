from ldap3 import MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

from common.config import settings
from common.ldap import get_connection


def set_computer_mac(computer_name: str, mac_address: str) -> dict:
    result = {'success': False, 'message': ''}
    try:
        conn = get_connection()
        search_filter = f"(&(objectClass=computer)(sAMAccountName={escape_filter_chars(computer_name)}$))"
        conn.search(
            search_base=settings.base_dn,
            search_filter=search_filter,
            attributes=['distinguishedName']
        )
        if not conn.entries:
            result['message'] = f"Компьютер {computer_name} не найден"
            return result

        dn = conn.entries[0].entry_dn
        conn.modify(dn, {'pager': [(MODIFY_REPLACE, [mac_address])]})

        if conn.result['result'] == 0:
            result['success'] = True
            result['message'] = f"MAC {mac_address} записан для {computer_name}"
        else:
            result['message'] = f"Ошибка записи в AD: {conn.result['description']}"

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()
    return result
