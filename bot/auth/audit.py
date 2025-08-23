import json
import logging

from auth.perms_storage import get_user

audit_log = logging.getLogger("audit")

def writeAuditLog(action: str, executor: int, message: str, args: object):
    user = get_user(executor)
    logging.info(
        f"{action} выполнено ({user.user_id}){user.login} с результатом: {message}, дополнительные параметры:" +
        json.dumps(args, ensure_ascii=False, sort_keys=True)
    )