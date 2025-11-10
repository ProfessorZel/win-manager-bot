from wakeonlan import send_magic_packet


def send_wake_on_lan_simple(mac_address: str) -> dict:
    """
    Отправляет Wake-on-LAN пакет используя библиотеку wakeonlan

    :param mac_address: MAC-адрес компьютера
    :return: Результат операции
    """
    result = {
        'success': False,
        'message': '',
        'mac_address': mac_address
    }

    try:
        send_magic_packet(mac_address)
        result['success'] = True
        result['message'] = f"Wake-on-LAN пакет отправлен для MAC-адреса: {mac_address}"

    except Exception as e:
        result['message'] = f"Ошибка при отправке Wake-on-LAN: {str(e)}"

    return result