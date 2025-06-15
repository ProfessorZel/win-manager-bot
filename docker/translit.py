import re
from typing import Optional, Dict


def create_login_from_name(
        full_name: str,
        name_chars: int = 1,
        patronymic_chars: int = 1,
        custom_translit: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Создает логин из ФИО с настраиваемой транслитерацией

    :param full_name: ФИО в формате "Фамилия Имя Отчество"
    :param name_chars: Количество первых букв имени для транслитерации (по умолчанию 1)
    :param patronymic_chars: Количество первых букв отчества для транслитерации (по умолчанию 1)
    :param custom_translit: Словарь для кастомной транслитерации (дополняет стандартный)
    :return: Сгенерированный логин или None при ошибке
    """
    # Базовый словарь транслитерации
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': ' '  # пробел сохраняем для разделения частей имени
    }

    # Добавляем кастомные правила транслитерации если они есть
    if custom_translit:
        translit_dict.update(custom_translit)

    try:
        # Нормализуем и разбиваем ФИО на части
        parts = re.sub(r'\s+', ' ', full_name.strip()).split()
        if len(parts) < 2:
            return None

        surname = parts[0]
        name = parts[1] if len(parts) > 1 else ""
        patronymic = parts[2] if len(parts) > 2 else ""

        # Функция транслитерации с учетом максимальной длины
        def translit_part(text: str, max_chars: int) -> str:
            if not text or max_chars <= 0:
                return ""

            result = []
            for i, char in enumerate(text.lower()):
                if i >= max_chars:
                    break
                if char in translit_dict:
                    result.append(translit_dict[char])
                elif char.isalpha():  # если символ уже английский
                    result.append(char)
            return ''.join(result)

        # Транслитерируем фамилию полностью
        translit_surname = translit_part(surname, len(surname))
        if not translit_surname:
            return None

        # Транслитерируем указанное количество символов имени и отчества
        name_part = translit_part(name, min(name_chars, len(name))) if name else ""
        patronymic_part = translit_part(patronymic, min(patronymic_chars, len(patronymic))) if patronymic else ""

        # Собираем логин
        login = (
                translit_surname.capitalize() +
                name_part.capitalize() +
                patronymic_part.capitalize()
        )

        # Очищаем от недопустимых символов
        login = re.sub(r'[^a-zA-Z]', '', login)

        return login if login else None

    except Exception as e:
        print(f"Ошибка при создании логина: {str(e)}")
        return None


# Тестовые примеры
if __name__ == "__main__":
    test_cases = [
        ("Иванов Пётр Сергеевич", 1, 1),  # IvanovPS
        ("Смирнова Анна", 2, 1),  # SmirnovaAn (а не AN, отчества нет)
        ("Козловский Ян", 2, 0),  # KozlovskiyYan
        ("Щербаков Илья Юрьевич", 1, 2),  # ShcherbakovIYu
        ("Мельник Оксана", 5, 2),  # MelnikOksan (только 5 букв имени)
        ("Горбачёв Михаил", 2, 3),  # GorbachevMi (нет отчества)
        ("O'Коннор Джон", 1, 0),  # OKonnorJ
        ("Петров-Водкин К", 2, 0),  # PetrovVodkinK (имя из 1 буквы)
        ("Лёвкин", 1, 1),  # None (только фамилия)
    ]

    print("Тестирование логинов:")
    for name, n_chars, p_chars in test_cases:
        login = create_login_from_name(name, n_chars, p_chars)
        print(f"{name:<30} → {login if login else 'Некорректное ФИО'}")