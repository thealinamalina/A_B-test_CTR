import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import configparser
import os
import numpy as np
import pandas as pd
import customtkinter as ctk

from ui_data import DataTab
from ui_analysis import AnalysisTab
from ui_reports import ReportsTab
from ui_settings import SettingsDialog
from ui_references import ReferencesTab
from ab_logic import normalize_to_3nf, denormalize_for_display


def load_config(path="config.ini"):
    """
    Читает конфигурационный файл config.ini.

    Секции файла: [Interface], [Paths], [Analysis].
    ConfigParser читает секции без учёта регистра ключей,
    но сохраняет исходный регистр названий секций.

    Параметры:
        path (str): путь к файлу конфигурации.
    Возвращает:
        configparser.ConfigParser: объект конфигурации.

    Автор:
        Галашина Жанна Ивановна
    """
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg


def ensure_dirs(cfg):
    """
        Создаёт необходимые папки проекта, если они отсутствуют.

        Читает пути из секции [Paths] файла config.ini.

        Параметры:
            cfg (configparser.ConfigParser): объект конфигурации.
        Возвращает: нет
    """
    for key in ("data_dir", "graphics_dir", "output_dir"):
        folder = cfg.get("Paths", key, fallback=key)
        os.makedirs(folder, exist_ok=True)


def generate_sample_data(n_users=200, seed=42):
    """
        Генерирует случайный демонстрационный датасет A/B-теста.

        Параметры:
            n_users (int): количество пользователей.
            seed (int): зерно генератора случайных чисел.
        Возвращает:
            pd.DataFrame: датафрейм с колонками user_id, group,
             clicks, views, ctr.
    """
    rng = np.random.default_rng(seed)
    groups = (["control"] * (n_users // 2) + ["treatment"] *
              (n_users - n_users // 2))
    clicks = rng.integers(0, 25, n_users)
    views = rng.integers(50, 200, n_users)
    df = pd.DataFrame({
        "user_id": range(1, n_users + 1),
        "group": groups,
        "converted": clicks,
        "views": views,
    })
    df["ctr"] = (df["converted"] / df["views"]).round(4)
    return df


"""
    Главный класс приложения A/B-тестирования.

    Управляет созданием окна, боковой панелью навигации,
    рабочей областью (фреймы вкладок) и общими данными.

    Параметры: нет
    Возвращает: нет
"""


class ABTestApp:
    """
        Инициализация: читает конфигурацию, строит интерфейс,
        загружает демонстрационные данные.

        Параметры: нет
        Возвращает: нет
    """

    def __init__(self):
        # Настройка внешнего вида CustomTkinter
        ctk.set_appearance_mode("light")  # "light", "dark", "system"
        ctk.set_default_color_theme("blue")

        # читаем config.ini
        self.cfg = load_config()
        ensure_dirs(self.cfg)

        # Параметры внешнего вида, секция interface
        iface = self.cfg["Interface"] if "Interface" in self.cfg \
            else {}
        self.bg_color = iface.get("bg_color", "#f0f0f0")
        self.font_family = iface.get("font_family", "Arial")
        self.font_size = int(iface.get("font_size", "10"))
        # Дополнительные цвета: если не заданы в config.ini,
        # берём по умолчанию
        self.sidebar_bg = iface.get("sidebar_bg", "#2c3e50")
        self.sidebar_fg = iface.get("sidebar_fg", "#ecf0f1")
        self.sidebar_abg = iface.get("sidebar_active_bg", "#3498db")
        self.accent = iface.get("accent_color", "#4a90d9")
        self.header_bg = iface.get("header_bg", "#34495e")
        self.header_fg = iface.get("header_fg", "#ffffff")

        # Секция [Analysis] — параметры статистического анализа
        analysis = self.cfg["Analysis"] if "Analysis" in self.cfg \
            else {}
        self.confidence_level = float(
            analysis.get("confidence_level", "0.95"))
        self.default_test = analysis.get("default_test", "ttest")

        # Общие данные
        self.data = None  # исходный DataFrame
        self.current_df = None  # отфильтрованный DataFrame
        self.users = None
        self.groups = None
        self.sessions = None
        self.full_df = None

        # Создание окна CustomTkinter
        self.root = ctk.CTk()
        self._setup_window()
        self._apply_styles()
        self._build_layout()

        # Загрузка демо-данных
        self._load_sample_data()

    # ── Настройка окна

    def _setup_window(self):
        """Задаёт заголовок, размер и минимальный размер окна."""
        title = "A/B-тестирование — анализ кликабельности (CTR)"
        width = 1280
        height = 750
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(900, 600)

    def _apply_styles(self):
        """
        Настраивает стили ttk-виджетов в соответствии
        с конфигурацией.
        """
        style = ttk.Style(self.root)
        theme = self.cfg.get("Interface", "theme", fallback="clam")
        if theme in style.theme_names():
            style.theme_use(theme)

        font_normal = (self.font_family, self.font_size)
        font_bold = (self.font_family, self.font_size, "bold")

        style.configure("TLabel",
                        font=font_normal)
        style.configure("TButton",
                        font=font_normal)
        style.configure("TCombobox",
                        font=font_normal)
        style.configure("Treeview",
                        font=font_normal,
                        rowheight=22)
        style.configure("Treeview.Heading",
                        font=font_bold,
                        background=self.header_bg,
                        foreground=self.header_fg)
        style.configure("Header.TLabel",
                        font=(self.font_family, 14, "bold"),
                        foreground=self.accent)
        style.configure("Accent.TButton",
                        font=font_bold)

    def _build_layout(self):
        """Создаёт верхнее меню, шапку и основную часть."""
        self._build_menu()
        self._build_header()
        self._build_body()

    def _build_menu(self):
        """Создаёт верхнее меню (Файл, Настройки, Справка)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню «Файл»
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Загрузить данные (CSV)…",
                              command=self.load_csv)
        file_menu.add_command(label="Сохранить данные…",
                              command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход",
                              command=self.root.quit)

        # Меню «Настройки»
        settings_menu = tk.Menu(menubar,
                                tearoff=0)
        menubar.add_cascade(label="Настройки",
                            menu=settings_menu)
        settings_menu.add_command(label="Параметры интерфейса…",
                                  command=self.open_settings)

        # Меню «Справка»
        help_menu = tk.Menu(menubar,
                            tearoff=0)
        menubar.add_cascade(label="Справка",
                            menu=help_menu)
        help_menu.add_command(label="О программе",
                              command=self._show_about)

    def _build_header(self):
        """Создаёт горизонтальную шапку с заголовком приложения."""
        hdr = ctk.CTkFrame(self.root,
                           fg_color=self.header_bg,
                           height=48)
        hdr.pack(side=tk.TOP,
                 fill=tk.X)
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr,
            text="A/B-тестирование — анализ кликабельности (CTR)",
            text_color=self.header_fg,
            font=(self.font_family, 13, "bold"),
        ).pack(side=tk.LEFT,
               padx=10,
               pady=8)

        self.status_var = tk.StringVar(value="Данные не загружены")
        ctk.CTkLabel(
            hdr,
            textvariable=self.status_var,
            text_color="#bdc3c7",
            font=(self.font_family, 9),
        ).pack(side=tk.RIGHT, padx=14)

    def _build_body(self):
        """
        Создаёт боковую панель навигации и рабочую
        область со стековыми фреймами.
        """
        body = ctk.CTkFrame(self.root,
                            fg_color="#f5f6fa")
        body.pack(fill=tk.BOTH,
                  expand=True)

        # ── Боковая панель ──
        sidebar = ctk.CTkFrame(body,
                               fg_color=self.sidebar_bg,
                               width=180)
        sidebar.pack(side=tk.LEFT,
                     fill=tk.Y)
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="НАВИГАЦИЯ",
            text_color="#7f8c8d",
            font=(self.font_family, 8, "bold"),
        ).pack(pady=(18, 4))

        # Рабочая область
        self.work_area = ctk.CTkFrame(body,
                                      fg_color="#f5f6fa")
        self.work_area.pack(side=tk.LEFT,
                            fill=tk.BOTH,
                            expand=True)

        # Создаём вкладки-фреймы
        self.data_tab = DataTab(self.work_area, self)
        self.analysis_tab = AnalysisTab(self.work_area, self)
        self.reports_tab = ReportsTab(self.work_area, self)
        self.references_tab = ReferencesTab(self.work_area, self)

        self.frames = {
            "data": self.data_tab.frame,
            "analysis": self.analysis_tab.frame,
            "reports": self.reports_tab.frame,
            "references": self.references_tab.frame,
        }

        # Все фреймы занимают одно место
        for frame in self.frames.values():
            frame.place(relx=0,
                        rely=0,
                        relwidth=1,
                        relheight=1)

        # Кнопки боковой панели (CustomTkinter)
        nav_items = [
            ("Данные", "data"),
            ("Анализ", "analysis"),
            ("Отчёты", "reports"),
            ("Справочники", "references"),
        ]

        self._nav_buttons = {}
        for label, key in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=label,
                fg_color=self.sidebar_bg,
                text_color=self.sidebar_fg,
                hover_color=self.sidebar_abg,
                corner_radius=0,
                anchor="w",
                height=40,
                font=(self.font_family, self.font_size),
                cursor="hand2",
                command=lambda k=key: self.show_frame(k),
            )
            btn.pack(fill=tk.X, padx=4, pady=1)
            self._nav_buttons[key] = btn

        # По умолчанию показываем «Данные»
        self.show_frame("data")

    def show_frame(self, key):
        """
        Отображает нужный фрейм и подсвечивает
         активную кнопку в боковой панели.
        """
        self.frames[key].lift()
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=self.sidebar_abg,
                              text_color="#ffffff",
                              font=(self.font_family,
                                    self.font_size, "bold"))
            else:
                btn.configure(fg_color=self.sidebar_bg,
                              text_color=self.sidebar_fg,
                              font=(self.font_family,
                                    self.font_size))

    def load_csv(self, do_clean=False):
        """
        Открывает диалог выбора CSV-файла,
        загружает данные и обновляет интерфейс.

        Параметры:
            do_clean (bool): если True, удаляются записи с
            несоответствием group-landing_page.
        """
        print("DEBUG: load_csv called, do_clean =", do_clean)
        path = filedialog.askopenfilename(
            title="Открыть CSV-файл",
            filetypes=[("CSV файлы", "*.csv"),
                       ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            df = pd.read_csv(path)
            if 'landing_page' in df.columns:
                print("DEBUG: landing_page exists")
                print("DEBUG: unique landing_page values:", df['landing_page'].unique())
            else:
                print("DEBUG: landing_page NOT found")

            # Если нет колонки views, то создаём со значением 1
            if 'views' not in df.columns:
                df['views'] = 1

            # Очистка от несоответствий (если запрошено)
            removed = 0
            if do_clean:
                from ab_logic import clean_misassignments
                df_clean, removed = clean_misassignments(df)
                print("DEBUG: removed =", removed)
            else:
                df_clean = df.copy()
                removed = 0

            if removed:
                print("DEBUG: about to show warning, removed =", removed)
                msg = f"Удалено {removed} записей с несоответствием группы и показанной страницы."
                messagebox.showwarning("Очистка данных", msg)

            # Вычисляем CTR, если колонок хватает
            if ("clicks" in df_clean.columns and
                    "views" in df_clean.columns):
                df_clean["ctr"] = (df_clean["clicks"] /
                                   df_clean["views"]).round(4)
            elif ("converted" in df_clean.columns
                  and "views" in df_clean.columns):
                df_clean["ctr"] = (df_clean["converted"] /
                                   df_clean["views"]).round(4)
            self.data = df_clean
            try:
                self.users, self.groups, self.sessions = normalize_to_3nf(self.data)
                self.current_df = denormalize_for_display(self.groups, self.sessions)
                self.full_df = self.current_df.copy()
            except Exception as e:
                messagebox.showerror("Ошибка нормализации", str(e))
                return
            self._refresh_all()
            clean_info = f" (очистка: {'да' if do_clean else 'нет'})"
            self.set_status(
                f"Загружено: {os.path.basename(path)} | {len(df_clean)} записей{clean_info}"
            )
        except Exception as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))

    def save_data(self):
        """
        Открывает диалог сохранения и записывает текущий
        датафрейм в CSV.
        """
        if self.current_df is None:
            messagebox.showwarning("Нет данных",
                                   "Нечего сохранять.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv")],
        )
        if path:
            self.current_df.to_csv(path, index=False)
            messagebox.showinfo("Сохранено",
                                f"Файл сохранён:\n{path}")

    def open_settings(self):
        """Открывает диалог настроек интерфейса."""
        SettingsDialog(self.root, self)

    def _show_about(self):
        """Показывает окно «О программе»."""
        messagebox.showinfo(
            "О программе",
            "A/B-тестирование — анализ кликабельности (CTR)\n\n"
            "Учебный проект, ВШЭ ШИФТ 2026\n"
            "Курс «Проектный семинар: Python в науке о данных»",
        )

    # Вспомогательные методы

    def _load_sample_data(self):
        """Загружает демонстрационные данные при запуске приложения."""
        self.data = generate_sample_data()
        try:
            (self.users,
             self.groups,
             self.sessions) = normalize_to_3nf(self.data)
            self.current_df = denormalize_for_display(
                self.groups,
                self.sessions)
            self.full_df = self.current_df.copy()
        except Exception as e:
            messagebox.showerror("Ошибка нормализации демо-данных",
                                 str(e))
            return
        self._refresh_all()
        self.set_status(
            f"Демо-данные загружены  |  {len(self.data)} записей"
        )

    def _refresh_all(self):
        """
        Обновляет отображение во всех вкладках после
        изменения данных.
        """
        if hasattr(self.data_tab, "update_table"):
            self.data_tab.update_table()
        if hasattr(self.analysis_tab, "update_analysis"):
            self.analysis_tab.update_analysis()
        # Обновление справочников не требуется при загрузке данных

    def set_status(self, text):
        """Устанавливает текст в строке статуса шапки."""
        self.status_var.set(text)

    def run(self):
        """Запускает главный цикл событий Tk."""
        self.root.mainloop()
