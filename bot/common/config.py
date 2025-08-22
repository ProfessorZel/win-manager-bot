import json
import os

from dotenv import load_dotenv

#load_dotenv()
class Settings:
    bot_token = os.getenv("TOKEN")
    ldap_server = os.getenv("LDAP_SERVER")
    vpn_access_group = os.getenv("VPN_ACCESS_GROUP")
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
    disabled_ou = os.getenv("DISABLED_OU")
    group_perm_mapping = json.loads(os.getenv("GROUP_PERM_MAPPING"))
    group_perms_sync_interval_seconds = os.getenv("GROUP_PERM_SYNC_INTERVAL_SECONDS", 3600)
    remove_new_password_msg_after = os.getenv("REMOVE_NEW_PASSWORD_MSG_AFTER", 120)
settings = Settings()