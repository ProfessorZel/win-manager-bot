from enum import Enum
class Permissions(Enum):
    ADMIN = "admin"
    UNLOCKUSER = "unlockuser"
    BLOCKUSER = "blockuser"
    LISTUSERS = "listusers"
    LAPS = "laps"
    NEWUSER = "newuser"
    RESETPASS = "resetpass"
    VPNENABLE = "vpnenable"
    VPNDISABLE = "vpndisable"

class UserObject:
    user_id: int
    login: str
    perms: set[Permissions]

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.login = None
        self.perms = set()

    def add_perms(self, perms: list[str]):
        """Добавляет права пользователю, объединяя с текущими (уникальные значения)"""
        perms = [Permissions(p) for p in perms]
        new_perms = set(perms)
        self.perms = self.perms | new_perms

    def set_perms(self, perms: list[Permissions]):
        """Заменяет все права пользователя на новый набор (уникальные значения)"""
        self.perms = set(perms)

    def check_perm(self, perm: Permissions) -> bool:
        """Проверяет наличие конкретного права у пользователя (админы имеют все права)"""
        return perm in  self.perms

    def set_login(self, login: str):
        self.login = login

user_id_to_perm: dict[int, UserObject] = {}

def get_user(user_id: int) -> UserObject:
    if user_id not in user_id_to_perm:
        user_id_to_perm[user_id] = UserObject(
            user_id=user_id
        )
    return user_id_to_perm[user_id]

def put_user(user: UserObject):
    user_id_to_perm[user.user_id] = user

def clear_all_users():
    user_id_to_perm.clear()

def check_perms(user_id: int, perm: Permissions) -> bool:
    if get_user(user_id).check_perm(perm):
        return True
    if get_user(user_id).check_perm(Permissions.ADMIN):
        return True
    return False