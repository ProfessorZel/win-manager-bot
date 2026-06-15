import logging

from ldap3.core.exceptions import LDAPException

from common.config import settings
from common.ldap import get_connection
from operations.arp_scan import get_mac_by_ip, resolve_hostname
from operations.set_pc_mac import set_computer_mac


def get_computers_without_mac() -> list[dict]:
    computers = []
    try:
        conn = get_connection()
        conn.search(
            search_base=settings.base_dn,
            search_filter="(&(objectClass=computer)(!(pager=*)))",
            attributes=['sAMAccountName', 'dNSHostName']
        )
        for entry in conn.entries:
            name = str(entry['sAMAccountName']).rstrip('$')
            dns = entry['dNSHostName'].value
            computers.append({'name': name, 'dns': dns})
    except LDAPException as e:
        logging.error(f"MAC sync: ошибка LDAP: {e}")
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()
    return computers


async def sync_macs_job(context):
    computers = get_computers_without_mac()
    if not computers:
        logging.info("MAC sync: все компьютеры уже имеют MAC")
        return

    logging.info(f"MAC sync: найдено {len(computers)} компьютеров без MAC")
    synced = 0

    for computer in computers:
        dns = computer['dns']
        if not dns:
            continue
        ip = resolve_hostname(dns)
        if not ip:
            continue
        mac = get_mac_by_ip(ip)
        if not mac:
            continue
        result = set_computer_mac(computer['name'], mac)
        if result['success']:
            logging.info(f"MAC sync: {computer['name']} → {mac}")
            synced += 1

    logging.info(f"MAC sync: записано {synced} MAC-адресов")
