"""
Модуль вкладки «Справочники» для управления справочниками.
Обеспечивает CRUD-операции и бинарное сохранение/загрузку.

Автор: Лукьянова Алина Павловна
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Library"))
from data_io import save_pickle, load_pickle
from ab_logic import denormalize_for_display


class ReferencesTab:
    """
    Вкладка «Справочники» для управления справочниками.

    Обеспечивает CRUD-операции (создание, чтение, обновление, удаление)
    и бинарное сохранение/загрузку справочников.

    Автор:
        Лукьянова Алина Павловна
    """
    def __init__(self, parent, app):
        """
        Инициализация вкладки справочников.

        Параметры:
            parent: tk.Widget - родительский контейнер.
            app: ABTestApp - ссылка на объект приложения.

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """

        self.app = app
        self.frame = ctk.CTkFrame(parent, fg_color="#f5f6fa")
        self.current_ref_name = "users"
        self.current_ref_df = pd.DataFrame()
        self.text_report_widget = None
        self.report_scrollbar = None

        self._build_toolbar()
        self._build_table()
        self._refresh()

    def _build_toolbar(self):
        """
        Создаёт панель инструментов для управления справочниками.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        toolbar = ctk.CTkFrame(self.frame,
                               fg_color="#f5f6fa")
        toolbar.pack(fill=tk.X, padx=10, pady=6)
        ctk.CTkLabel(toolbar,
                     text="Справочник:",
                     font=(self.app.font_family, 12)).pack(side=tk.LEFT)
        self.ref_combo = ctk.CTkComboBox(
            toolbar,
            values=["users", "groups"],
            state="readonly",
            width=100,
            command=self._on_ref_change
        )
        self.ref_combo.pack(side=tk.LEFT, padx=6)
        self.ref_combo.set("users")
        ctk.CTkButton(toolbar,
                      text="Сохранить в бинарный файл",
                      command=self._save_binary).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(toolbar, text="Загрузить из бинарного файла",
                      command=self._load_binary).pack(side=tk.LEFT, padx=4)

        btn_frame = ctk.CTkFrame(self.frame, fg_color="#f5f6fa")
        btn_frame.pack(fill=tk.X, padx=10, pady=6)
        ctk.CTkButton(btn_frame, text="Добавить запись",
                      command=self._add_record).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(btn_frame, text="Редактировать запись",
                      command=self._edit_record).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(btn_frame, text="Удалить запись",
                      command=self._delete_record).pack(side=tk.LEFT, padx=4)

    def _build_table(self):
        """
        Создаёт таблицу Treeview для отображения записей справочника.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        table_frame = ctk.CTkFrame(self.frame, fg_color="white",
                                   border_width=1, border_color="#dcdde1")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        from ui_data import build_treeview
        self.tree = build_treeview(table_frame)

    def _on_ref_change(self, choice):
        """
        Обрабатывает изменение выбранного справочника в выпадающем списке.
        Обновляет внутреннее имя текущего справочника и перезагружает
        отображаемые данные.

        Параметры:
            choice: str - название выбранного справочника ('users' или 'groups').

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        self.current_ref_name = choice
        self._refresh()

    def _refresh(self):
        """
        Обновляет содержимое таблицы в соответствии с текущим справочником.

        Загружает данные из app.users или app.groups, копирует их в
        current_ref_df и перерисовывает таблицу через fill_treeview.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        if self.current_ref_name == "users":
            self.current_ref_df = self.app.users.copy() \
                if self.app.users is not None else pd.DataFrame()
        else:
            self.current_ref_df = self.app.groups.copy() \
                if self.app.groups is not None else pd.DataFrame()
        from ui_data import fill_treeview
        fill_treeview(self.tree, self.current_ref_df)

    def _save_binary(self):
        """
        Сохраняет текущий справочник в бинарный файл формата pickle.

        Открывает диалог сохранения с предложением имени файла по умолчанию.
        При успешном сохранении показывает информационное сообщение.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        if self.current_ref_df.empty:
            messagebox.showwarning("Нет данных",
                                   "Справочник пуст, сохранять нечего.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")],
            initialfile=f"{self.current_ref_name}.pkl"
        )
        if path:
            save_pickle(self.current_ref_df, path)
            messagebox.showinfo(
                "Сохранено",
                f"Справочник '{self.current_ref_name}' сохранён в {path}")

    def _load_binary(self):
        """
        Загружает справочник из бинарного файла формата pickle.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        path = filedialog.askopenfilename(
            filetypes=[("Pickle files", "*.pkl")])
        if not path:
            return
        df = load_pickle(path)
        if self.current_ref_name == "users":
            self.app.users = df
        else:
            self.app.groups = df
        self.current_ref_df = df
        self._refresh()
        if self.app.sessions is not None:
            self.app.current_df = (
                denormalize_for_display(self.app.groups, self.app.sessions))
            if hasattr(self.app.data_tab, "update_table"):
                self.app.data_tab.update_table()
        messagebox.showinfo("Загружено",
                            f"Справочник '{self.current_ref_name}' загружен.")

    def _add_record(self):
        """
        Добавляет новую запись в выбранный справочник.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        if self.current_ref_name == "users":
            new_id = simpledialog.askinteger("Добавить пользователя",
                                             "Введите новый user_id:",
                                             parent=self.frame)
            if new_id is not None and new_id > 0:
                # Проверка, нет ли уже такого ID
                if self.current_ref_df['user_id'].isin([new_id]).any():
                    messagebox.showerror("Ошибка",
                                         f"user_id {new_id} уже существует.")
                    return
                new_row = pd.DataFrame({'user_id': [new_id]})
                self.current_ref_df = pd.concat([self.current_ref_df, new_row],
                                                ignore_index=True)
        else:  # groups
            group_name = simpledialog.askstring(
                "Добавить группу",
                "Введите название группы (control/treatment):",
                parent=self.frame)
            if group_name and group_name.strip():
                # Не допускаем дубликатов названий групп
                if group_name in self.current_ref_df['group_name'].values:
                    messagebox.showerror(
                        "Ошибка",
                        f"Группа '{group_name}' уже существует.")
                    return
                new_id = self.current_ref_df['group_id'].max() + 1 \
                    if not self.current_ref_df.empty else 1
                new_row = pd.DataFrame({'group_id': [new_id],
                                        'group_name': [group_name.strip()]})
                self.current_ref_df = pd.concat([self.current_ref_df, new_row],
                                                ignore_index=True)

        # Сохраняем в приложение
        if self.current_ref_name == "users":
            self.app.users = self.current_ref_df
        else:
            self.app.groups = self.current_ref_df
        self._refresh()
        if self.app.sessions is not None:
            self.app.current_df = denormalize_for_display(self.app.groups,
                                                          self.app.sessions)
            if hasattr(self.app.data_tab, "update_table"):
                self.app.data_tab.update_table()

    def _edit_record(self):
        """
        Редактирует выбранную запись в справочнике.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Нет выбора",
                                   "Выберите запись для редактирования.")
            return
        values = self.tree.item(selected[0], 'values')
        if not values:
            return

        if self.current_ref_name == "users":
            old_id = int(values[0])  # user_id
            new_id = simpledialog.askinteger("Редактировать",
                                             "Новый user_id:",
                                             initialvalue=old_id,
                                             parent=self.frame)
            if new_id is not None and new_id > 0 and new_id != old_id:
                # Проверка уникальности
                if self.current_ref_df['user_id'].isin([new_id]).any():
                    messagebox.showerror("Ошибка",
                                         f"user_id {new_id} уже существует.")
                    return
                self.current_ref_df.loc[self.current_ref_df['user_id']
                                        == old_id, 'user_id'] \
                    = new_id
            else:
                return
        else:  # groups
            old_name = values[1]
            new_name = simpledialog.askstring(
                "Редактировать",
                "Новое название группы:",
                initialvalue=old_name, parent=self.frame)
            if new_name and new_name.strip() and new_name != old_name:
                # Проверка уникальности названия
                if new_name in self.current_ref_df['group_name'].values:
                    messagebox.showerror(
                        "Ошибка",
                        f"Группа '{new_name}' уже существует.")
                    return
                self.current_ref_df.loc[self.current_ref_df['group_name']
                                        == old_name, 'group_name'] \
                    = new_name.strip()
            else:
                return

        if self.current_ref_name == "users":
            self.app.users = self.current_ref_df
        else:
            self.app.groups = self.current_ref_df
        self._refresh()
        if self.app.sessions is not None:
            self.app.current_df = denormalize_for_display(self.app.groups,
                                                          self.app.sessions)
            if hasattr(self.app.data_tab, "update_table"):
                self.app.data_tab.update_table()

    def _delete_record(self):
        """
        Удаляет выбранную запись из справочника.

        Параметры:
            None

        Возвращаемое значение:
            None

        Автор:
            Лукьянова Алина Павловна
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Нет выбора",
                                   "Выберите запись для удаления.")
            return
        values = self.tree.item(selected[0], 'values')
        if not values:
            return

        # Для групп проверим, не используется ли группа в сессиях
        if self.current_ref_name == "groups":
            group_name = values[1]
            if self.app.sessions is not None and self.app.groups is not None:
                group_id = (
                    self.current_ref_df.loc[self.current_ref_df['group_name']
                                            == group_name, 'group_id'].values)
                if len(group_id) > 0 and (self.app.sessions['group_id']
                                          == group_id[0]).any():
                    if not messagebox.askyesno("Предупреждение",
                                               f"Группа '{group_name}' используется в данных сессий.\n"
                                               "Вы уверены, что хотите удалить?"):
                        return

        if not messagebox.askyesno(
                "Подтверждение",
                f"Удалить выбранную запись из справочника '{self.current_ref_name}'?"):
            return

        if self.current_ref_name == "users":
            user_id = int(values[0])
            self.current_ref_df = (
                self.current_ref_df[self.current_ref_df['user_id']
                                    != user_id].reset_index(drop=True))
        else:
            group_name = values[1]
            self.current_ref_df = (
                self.current_ref_df[self.current_ref_df['group_name']
                                    != group_name].reset_index(drop=True))

        if self.current_ref_name == "users":
            self.app.users = self.current_ref_df
        else:
            self.app.groups = self.current_ref_df
        self._refresh()
        if self.app.sessions is not None:
            self.app.current_df = denormalize_for_display(self.app.groups,
                                                          self.app.sessions)
            if hasattr(self.app.data_tab, "update_table"):
                self.app.data_tab.update_table()
