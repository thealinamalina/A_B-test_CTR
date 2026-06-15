"""
Функции для A/B-тестирования (CTR).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Library"))

import pandas as pd
from stat_calc import z_test


def normalize_to_3nf(df):
    """
    Преобразует датасет A/B-теста в три таблицы:
     users, groups, sessions.
    Приводит к 3НФ.

    Параметры:
        df: pandas.DataFrame - датафрейм.
        Замечание: Датасет должен содержать колонки:
        'user_id', 'group', 'converted', 'views'.

    Возвращаемое значение:
        tuple (users, groups, sessions):
            users: pandas.DataFrame с колонкой
            'user_id' (только уникальные).
            groups: pandas.DataFrame с колонками
            'group_id', 'group_name'.
            sessions: pandas.DataFrame с колонками
            'session_id', 'user_id', 'group_id', 'click', 'views'.

    Автор:
        Лукьянова Алина Павловна
    """
    required = {'user_id', 'group', 'converted', 'views'}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise KeyError(f"Отсутствуют необходимые колонки: {missing}")
    group_names = df['group'].unique()
    groups = pd.DataFrame({
        'group_id': range(1, len(group_names) + 1),
        'group_name': group_names
    })
    group_map = dict(zip(groups['group_name'], groups['group_id']))
    users = pd.DataFrame({'user_id': df['user_id'].unique()})
    sessions = df.copy()
    sessions['group_id'] = sessions['group'].map(group_map)
    sessions = sessions.rename(columns={'converted': 'click'})
    sessions['session_id'] = range(1, len(sessions) + 1)
    sessions = sessions[['session_id',
                         'user_id',
                         'group_id',
                         'click',
                         'views']]
    return users, groups, sessions


def denormalize_for_display(groups, sessions):
    """
    Объединяет нормализованные таблицы обратно в
    датасет для отображения в GUI.

    Параметры:
        groups: pandas.DataFrame с колонками
        'group_id', 'group_name'.
        sessions: pandas.DataFrame с колонками
        'session_id', 'user_id', 'group_id', 'click', 'views'.

    Возвращаемое значение:
        df: pandas.DataFrame - датафрейм, колонки:
        user_id, group, converted, views.

    Автор:
        Лукьянова Алина Павловна
    """
    # Добавляем название группы
    sessions_with_group = sessions.merge(groups,
                                         on='group_id',
                                         how='left')
    result = sessions_with_group[['user_id', 'group_name',
                                  'click', 'views']]
    result = result.rename(columns={'group_name': 'group',
                                    'click': 'converted'})
    result['ctr'] = result['converted'] / result['views']
    return result


def ctr_by_group(sessions, groups):
    """
    Рассчитывает CTR (конверсию) для каждой группы.

    Параметры:
        groups: pandas.DataFrame - датафрейм с колонками
        'group_id', 'group_name'.
        sessions: pandas.DataFrame - датафрейм с колонками
        'session_id', 'user_id', 'group_id', 'click', 'views'.

    Возвращаемое значение:
        df: pandas.DataFrame - датафрейм, колонки:
        group_name, ctr.

    Автор:
        Лукьянова Алина Павловна
    """
    agg = sessions.groupby('group_id').agg(
        total_clicks=('click', 'sum'),
        total_views=('views', 'sum')).reset_index()
    agg['ctr'] = agg['total_clicks'] / agg['total_views']
    result = agg.merge(groups, on='group_id')
    return result[['group_name', 'ctr']]


def z_test_two_proportions(sessions, groups, alpha=0.05):
    """
    Выполняет Z-тест для CTR между контрольной и тестовой группами.

    Параметры:
        groups: pandas.DataFrame - датафрейм с колонками
         'group_id', 'group_name'.
        sessions: pandas.DataFrame - датафрейм с колонками
        'session_id', 'user_id', 'group_id', 'click', 'views'.
        alpha: float - уровень значимости результатов.

    Возвращаемое значение:
        dict
            Результат из Library.stat_calc.z_test + интерпретация.

    Автор:
        Лукьянова Алина Павловна
    """
    agg = sessions.groupby('group_id').agg(
        total_clicks=('click', 'sum'),
        total_views=('views', 'sum')).reset_index()
    agg = agg.merge(groups, on='group_id')
    control = agg[agg['group_name'] == 'control'].iloc[0]
    treatment = agg[agg['group_name'] == 'treatment'].iloc[0]
    return z_test(
        control['total_clicks'],
        control['total_views'],
        treatment['total_clicks'],
        treatment['total_views'],
        alpha=alpha
    )


def descriptive_stats_per_group(sessions, groups, metric='click'):
    """
    Возвращает описательные статистики для числовой метрики по группам.

    Параметры:
        groups: pandas.DataFrame - датафрейм с колонками
        'group_id', 'group_name'.
        sessions: pandas.DataFrame - датафрейм с колонками
        'session_id', 'user_id', 'group_id', 'click', 'views'.
        metric: str - принимает 'click' или 'views'

    Возвращаемое значение:
        stats: pandas.DataFrame, индекс – группы, колонки –
        статистики (mean, median, std, var, min, max).

    Автор:
        Лукьянова Алина Павловна
    """
    sessions_with_group = sessions.merge(groups, on='group_id')
    stats = sessions_with_group.groupby('group_name')[metric].agg(
        mean='mean',
        median='median',
        std='std',
        var='var',
        min='min',
        max='max'
    )
    return stats


def pivot_table_report(df, index, columns, values, aggfunc='mean'):
    """
    Формирование сводной таблицы.

    Параметры:
        df: pandas.DataFrame - датафрейм.
        index: str - поля, по которым будут строиться строки таблицы.
        columns: str - поля, по которым будут строиться столбцы таблицы.
        values: str - агрегируемые значения.
        aggfunc: str or function - функция агрегации.

    Возвращаемое значение:
        pandas.DataFrame - сводная таблица.

    Автор:
        Лукьянова Алина Павловна
    """
    return pd.pivot_table(df,
                          index=index,
                          columns=columns,
                          values=values,
                          aggfunc=aggfunc)


def prepare_for_pivot(sessions, groups):
    """
    Подготавливает денормализованные данные для
    построения сводных таблиц.

    Параметры:
        groups: pandas.DataFrame - датафрейм с колонками
        'group_id', 'group_name'.
        sessions: pandas.DataFrame - датафрейм с колонками
        'session_id', 'user_id', 'group_id', 'click', 'views'.

    Возвращаемое значение:
        pandas.DataFrame - датафрейм.

    Автор:
        Лукьянова Алина Павловна
    """
    df = sessions.merge(groups, on='group_id')
    return df[['group_name', 'click', 'views']]


def clean_misassignments(df):
    """
    Удаляет записи, где группа не соответствует landing_page.
    control должны видеть old_page, treatment — new_page.
    Если колонка "landing_page" отсутствует, возвращает датасет
    без изменений.

    Параметры:
        df: pandas.DataFrame - исходный датафрейм.

    Возвращаемое значение:
        df_clean: pandas.DataFrame - датафрейм с применённым фильтром.
        removed: int - количество удалённых строк.

    Автор:
        Лукьянова Алина Павловна
    """
    if 'landing_page' not in df.columns:
        return df, 0
    correct = (
        ((df['group'] == 'control') & (df['landing_page'] == 'old_page')) |
        ((df['group'] == 'treatment') & (df['landing_page'] == 'new_page'))
    )
    removed = (~correct).sum()
    if removed:
        df_clean = df[correct].reset_index(drop=True)
    else:
        df_clean = df.copy()
    return df_clean, removed
