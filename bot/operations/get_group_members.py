import logging

from ldap3 import SUBTREE
from ldap3.utils.conv import escape_filter_chars

from common.config import settings
from common.ldap import get_connection


def get_group_members(group_name, user_attributes=None, actve_only=False):
    """
    Retrieve user members of a group in Active Directory.

    :param server_address: LDAP server address (e.g., 'ldap://domain.com')
    :param bind_dn: Bind DN (e.g., 'admin@domain.com')
    :param bind_password: Bind password
    :param base_dn: Base DN (e.g., 'dc=domain,dc=com')
    :param group_name: Group's common name (CN)
    :param user_attributes: List of user attributes to retrieve (default: ['cn', 'sAMAccountName'])
    :return: List of user entries (or empty list if none found)
    """
    if user_attributes is None:
        user_attributes = ['cn', 'sAMAccountName']  # Default attributes

    # 1. Connect to LDAP server
    conn = get_connection()

    try:
        # 2. Search for the target group
        group_filter = f"(&(objectClass=group)(cn={group_name}))"
        conn.search(
            search_base=settings.base_dn,
            search_filter=group_filter,
            search_scope=SUBTREE,
            attributes=['member']  # Retrieve only 'member' attribute
        )

        if not conn.entries:
            logging.info(f"Group '{group_name}' not found.")
            return []

        group_entry = conn.entries[0]
        member_dns = group_entry.member.values  # List of user DNs

        if not member_dns:
            logging.info(f"Group '{group_name}' has no members.")
            return []

        # 3. Fetch user entries in chunks (to avoid huge filters)
        users = []
        chunk_size = 100  # Adjust based on LDAP server limits
        for i in range(0, len(member_dns), chunk_size):
            chunk = member_dns[i:i + chunk_size]

            # Build OR-filter for DNs in current chunk
            or_filters = ''.join([f'(distinguishedName={escape_filter_chars(dn)})' for dn in chunk])
            search_filter = f"(&(objectClass=user)" + (f"(!(userAccountControl:1.2.840.113556.1.4.803:=2))" if actve_only else "")+ (f"(!(lockoutTime>=1))" if actve_only else "") + (f"(|{or_filters}))")


            conn.search(
                search_base=settings.base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=user_attributes
            )
            users.extend(conn.entries)

        return users

    finally:
        conn.unbind()