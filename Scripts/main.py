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
    app = ABTestApp()
    app.run()


if __name__ == "__main__":
    main()
