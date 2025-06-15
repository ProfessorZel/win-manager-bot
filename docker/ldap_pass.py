import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ldap3 import Connection
from ldap3.core.exceptions import LDAPException

# load_dotenv()

# Конфигурация из .env
ad_bind_user = os.getenv("AD_BIND_USER")
ad_bind_pass = os.getenv("AD_BIND_PASSWORD")
domain = os.getenv("DOMAIN")
base_dn = os.getenv("BASE_DN")


def get_computer_laps_password(server, computer_name: str) -> dict:
    """
    Получает LAPS пароль и информацию о сроке действия для компьютерного аккаунта

    :param server: LDAP сервер
    :param computer_name: Имя компьютера (без $)
    :return: Результат операции с информацией о LAPS пароле
    """
    result = {
        'success': False,
        'message': '',
        'computer_name': computer_name,
        'laps_password': None,
        'laps_expiry': None,
        'laps_expiry_status': None,
        'computer_dn': None
    }

    try:
        conn = Connection(
            server,
            user=f"{domain}\\{ad_bind_user}",
            password=ad_bind_pass,
            authentication="SIMPLE",
            auto_bind=True
        )

        # Поиск компьютерного аккаунта
        search_filter = f"(&(objectClass=computer)(sAMAccountName={computer_name}$))"
        attrs = [
            'ms-Mcs-AdmPwd',
            'ms-Mcs-AdmPwdExpirationTime',
            'distinguishedName',
            'operatingSystem',
            'lastLogonTimestamp'
        ]

        conn.search(
            search_base=f"{base_dn}",
            search_filter=search_filter,
            attributes=attrs
        )

        if not conn.entries:
            result['message'] = f"Компьютерный аккаунт {computer_name} не найден"
            return result

        computer_entry = conn.entries[0]
        result['computer_dn'] = computer_entry.entry_dn

        # Проверяем наличие LAPS атрибутов
        if hasattr(computer_entry, 'ms-Mcs-AdmPwd'):
            result['laps_password'] = str(computer_entry['ms-Mcs-AdmPwd'].value)

            if hasattr(computer_entry, 'ms-Mcs-AdmPwdExpirationTime'):
                # Конвертируем Windows FileTime в datetime
                file_time = int(computer_entry['ms-Mcs-AdmPwdExpirationTime'].value)
                epoch_start = datetime(1601, 1, 1)
                expiration_time = epoch_start + timedelta(microseconds=file_time // 10)

                result['laps_expiry'] = expiration_time.strftime('%Y-%m-%d')

                # Проверяем статус пароля
                current_time = datetime.now()
                if current_time > expiration_time:
                    result['laps_expiry_status'] = '(Истек)'
                    result['message'] = 'Пароль LAPS просрочен'
                else:
                    time_left = expiration_time - current_time
                    days_left = time_left.days
                    result['laps_expiry_status'] = f'({days_left} дней)'
                    result['message'] = 'LAPS пароль успешно получен'

                result['success'] = True
            else:
                result['message'] = 'Атрибут срока действия LAPS пароля не найден'
        else:
            result['message'] = 'LAPS пароль не найден или нет прав на чтение'

        # Дополнительная информация о компьютере
        if hasattr(computer_entry, 'operatingSystem'):
            result['os'] = str(computer_entry['operatingSystem'].value)
        if hasattr(computer_entry, 'lastLogonTimestamp'):
            last_logon = computer_entry['lastLogonTimestamp'].value
            if last_logon:
                last_logon_time = datetime(1601, 1, 1) + timedelta(microseconds=int(last_logon) // 10)
                result['last_logon'] = last_logon_time.strftime('%Y-%m-%d')

    except LDAPException as e:
        result['message'] = f"Ошибка LDAP: {str(e)}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return result