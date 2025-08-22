user_id_to_perm = {}

def clear_all_perms():
    user_id_to_perm.clear()

def check_perms(user_id: int, perm: str) -> bool:
    if check_perms_to_user(user_id, perm):
        return True
    if check_perms_to_user(user_id, "admin"):
        return True
    return False

def add_perms_to_user(user_id: int, perms: list[str]):
    """Добавляет права пользователю, объединяя с текущими (уникальные значения)"""
    current_perms = user_id_to_perm.get(user_id, set())
    new_perms = set(perms)
    user_id_to_perm[user_id] = current_perms | new_perms

def set_perms_to_user(user_id: int, perms: list[str]):
    """Заменяет все права пользователя на новый набор (уникальные значения)"""
    user_id_to_perm[user_id] = set(perms)

def check_perms_to_user(user_id: int, perm: str) -> bool:
    """Проверяет наличие конкретного права у пользователя (админы имеют все права)"""
    user_perms = user_id_to_perm.get(user_id, set())
    return perm in user_perms