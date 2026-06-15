"""
Модуль вкладки «Отчёты» приложения A/B-тестирования.
 
Обеспечивает построение графиков (столбчатая диаграмма, гистограмма,
диаграмма Бокса–Вискера, рассеивания) и сохранение текстовых/графических отчётов.

Автор:
    Галашина Жанна Ивановна
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

# matplotlib подключается ленивым импортом, чтобы не замедлять старт
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from ab_logic import prepare_for_pivot, pivot_table_report
matplotlib.use("TkAgg")


def plot_bar(fig, df, metric="ctr", group_col="group"):
    """
    Строит столбчатую диаграмму среднего значения метрики по группам.
 
    Параметры:
        fig (Figure): объект фигуры matplotlib.
        df (pd.DataFrame): датафрейм с данными.
        metric (str): название метрики.
        group_col (str): название колонки с группами.
    Возвращает: нет
    """
    ax = fig.add_subplot(111)
    if df is None or df.empty or group_col not in df.columns:
        ax.text(0.5, 0.5, "Нет данных",
                ha="center",
                va="center")
        return
 
    grouped = df.groupby(group_col)[metric].mean()
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]
    bars = ax.bar(grouped.index, grouped.values,
                  color=colors[:len(grouped)], width=0.5,
                  edgecolor="white", linewidth=1.5)
    
    for bar, val in zip(bars, grouped.values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.001,
                f"{val:.4f}",
                ha="center",
                va="bottom",
                fontsize=9)
 
    ax.set_title(f"Средний {metric.upper()} по группам",
                 fontsize=12,
                 fontweight="bold")
    ax.set_xlabel("Группа")
    ax.set_ylabel(metric.upper())
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_hist(fig, df, metric="ctr", group_col="group"):
    """
    Строит гистограмму распределения метрики по группам.
 
    Параметры:
        fig (Figure): объект фигуры matplotlib.
        df (pd.DataFrame): датафрейм с данными.
        metric (str): название метрики.
        group_col (str): название колонки с группами.
    Возвращает: нет
    """
    ax = fig.add_subplot(111)
    if df is None or df.empty or group_col not in df.columns:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        return
 
    colors = {"control": "#3498db", "treatment": "#e74c3c"}
    for grp, sub in df.groupby(group_col):
        vals = sub[metric].dropna()
        ax.hist(vals, bins=15, alpha=0.65,
                color=colors.get(grp, "#95a5a6"),
                label=f"Группа {grp}", edgecolor="white")

    ax.set_title(f"Гистограмма распределения {metric.upper()}",
                 fontsize=12,
                 fontweight="bold")
    ax.set_xlabel(metric.upper())
    ax.set_ylabel("Частота")
    ax.legend()
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    
def plot_boxplot(fig, df, metric="ctr", group_col="group"):
    """
    Строит диаграмму Бокса–Вискера для метрики по группам.

    Параметры:
        fig (Figure): объект фигуры matplotlib.
        df (pd.DataFrame): датафрейм с данными.
        metric (str): название метрики.
        group_col (str): название колонки с группами.
    Возвращает: нет
    """
    ax = fig.add_subplot(111)
    if df is None or df.empty or group_col not in df.columns:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        return
 
    groups = sorted(df[group_col].unique())
    data = [df[df[group_col] == g][metric].dropna().values
            for g in groups]
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]
 
    bp = ax.boxplot(data,
                    labels=groups,
                    patch_artist=True,
                    notch=False,
                    medianprops=dict(color="white",
                                     linewidth=2))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
        
    ax.set_title(f"Диаграмма Бокса–Вискера: {metric.upper()}",
                 fontsize=12,
                 fontweight="bold")
    ax.set_xlabel("Группа")
    ax.set_ylabel(metric.upper())
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    

def plot_scatter(fig, df,
                 x_col="views",
                 y_col="converted",
                 group_col="group"):
    """
    Строит диаграмму рассеивания converted vs views
    с раскраской по группам.
 
    Параметры:
        fig (Figure): объект фигуры matplotlib.
        df (pd.DataFrame): датафрейм с данными.
        x_col (str): колонка для оси X.
        y_col (str): колонка для оси Y.
        group_col (str): название колонки с группами.
    Возвращает: нет
    """
    ax = fig.add_subplot(111)
    if df is None or df.empty:
        ax.text(0.5, 0.5, "Нет данных",
                ha="center",
                va="center")
        return
 
    colors = {"control": "#3498db", "treatment": "#e74c3c"}
    for grp in df[group_col].unique():
        sub = df[df[group_col] == grp]
        sub_clean = sub[[x_col, y_col]].dropna()
        if sub_clean.empty:
            continue
        xv = sub_clean[x_col]
        yv = sub_clean[y_col]
        ax.scatter(xv, yv, alpha=0.65, s=40,
                   color=colors.get(grp, "#95a5a6"),
                   label=f"Группа {grp}",
                   edgecolors="white",
                   linewidths=0.5)

    ax.set_title(f"Диаграмма рассеивания: {y_col} vs {x_col}",
                 fontsize=12,
                 fontweight="bold")
    ax.set_xlabel(x_col.capitalize())
    ax.set_ylabel(y_col.capitalize())
    ax.legend()
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    
# Класс вкладки «Отчёты»

class ReportsTab:
    """
    Вкладка «Отчёты»: выбор типа графика, построение, сохранение.
 
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
        self._current_fig = None
        self.text_report_widget = None
        self.report_scrollbar = None
 
        self._build_toolbar()
        self._build_chart_area()
 
    # ── Построение интерфейса ────────────────────────────────────────
 
    def _build_toolbar(self):
        """
        Создаёт панель выбора типа графика, метрики и кнопок действий.
 
        Параметры: нет
        Возвращает: нет
        """
        toolbar = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        toolbar.pack(fill=tk.X, padx=10, pady=6)
 
        ctk.CTkLabel(
            toolbar,
            text="Визуальные отчёты",
            font=(self.app.font_family, 14, "bold"),
            text_color=self.app.accent,
        ).pack(side=tk.LEFT, padx=(0, 20))
 
        # Тип графика
        ctk.CTkLabel(toolbar, text="Тип графика:").pack(side=tk.LEFT)
        self.chart_var = tk.StringVar(value="Столбчатая диаграмма")
        chart_combo = ctk.CTkComboBox(
            toolbar,
            variable=self.chart_var,
            values=[
                "Столбчатая диаграмма",
                "Гистограмма",
                "Диаграмма Бокса–Вискера",
                "Диаграмма рассеивания",
                "Сводная таблица",
            ],
            width=200,
            state="readonly",
        )
        chart_combo.pack(side=tk.LEFT, padx=6)
 
        # Метрика
        ctk.CTkLabel(toolbar, text="Метрика:").pack(side=tk.LEFT)
        self.metric_var = tk.StringVar(value="ctr")
        metric_combo = ctk.CTkComboBox(
            toolbar,
            variable=self.metric_var,
            values=["ctr", "converted", "views"],
            width=100,
            state="readonly",
        )
        metric_combo.pack(side=tk.LEFT, padx=6)
 
        # Кнопки
        ctk.CTkButton(
            toolbar,
            text="▶  Построить",
            command=self._build_chart,
        ).pack(side=tk.LEFT, padx=8)
 
        ctk.CTkButton(
            toolbar,
            text="💾  Сохранить график",
            command=self._save_chart,
        ).pack(side=tk.RIGHT, padx=4)
 
    def _build_chart_area(self):
        """
        Создаёт область для отображения графика matplotlib.
 
        Параметры: нет
        Возвращает: нет
        """
        self.chart_frame = ctk.CTkFrame(
            self.frame,
            fg_color="white",
            border_width=1,
            border_color="#dcdde1"
        )
        self.chart_frame.pack(fill=tk.BOTH,
                              expand=True,
                              padx=10,
                              pady=(0, 10))
 
        # Заглушка до построения графика
        self.placeholder = ctk.CTkLabel(
            self.chart_frame,
            text="Выберите тип графика и нажмите «Построить»",
            text_color="#b2bec3",
            font=(self.app.font_family, 12),
        )
        self.placeholder.pack(expand=True)
 
        self.canvas = None
        self.toolbar_widget = None
 
    # Действия

    def _build_pivot(self):
        """
        Строит сводную таблицу на основе нормализованных данных.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        if self.app.sessions is None or self.app.groups is None:
            messagebox.showwarning(
                "Нет данных",
                "Данные не загружены.")
            return
        df = prepare_for_pivot(self.app.sessions, self.app.groups)
        pivot = pivot_table_report(df,
                                   index='group_name',
                                   columns=None,
                                   values='click',
                                   aggfunc='mean')
        self._show_text_report(pivot.to_string())

    def _show_text_report(self, text):
        """
        Отображает текстовый отчёт в области,
        заменяя предыдущий график/текст.

        Параметры:
            text: str - текст отчёта.

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar_widget:
            self.toolbar_widget.destroy()
            self.toolbar_widget = None
        if hasattr(self, 'text_report_widget') and self.text_report_widget:
            self.text_report_widget.destroy()
            self.text_report_widget = None
        if hasattr(self, 'report_scrollbar') and self.report_scrollbar:
            self.report_scrollbar.destroy()
            self.report_scrollbar = None
        if self.placeholder.winfo_exists():
            self.placeholder.pack_forget()
        text_widget = tk.Text(self.chart_frame,
                              font=("Courier New", 10),
                              wrap=tk.NONE)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)
        scrollbar = tk.Scrollbar(self.chart_frame,
                                 orient=tk.VERTICAL,
                                 command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT,
                         fill=tk.BOTH,
                         expand=True)
        scrollbar.pack(side=tk.RIGHT,
                       fill=tk.Y)
        self.text_report_widget = text_widget
        self.report_scrollbar = scrollbar

    def _build_chart(self):
        """
        Строит выбранный тип графика и отображает его в chart_frame.
 
        Параметры: нет
        Возвращает: нет
        """
        if self.app.current_df is None or self.app.current_df.empty:
            messagebox.showwarning(
                "Нет данных",
                "Загрузите данные перед построением графика.")
            return
 
        chart_type = self.chart_var.get()
        metric = self.metric_var.get()
 
        # Удаляем предыдущий canvas и toolbar
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar_widget:
            self.toolbar_widget.destroy()
            self.toolbar_widget = None
        if hasattr(self, 'text_report_widget') and self.text_report_widget:
            self.text_report_widget.destroy()
            self.text_report_widget = None
        if hasattr(self, 'report_scrollbar') and self.report_scrollbar:
            self.report_scrollbar.destroy()
            self.report_scrollbar = None
        if self.placeholder.winfo_exists():
            self.placeholder.pack_forget()

        if chart_type == "Сводная таблица":
            self._build_pivot()
            return

        # Строим фигуру
        fig = Figure(figsize=(8, 5), dpi=96)
        self._current_fig = fig
 
        if chart_type == "Столбчатая диаграмма":
            plot_bar(fig, self.app.current_df, metric)
        elif chart_type == "Гистограмма":
            plot_hist(fig, self.app.current_df, metric)
        elif chart_type == "Диаграмма Бокса–Вискера":
            plot_boxplot(fig, self.app.current_df, metric)
        elif chart_type == "Диаграмма рассеивания":
            plot_scatter(fig, self.app.current_df,
                         x_col="views",
                         y_col="converted")
        elif chart_type == "Сводная таблица":
            self._build_pivot()
 
        fig.tight_layout(pad=2.0)
 
        # Встраиваем в Tk
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
 
        self.toolbar_widget = NavigationToolbar2Tk(self.canvas,
                                                   self.chart_frame)
        self.toolbar_widget.update()
 
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
 
    def _save_chart(self):
        """
        Сохраняет текущий график в файл (PNG/SVG/PDF).
 
        Параметры: нет
        Возвращает: нет
        """
        if self._current_fig is None:
            messagebox.showwarning("График не построен",
                                   "Сначала постройте график.")
            return
 
        graphics_dir = self.app.cfg.get("Paths",
                                        "graphics_dir",
                                        fallback="Graphics")
        path = filedialog.asksaveasfilename(
            initialdir=graphics_dir,
            defaultextension=".png",
            filetypes=[
                ("PNG изображение", "*.png"),
                ("SVG векторный", "*.svg"),
                ("PDF документ", "*.pdf"),
            ],
        )
        if path:
            self._current_fig.savefig(path,
                                      dpi=150,
                                      bbox_inches="tight")
            messagebox.showinfo(
                "Сохранено",
                f"График сохранён:\n{path}")
