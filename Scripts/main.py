"""
Модуль входа для приложения 'А/В-тестирование и анализ CTR'

Запуск: python main.py
"""

import sys
import os
from ui_main import ABTestApp


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Library"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Scripts"))


def main():
    """
    Точка входа в приложение.

    Создаёт экземпляр ABTestApp и запускает главный цикл.
    Вызывается при запуске скрипта: python Scripts/main.py

    Параметры:
        None

    Возвращаемое значение:
        None

    Автор:
        Лукьянова Алина Павловна
    """
    app = ABTestApp()
    app.run()


if __name__ == "__main__":
    main()
