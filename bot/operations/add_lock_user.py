import random

from common.config import settings
from common.sciener import add_keyboard_password


async def create_lock_user(name: str) -> dict:
    result = {'success': False, 'message': '', 'code': None}
    if not settings.sciener_client_id:
        result['message'] = 'Sciener не настроен'
        return result
    try:
        code = str(random.randint(10000, 99999))
        data = await add_keyboard_password(name, code)
        if 'keyboardPwdId' in data:
            result['success'] = True
            result['code'] = code
        else:
            result['message'] = f"Ошибка API: {data.get('errmsg', str(data))}"
    except Exception as e:
        result['message'] = f"Критическая ошибка: {str(e)}"
    return result
