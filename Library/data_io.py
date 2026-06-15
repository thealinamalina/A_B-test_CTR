"""
Модуль для ввода/вывода данных
"""


import pandas as pd
from pathlib import Path
import pickle


def load_csv_data(filename):
    """
    Загружает CSV файл с датасетом из папки Data.

    Параметры:
        filename: str - имя файла.

    Возвращаемое значение:
        df: pandas.DataFrame - загруженные данные в формате датафрейма.

    Автор:
        Лукьянова Алина Павловна
    """
    path = Path(__file__).resolve().parent
    file_path = path / "Data" / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Файл: {file_path} не найден.")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Ошибка при чтении файла: {e}.")
    if df.empty:
        raise ValueError("Файл пуст.")
    return df


def load_pickle(filepath):
    """
    Загружает данные из бинарного файла (pickle).

    Параметры:
        filepath: str - путь к файлу.

    Возвращаемое значение:
        any - загруженные данные.

    Автор:
        Лукьянова Алина Павловна
    """
    with open(filepath, 'rb') as file:
        return pickle.load(file)


def save_pickle(data, filepath):
    """
    Сохраняет данные в бинарный файл.

    Параметры:
        data: any - сохраняемые данные.
        filepath: str - путь к файлу.

    Возвращаемое значение:
        None

    Автор:
        Лукьянова Алина Павловна
    """
    with open(filepath, 'wb') as file:
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
