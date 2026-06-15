"""
Модуль вкладки «Данные» приложения A/B-тестирования.
 
Обеспечивает отображение загруженного датасета в виде таблицы (Treeview),
фильтрацию по группам и отображение сводной информации о датафрейме.

Автор:
    Галашина Жанна Ивановна
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox  # Добавляем для Treeview, Scrollbar


def build_treeview(parent):
    """
    Создаёт виджет Treeview со скроллбарами в заданном родительском фрейме.
 
    Параметры:
        parent (tk.Widget): родительский виджет.
    Возвращает:
        ttk.Treeview: готовый виджет таблицы.
    """
    frame = ctk.CTkFrame(parent)  # ttk.Frame -> CTkFrame
    frame.pack(fill=tk.BOTH, expand=True)
 
    v_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    h_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
 
    tree = ttk.Treeview(
        frame,
        yscrollcommand=v_scroll.set,
        xscrollcommand=h_scroll.set,
        selectmode="browse",
    )
    v_scroll.config(command=tree.yview)
    h_scroll.config(command=tree.xview)
    
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
    # Чередующиеся цвета строк
    tree.tag_configure("odd",  background="#f9f9f9")
    tree.tag_configure("even", background="#ffffff")
 
    return tree


def fill_treeview(tree, df):
    """
    Заполняет Treeview данными из датафрейма, очищая предыдущее содержимое.
 
    Параметры:
        tree (ttk.Treeview): виджет таблицы.
        df (pd.DataFrame): данные для отображения.
    Возвращает: нет
    """
    # Очистка
    for item in tree.get_children():
        tree.delete(item)
 
    if df is None or df.empty:
        return
 
    columns = list(df.columns)
    tree["columns"] = columns
    tree["show"] = "headings"
 
    for col in columns:
        tree.heading(col, text=col.upper())
        # Автоширина по названию колонки и данным
        max_width = max(len(str(col)) * 9, 80)
        tree.column(col, width=max_width, minwidth=60, anchor=tk.CENTER)

    for i, (_, row) in enumerate(df.iterrows()):
        tag = "odd" if i % 2 else "even"
        values = []
        for col in columns:
            val = row[col]
            if isinstance(val, float):
                values.append(f"{val:.4f}")
            else:
                values.append(str(val))
        tree.insert("", tk.END, values=values, tags=(tag,))


class DataTab:
    """
    Вкладка «Данные»: отображение таблицы, фильтрация, сводная информация.
    
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
        self._build_table()
        self._build_info_bar()

    def _clean_data_now(self):
        """
        Очищает уже загруженные данные от несоответствий
        группы и landing_page.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        if self.app.data is None or self.app.data.empty:
            messagebox.showwarning(
                "Нет данных",
                "Сначала загрузите данные (CSV)."
            )
            return
        from ab_logic import clean_misassignments
        confirm = messagebox.askyesno(
            "Очистка данных",
            "Вы уверены? Это удалит все записи, где группа не соответствует странице.\n"
            "Это действие нельзя отменить."
        )
        if not confirm:
            return
        df_clean, removed = clean_misassignments(self.app.data)
        if removed == 0:
            messagebox.showinfo(
                "Очистка",
                "Несоответствий не найдено. Данные не изменены."
            )
            return
        self.app.data = df_clean
        try:
            from ab_logic import normalize_to_3nf, denormalize_for_display
            (self.app.users,
                self.app.groups,
                self.app.sessions) = normalize_to_3nf(self.app.data)
            self.app.current_df = denormalize_for_display(
                self.app.groups,
                self.app.sessions)
            self.app.full_df = self.app.current_df.copy()
        except Exception as e:
            messagebox.showerror("Ошибка нормализации", str(e))
            return
        self._refresh_all_ui()
        messagebox.showinfo(
            "Очистка завершена",
            f"Удалено записей с несоответствиями: {removed}\n"
            f"Осталось записей: {len(self.app.data)}"
        )

    def _refresh_all_ui(self):
        """
        Обновляет все вкладки после изменения данных.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        self.update_table()
        if hasattr(self.app, 'analysis_tab'):
            self.app.analysis_tab.update_analysis()
        self.app.set_status(f"Данные очищены | {len(self.app.data)} записей")

    def _build_toolbar(self):
        """
        Создаёт панель инструментов с заголовком и элементами фильтрации.
 
        Параметры: нет
        Возвращает: нет
        """
        toolbar = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        toolbar.pack(fill=tk.X, padx=10, pady=6)
 
        # Заголовок вкладки
        ctk.CTkLabel(
            toolbar,
            text="Таблица данных",
            font=(self.app.font_family, 14, "bold"),
            text_color=self.app.accent,
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        # Фильтр по группе
        ctk.CTkLabel(toolbar, text="Фильтр по группе:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="Все")
        self.filter_combo = ctk.CTkComboBox(
            toolbar,
            variable=self.filter_var,
            values=["Все", "control", "treatment"],
            width=100,
            state="readonly",
            command=self._apply_filter
        )
        self.filter_combo.pack(side=tk.LEFT, padx=6)
 
        # Кнопка сброса
        ctk.CTkButton(
            toolbar,
            text="Сбросить фильтр",
            command=self._reset_filter,
        ).pack(side=tk.LEFT, padx=4)

        # Кнопка «Очистить несоответствия»
        ctk.CTkButton(
            toolbar,
            text="🧹 Очистить несоответствия",
            command=self._clean_data_now,
            fg_color="#e67e22",
            hover_color="#d35400"
        ).pack(side=tk.LEFT, padx=10)
 
        # Кнопка «Загрузить CSV»
        ctk.CTkButton(
            toolbar,
            text="📂  Загрузить CSV",
            command=self._load_csv,
        ).pack(side=tk.RIGHT, padx=4)

    def _load_csv(self):
        """Вызывает app.load_csv с параметром очистки."""
        self.app.load_csv(do_clean=False)

    def _build_table(self):
        """
        Создаёт основную таблицу Treeview для отображения данных.
 
        Параметры: нет
        Возвращает: нет
        """
        table_outer = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        table_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))
 
        # Белый фон для области таблицы
        table_bg = ctk.CTkFrame(
            table_outer,
            fg_color="white",
            border_width=1,
            border_color="#dcdde1"
        )
        table_bg.pack(fill=tk.BOTH, expand=True)
 
        self.tree = build_treeview(table_bg)
 
    def _build_info_bar(self):
        """
        Создаёт нижнюю строку с информацией о записях.
 
        Параметры: нет
        Возвращает: нет
        """
        self.info_var = tk.StringVar(value="")
        info_bar = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        info_bar.pack(fill=tk.X, padx=10, pady=(0, 6))
        ctk.CTkLabel(
            info_bar,
            textvariable=self.info_var,
            text_color="#636e72",
            font=(self.app.font_family, 9),
        ).pack(side=tk.LEFT)
      
    # Логика фильтрации

    def _apply_filter(self, event=None):
        """
        Фильтрует данные по выбранной группе и обновляет таблицу.
 
        Параметры:
            event: событие ComboboxSelected (может быть None).
        Возвращает: нет
        """
        if self.app.full_df is None:
            return
 
        val = self.filter_var.get()
        if val == "Все":
            self.app.current_df = self.app.full_df.copy()
        elif "group" in self.app.full_df.columns:
            self.app.current_df = self.app.full_df[
                self.app.full_df["group"] == val
            ].copy()
        else:
            self.app.current_df = self.app.full_df.copy()
 
        self.update_table()
        
    def _reset_filter(self):
        """
        Сбрасывает фильтр и показывает все записи.
 
        Параметры: нет
        Возвращает: нет
        """
        self.filter_var.set("Все")
        self._apply_filter()
        
    # Обновление таблицы
 
    def update_table(self):
        """
        Перерисовывает таблицу на основе self.app.current_df.
 
        Параметры: нет
        Возвращает: нет
        """
        fill_treeview(self.tree, self.app.current_df)
 
        # Обновляем инфо-строку
        if (self.app.current_df is not None
                and not self.app.current_df.empty):
            total = len(self.app.data) \
                if self.app.data is not None else 0
            shown = len(self.app.current_df)
            cols = len(self.app.current_df.columns)
            self.info_var.set(
                f"Показано {shown} из {total} записей  |  Столбцов: {cols}"
            )
        else:
            self.info_var.set("Нет данных")
