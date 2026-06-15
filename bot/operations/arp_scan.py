import socket
import logging

from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp


def resolve_hostname(hostname: str) -> str | None:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def get_mac_by_ip(ip: str) -> str | None:
    try:
        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
        answered, _ = srp(packet, timeout=2, verbose=False)
        if answered:
            return answered[0][1].hwsrc
    except Exception as e:
        logging.debug(f"ARP failed for {ip}: {e}")
    return None
