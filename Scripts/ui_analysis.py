"""
Модуль вкладки «Анализ» приложения A/B-тестирования.

Обеспечивает расчёт описательных статистик (среднее, медиана, дисперсия, CTR)
и сравнительный анализ групп A и B с выводом результатов в текстовую область.

Автор:
    Галашина Жанна Ивановна
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox  # Добавлено для Scrollbar
import numpy as np
import pandas as pd
from ab_logic import ctr_by_group, z_test_two_proportions, descriptive_stats_per_group

# Функции расчётов


def calc_group_stats(df, group_col="group", metric_col="ctr"):
    """
    Рассчитывает описательные статистики по каждой группе.
    Параметры:
        df (pd.DataFrame): датафрейм с данными.
        group_col (str): название колонки с группами.
        metric_col (str): название колонки с метрикой.
    Возвращает:
        dict: словарь {группа: {статистика: значение}}.
    """
    result = {}
    if df is None or df.empty or group_col not in df.columns:
        return result
    if metric_col not in df.columns:
        return result

    for grp, sub in df.groupby(group_col):
        vals = sub[metric_col].dropna()
        result[grp] = {
            "n":         len(vals),
            "mean":      vals.mean(),
            "median":    vals.median(),
            "std":       vals.std(),
            "var":       vals.var(),
            "min":       vals.min(),
            "max":       vals.max(),
            "sum_clicks":  sub["clicks"].sum()
            if "clicks" in sub.columns else None,
            "sum_views":   sub["views"].sum()
            if "views" in sub.columns else None,
        }
        # CTR по всей группе
        sc = result[grp]["sum_clicks"]
        sv = result[grp]["sum_views"]
        result[grp]["agg_ctr"] = (sc / sv) \
            if (sc is not None and sv and sv > 0) else None

    return result


def compare_groups(df,
                   group_col="group",
                   metric_col="ctr",
                   confidence_level=0.95):
    """
    Выполняет сравнение двух групп: разница средних и
    приблизительная значимость.

    Параметры:
        df (pd.DataFrame): датафрейм с данными.
        group_col (str): название колонки с группами.
        metric_col (str): название колонки с метрикой.
        confidence_level (float): уровень доверия из config.ini
        (по умолчанию 0.95).
    Возвращает:
        str: многострочный текстовый отчёт.
    """
    if df is None or df.empty:
        return "Данные не загружены."

    groups = df[group_col].unique() if group_col in df.columns else []
    if len(groups) < 2:
        return "Недостаточно групп для сравнения."

    g_a = df[df[group_col] == "A"][metric_col].dropna() \
        if "A" in groups else pd.Series()
    g_b = df[df[group_col] == "B"][metric_col].dropna() \
        if "B" in groups else pd.Series()

    if g_a.empty or g_b.empty:
        return "Одна из групп пуста."

    diff = g_b.mean() - g_a.mean()
    rel = (diff / g_a.mean() * 100) if g_a.mean() != 0 else 0.0

    # Приближённая проверка значимости через z-тест для разницы средних
    n_a, n_b = len(g_a), len(g_b)
    se = np.sqrt(g_a.var() / n_a + g_b.var() / n_b)
    z = diff / se if se > 0 else 0.0
    # Порог z определяется уровнем доверия из config.ini
    # confidence_level=0.95 → z_crit=1.96; 0.99 → 2.576
    z_table = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
    z_crit = z_table.get(round(confidence_level, 2), 1.96)
    significant = abs(z) > z_crit

    lines = [
        "═" * 50,
        "СРАВНЕНИЕ ГРУПП A и B",
        "═" * 50,
        f"Метрика: {metric_col}",
        "",
        f"Средний CTR группы A: {g_a.mean():.4f}",
        f"Средний CTR группы B: {g_b.mean():.4f}",
        f"Разница (B − A)     : {diff:+.4f}",
        f"Относительное изменение: {rel:+.1f}%",
        "",
        f"Z-статистика        : {z:.3f}",
        f"Значимость (α=0.05): {'ДА — различия статистически значимы' if significant else 'НЕТ — различия не значимы'}",
        "",
        "─" * 50,
        "ВЫВОД:",
        (
            f"Группа B показывает {'лучший' if diff > 0 else 'худший'} результат на {abs(rel):.1f}%."
            if significant else
            "Различия между группами не являются статистически значимыми."
        ),
        "═" * 50,
    ]
    return "\n".join(lines)


def format_stats_text(stats):
    """
    Форматирует словарь статистик в читаемый текстовый отчёт.

    Параметры:
        stats (dict): словарь {группа: {статистика: значение}}.
    Возвращает:
        str: многострочный текстовый отчёт.
    """
    if not stats:
        return "Нет данных для расчёта."

    lines = ["═" * 50, "  ОПИСАТЕЛЬНЫЕ СТАТИСТИКИ", "═" * 50]
    for grp in sorted(stats.keys()):
        s = stats[grp]
        lines += [
            f"\n  Группа {grp}",
            "─" * 50,
            f"  Кол-во записей   : {s['n']}",
            f"  Среднее CTR      : {s['mean']:.4f}",
            f"  Медиана CTR      : {s['median']:.4f}",
            f"  Стд. отклонение  : {s['std']:.4f}",
            f"  Дисперсия        : {s['var']:.4f}",
            f"  Минимум          : {s['min']:.4f}",
            f"  Максимум         : {s['max']:.4f}",
        ]
        if s["sum_clicks"] is not None:
            lines.append(f"  Сумма кликов     : {s['sum_clicks']}")
            lines.append(f"  Сумма просмотров : {s['sum_views']}")
        if s["agg_ctr"] is not None:
            lines.append(f"  CTR по группе    : {s['agg_ctr']:.4f}")

    lines += ["", "═" * 50]
    return "\n".join(lines)

# Класс вкладки «Анализ»


class AnalysisTab:
    """
    Вкладка «Анализ»: расчёт метрик и сравнение групп A/B.

    Параметры:
        parent (tk.Widget): родительский контейнер (рабочая область).
        app (ABTestApp): ссылка на главный объект приложения.
    Возвращает: нет
    """

    def __init__(self, parent, app):
        """
        Инициализация: создаёт фрейм вкладки и все виджеты.

        Параметры:
            parent (tk.Widget): контейнер рабочей области.
            app (ABTestApp): главный объект приложения.
        Возвращает: нет
        """
        self.app = app
        self.frame = ctk.CTkFrame(parent, fg_color="#f5f6fa")

        self._build_toolbar()
        self._build_content()

    # Построение интерфейса 

    def _build_toolbar(self):
        """
        Создаёт панель инструментов с кнопками расчётов.

        Параметры: нет
        Возвращает: нет
        """
        toolbar = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        toolbar.pack(fill=tk.X, padx=10, pady=6)

        ctk.CTkLabel(toolbar, text="Статистический анализ",
                     font=(self.app.font_family, 14, "bold"),
                     text_color=self.app.accent).pack(side=tk.LEFT,
                                                      padx=(0, 20))

        # Выбор метрики
        ctk.CTkLabel(toolbar, text="Метрика:").pack(side=tk.LEFT)
        self.metric_var = tk.StringVar(value="click")
        metric_combo = ctk.CTkComboBox(toolbar,
                                       variable=self.metric_var,
                                       values=["click", "views"],
                                       width=100,
                                       state="readonly")
        metric_combo.pack(side=tk.LEFT, padx=6)

        ctk.CTkButton(toolbar,
                      text="Описательные статистики",
                      command=self._show_descriptive).pack(side=tk.LEFT,
                                                           padx=4)
        ctk.CTkButton(toolbar,
                      text="Сравнить группы (Z-тест)",
                      command=self._show_comparison).pack(side=tk.LEFT,
                                                          padx=4)
        ctk.CTkButton(toolbar,
                      text="Сохранить отчёт",
                      command=self._save_report).pack(side=tk.LEFT,
                                                      padx=4)
        ctk.CTkButton(toolbar,
                      text="Очистить",
                      command=self._clear_output).pack(side=tk.RIGHT,
                                                       padx=4)

    def _build_content(self):
        """
        Создаёт карточки сводных показателей и текстовую область вывода.

        Параметры: нет
        Возвращает: нет
        """
        # Верхняя строка с карточками KPI
        kpi_frame = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        kpi_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.kpi_cards = {}
        kpi_defs = [("ctr_control", "CTR контроль", "#3498db"),
                    ("ctr_treatment", "CTR тест", "#2ecc71")]
        for key, label, color in kpi_defs:
            card = self._make_kpi_card(kpi_frame, label, "—", color)
            card.pack(side=tk.LEFT, padx=6, pady=4)
            self.kpi_cards[key] = card

        # Текстовая область
        text_frame = ctk.CTkFrame(self.frame,
                                  fg_color="#f5f6fa")
        text_frame.pack(fill=tk.BOTH,
                        expand=True,
                        padx=10,
                        pady=(0, 10))
        wrapper = ctk.CTkFrame(text_frame,
                               fg_color="white",
                               border_width=1,
                               border_color="#dcdde1")
        wrapper.pack(fill=tk.BOTH, expand=True)
        v_scroll = ttk.Scrollbar(wrapper, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output = tk.Text(wrapper,
                              font=("Courier New", 10),
                              bg="white",
                              fg="#2d3436",
                              relief=tk.FLAT,
                              padx=14,
                              pady=10,
                              yscrollcommand=v_scroll.set,
                              wrap=tk.NONE, state=tk.DISABLED)
        self.output.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=self.output.yview)

    def _make_kpi_card(self, parent, label, value, color):
        """
        Создаёт одну карточку KPI (цветная рамка с заголовком
        и значением).

        Параметры:
            parent (tk.Widget): родительский фрейм.
            label (str): подпись карточки.
            value (str): начальное значение.
            color (str): цвет рамки.
        Возвращает:
            ctk.CTkFrame: фрейм карточки.
        """
        outer = ctk.CTkFrame(parent,
                             fg_color="white",
                             border_width=2,
                             border_color=color)
        ctk.CTkLabel(outer,
                     text=label,
                     text_color="#636e72",
                     font=(self.app.font_family, 8)).pack(padx=12,
                                                          pady=(6, 0))
        val_lbl = ctk.CTkLabel(outer,
                               text=value,
                               text_color=color,
                               font=(self.app.font_family, 16, "bold"))
        val_lbl.pack(padx=12, pady=(0, 8))
        outer.val_label = val_lbl
        return outer

    # ── Действия ────────────────────────────────────────────────────

    def _show_descriptive(self):
        """
        Рассчитывает описательные статистики и выводит их
        в текстовую область.

        Параметры: нет
        Возвращает: нет
        """
        if self.app.sessions is None or self.app.groups is None:
            self._write_output(
                "Данные не загружены или не нормализованы."
            )
            return
        metric = self.metric_var.get()
        stats = descriptive_stats_per_group(self.app.sessions,
                                            self.app.groups,
                                            metric=metric)
        self._write_output(f"Описательные статистики для метрики '{metric}':\n\n{stats.to_string()}")
        self._update_kpi()

    def _show_comparison(self):
        """
        Выполняет сравнение групп и выводит результат
        в текстовую область.

        Параметры: нет
        Возвращает: нет
        """
        if self.app.sessions is None or self.app.groups is None:
            self._write_output("Данные не загружены или не нормализованы.")
            return
        alpha = getattr(self.app, 'confidence_level', 0.05)
        res = z_test_two_proportions(self.app.sessions,
                                     self.app.groups,
                                     alpha=alpha)
        text = (f"Z-тест для пропорций (CTR):\n"
                f"Z-статистика: {res['z_stat']:.4f}\n"
                f"p-value: {res['p_value']:.6f}\n"
                f"CTR контроль: {res['control_ctr']:.4f}\n"
                f"CTR тест: {res['treatment_ctr']:.4f}\n"
                f"Lift: {res['lift']:.2f}%\n"
                f"Вывод: {res['interpretation']}")
        self._write_output(text)
        self._update_kpi()

    def _clear_output(self):
        """
        Очищает текстовую область вывода.

        Параметры: нет
        Возвращает: нет
        """
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)

    def _write_output(self, text):
        """
        Записывает текст в область вывода
        (заменяет предыдущее содержимое).

        Параметры:
            text (str): текст для отображения.
        Возвращает: нет
        """
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.config(state=tk.DISABLED)

    def _update_kpi(self):
        """
        Обновляет значения карточек KPI на основе
        рассчитанных статистик.

        Параметры: нет
        Возвращает: нет
        """
        if self.app.sessions is None or self.app.groups is None:
            return
        ctr_df = ctr_by_group(self.app.sessions, self.app.groups)
        ctr_dict = dict(zip(ctr_df['group_name'], ctr_df['ctr']))
        self.kpi_cards['ctr_control'].val_label.configure(
            text=f"{ctr_dict.get('control',0):.4f}"
        )
        self.kpi_cards['ctr_treatment'].val_label.configure(
            text=f"{ctr_dict.get('treatment',0):.4f}"
        )

    def _save_report(self):
        """
        Сохраняет отчёт по заданному пути.

        Параметры: нет
        Возвращает: нет
        """
        content = self.output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Нет отчёта", "Нечего сохранять.")
            return
        output_dir = self.app.cfg.get("Paths", "output_dir",
                                      fallback="Output")
        path = filedialog.asksaveasfilename(initialdir=output_dir,
                                            defaultextension=".txt",
                                            filetypes=[("Text files",
                                                        "*.txt")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Сохранено", f"Отчёт сохранён в {path}")

    def update_analysis(self):
        """
        Автоматически обновляет KPI-карточки при загрузке новых данных.

        Параметры: нет
        Возвращает: нет
        """
        self._update_kpi()
