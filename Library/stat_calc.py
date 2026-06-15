"""
Модуль сбора статистики
"""
import math

import pandas as pd


def z_test(converted_control, views_control,
           converted_treatment, views_treatment, alpha=0.05):
    """
    Z-тест (расчёт CTR) между контрольной и тестовой группой.

    Параметры:
        converted_control: int - количество конверсий (кликов)
        в контрольной группе.
        views_control: int - количество показов
        в контрольной группе.
        converted_treatment: int - количество конверсий (кликов)
        в тестовой группе.
        views_treatment: int - количество показов в
        тестовой группе.
        alpha: float - уровень значимости.

    Возвращаемое значение:
        dict
            Ключи:
            - 'z_stat': float
            - 'p_value': float
            - 'reject': bool
            - 'control_ctr': float
            - 'treatment_ctr': float
            - 'lift': float
            - 'interpretation': str

    Автор:
        Лукьянова Алина Павловна
    """
    control_proportion = converted_control / views_control
    treatment_proportion = converted_treatment / views_treatment
    proportion_pool = ((converted_control + converted_treatment) /
                       (views_control + views_treatment))
    standard_error = math.sqrt(proportion_pool * (1 - proportion_pool)
                               * (1 / views_control +
                                  1 / views_treatment))
    z = (treatment_proportion - control_proportion) / standard_error
    proportion_value = 2 * (1 - (1 + math.erf(abs(z) / math.sqrt(2))) / 2)
    reject = proportion_value < alpha
    lift = ((treatment_proportion - control_proportion) /
            control_proportion * 100) if control_proportion > 0 else 0.0
    return {
        'z_stat': z,
        'p_value': proportion_value,
        'reject': reject,
        'control_ctr': control_proportion,
        'treatment_ctr': treatment_proportion,
        'lift': lift,
        'interpretation': 'Различия статистически значимы'
        if reject else 'Различия статистически не значимы'
    }


def descriptive_stats(df, numeric_cols):
    """
    Возвращает описательные статистики для числовых столбцов.

    Праметры:
        df : pandas.DataFrame - датафрейм.
        numeric_cols : list of str -
        Список заголовков числовых колонок.

    Возвращаемое значение:
        result: pandas.DataFrame - датафрейм,
        индекс – названия статистик, столбцы – переменные.

    Автор:
        Лукьянова Алина Павловна
    """
    stats = df[numeric_cols].describe().T
    stats['median'] = df[numeric_cols].median()
    stats['variance'] = df[numeric_cols].var()
    result = stats[['mean',
                    'median',
                    'variance',
                    'std',
                    'min',
                    'max']].T
    return result


def frequency_table(df, categorical_col):
    """
    Строит таблицу частот для
    категориальной переменной.

    Параметры:
        df : pandas.DataFrame - датафрейм.
        categorical_col : str - название колонки.

    Возвращаемое значение:
        result: pandas.DataFrame - датафрейм,
        колонки: 'Значение', 'Частота', 'Процент'

    Автор:
        Лукьянова Алина Павловна
    """
    freq = df[categorical_col].value_counts()
    percent = 100 * freq / len(df)
    result = pd.DataFrame({
        'Значение': freq.index,
        'Частота': freq.values,
        'Процент': percent.values
    })
    return result
