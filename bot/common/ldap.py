from ldap3 import Server, ALL, Connection

from common.config import settings

server = Server(settings.ldap_server, get_info=ALL, use_ssl=True)

def get_connection():
    return Connection(
            server,
            user=f"{settings.domain}\\{settings.ad_bind_user}",
            password=settings.ad_bind_pass,
            authentication="SIMPLE",
            auto_bind=True
        )