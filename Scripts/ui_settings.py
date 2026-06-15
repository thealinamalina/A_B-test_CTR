"""
Модуль диалогового окна настроек интерфейса.

Позволяет пользователю редактировать параметры интерфейса
(цвета, шрифт, размер)
и сохранять их в конфигурационный файл settings.ini.

Автор:
    Галашина Жанна Ивановна
"""

import tkinter as tk
from tkinter import colorchooser, messagebox
from typing import Optional
import customtkinter as ctk

# Вспомогательные функции

def save_config(cfg, path="config.ini"):
    """
    Записывает объект конфигурации в файл .ini.

    Параметры:
        cfg (configparser.ConfigParser): объект конфигурации.
        path (str): путь к файлу.
    Возвращает: нет
    """
    with open(path, "w", encoding="utf-8") as fh:
        cfg.write(fh)


def pick_color(parent, initial="#ffffff") -> Optional[str]:
    """
    Открывает диалог выбора цвета и возвращает выбранный hex-код.

    Параметры:
        parent (tk.Widget): родительское окно.
        initial (str): начальный цвет в hex-формате.
    Возвращает:
        str | None: выбранный цвет или None, если отменено.
    """
    result = colorchooser.askcolor(color=initial, parent=parent)
    if result and result[1]:
        return result[1]
    return None


# Класс диалога настроек

class SettingsDialog:
    """
    Модальное окно настроек интерфейса.

    Показывает текущие параметры из settings.ini, позволяет их изменить
    и сохранить (с перезапуском для применения изменений).

    Параметры:
        parent (tk.Widget): родительское окно.
        app (ABTestApp): ссылка на главный объект приложения.
    Возвращает: нет
    """

    def __init__(self, parent, app):
        """
        Инициализация: создаёт модальное диалоговое окно.

        Параметры:
            parent (tk.Widget): родительское окно.
            app (ABTestApp): главный объект приложения.
        Возвращает: нет
        """
        self.app = app
        self.cfg = app.cfg

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Настройки интерфейса")
        self.dialog.geometry("500x550")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Модальный режим

        self._build_ui()

    # Построение интерфейса

    def _build_ui(self):
        """
        Создаёт поля редактирования параметров и кнопки
        «Сохранить» / «Отмена».

        Параметры: нет
        Возвращает: нет
        """
        # Получаем секции конфига (с учётом регистра)
        iface = self.cfg["Interface"] if "Interface" in self.cfg \
            else {}
        analysis_cfg = self.cfg["Analysis"] if "Analysis" in self.cfg \
            else {}
        paths_cfg = self.cfg["Paths"] if "Paths" in self.cfg else {}

        # Основной фрейм с прокруткой
        main_frame = ctk.CTkScrollableFrame(
            self.dialog, width=460, height=480)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Заголовок
        ctk.CTkLabel(
            main_frame,
            text="Параметры интерфейса",
            font=(self.app.font_family, 16, "bold"),
        ).pack(anchor=tk.W, pady=(0, 14))

        # Описания параметров и их ключи
        # Поля секции [Interface]
        iface_fields = [
            ("Шрифт:", "font_family", "entry"),
            ("Размер шрифта:", "font_size", "entry"),
            ("Цвет фона:", "bg_color", "color"),
            ("Цвет акцента:", "accent_color", "color"),
            ("Цвет боковой панели:", "sidebar_bg", "color"),
            ("Цвет шапки:", "header_bg", "color"),
        ]

        # Секция [Analysis] — параметры расчётов
        analysis_fields = [
            ("Уровень доверия (0.90–0.99):",
             "confidence_level",
             "entry"),
            ("Тест по умолчанию (ttest):",
             "default_test",
             "entry"),
        ]

        # Секция [Paths]
        paths_fields = [
            ("Папка данных:",
             "data_dir",
             "entry"),
            ("Папка графиков:",
             "graphics_dir",
             "entry"),
            ("Папка отчётов:",
             "output_dir",
             "entry"),
        ]

        self.vars = {}  # {key: StringVar} — все секции
        self.section_map = {}  # {key: section_name}
        self.color_frames = {}  # {key: CTkFrame} для обновления цвета

        # ── [Interface] ──
        ctk.CTkLabel(
            main_frame,
            text="Интерфейс [Interface]",
            font=(self.app.font_family, 12, "bold"),
            text_color="#636e72"
        ).pack(anchor=tk.W, pady=(8, 4))

        for label, key, widget_type in iface_fields:
            current = iface.get(key, "")
            var = tk.StringVar(value=current)
            self.vars[key] = var
            self.section_map[key] = "Interface"

            # Строка параметра
            row_frame = ctk.CTkFrame(main_frame,
                                     fg_color="transparent")
            row_frame.pack(fill=tk.X, pady=4)

            ctk.CTkLabel(row_frame,
                         text=label,
                         width=140).pack(side=tk.LEFT, padx=(0, 8))

            if widget_type == "entry":
                entry = ctk.CTkEntry(row_frame,
                                     textvariable=var,
                                     width=200)
                entry.pack(side=tk.LEFT)
            elif widget_type == "color":
                # Фрейм для отображения цвета
                color_frame = ctk.CTkFrame(
                    row_frame,
                    fg_color=current or "#ffffff",
                    width=30,
                    height=24)
                color_frame.pack(side=tk.LEFT, padx=(0, 8))
                color_frame.bind("<Button-1>",
                                 lambda e, k=key, cf=color_frame:
                                 self._pick(k, cf))
                self.color_frames[key] = color_frame

                # Поле для ввода hex-кода
                entry = ctk.CTkEntry(row_frame,
                                     textvariable=var,
                                     width=120)
                entry.pack(side=tk.LEFT)
                entry.bind("<KeyRelease>",
                           lambda e, k=key, cf=color_frame:
                           self._update_color_preview(k, cf))

        # ── [Analysis] ──
        ctk.CTkLabel(
            main_frame,
            text="Анализ [Analysis]",
            font=(self.app.font_family, 12, "bold"),
            text_color="#636e72"
        ).pack(anchor=tk.W, pady=(12, 4))

        for label, key, widget_type in analysis_fields:
            current = analysis_cfg.get(key, "")
            var = tk.StringVar(value=current)
            self.vars[key] = var
            self.section_map[key] = "Analysis"

            row_frame = ctk.CTkFrame(main_frame,
                                     fg_color="transparent")
            row_frame.pack(fill=tk.X, pady=4)

            ctk.CTkLabel(row_frame,
                         text=label,
                         width=200).pack(side=tk.LEFT, padx=(0, 8))
            entry = ctk.CTkEntry(row_frame,
                                 textvariable=var,
                                 width=160)
            entry.pack(side=tk.LEFT)

        # ── [Paths] ──
        ctk.CTkLabel(
            main_frame,
            text="Пути [Paths]",
            font=(self.app.font_family, 12, "bold"),
            text_color="#636e72"
        ).pack(anchor=tk.W, pady=(12, 4))

        for label, key, widget_type in paths_fields:
            current = paths_cfg.get(key, "")
            var = tk.StringVar(value=current)
            self.vars[key] = var
            self.section_map[key] = "Paths"

            row_frame = ctk.CTkFrame(main_frame,
                                     fg_color="transparent")
            row_frame.pack(fill=tk.X, pady=4)

            ctk.CTkLabel(row_frame,
                         text=label,
                         width=140).pack(side=tk.LEFT, padx=(0, 8))
            entry = ctk.CTkEntry(row_frame,
                                 textvariable=var,
                                 width=200)
            entry.pack(side=tk.LEFT)

        # Разделитель
        ctk.CTkFrame(main_frame, height=1,
                     fg_color="#dcdde1").pack(fill=tk.X, pady=16)

        # Информационная метка
        ctk.CTkLabel(
            main_frame,
            text="* Изменения применятся после перезапуска приложения.",
            text_color="#636e72",
            font=(self.app.font_family, 9),
        ).pack(anchor=tk.W, pady=(0, 12))

        # Кнопки
        btn_frame = ctk.CTkFrame(main_frame,
                                 fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=8)

        ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=self.dialog.destroy,
            width=100,
        ).pack(side=tk.RIGHT, padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=self._save,
            width=100,
        ).pack(side=tk.RIGHT, padx=4)

    # ── Действия ────────────────────────────────────────────────────

    def _pick(self, key, color_frame):
        """
        Открывает диалог выбора цвета и
        обновляет соответствующую переменную.

        Параметры:
            key (str): ключ параметра в словаре self.vars.
            color_frame (ctk.CTkFrame):
            фрейм-образец цвета для обновления.
        Возвращает: нет
        """
        current = self.vars[key].get()
        chosen = pick_color(self.dialog,
                            initial=current or "#ffffff")
        if chosen is not None:
            self.vars[key].set(chosen)
            color_frame.configure(fg_color=chosen)

    def _update_color_preview(self, key, color_frame):
        """
        Обновляет цвет фрейма-образца при вводе hex-кода вручную.

        Параметры:
            key (str): ключ параметра.
            color_frame (ctk.CTkFrame): фрейм-образец цвета.
        Возвращает: нет
        """
        value = self.vars[key].get().strip()
        # Простая проверка на hex-код
        if value.startswith("#") and len(value) in (4, 7):
            try:
                color_frame.configure(fg_color=value)
            except Exception:
                pass

    def _save(self):
        """
        Сохраняет изменённые параметры в конфигурационный файл.

        Параметры: нет
        Возвращает: нет
        """
        # Убеждаемся, что секции существуют
        if "Interface" not in self.cfg:
            self.cfg["Interface"] = {}
        if "Analysis" not in self.cfg:
            self.cfg["Analysis"] = {}
        if "Paths" not in self.cfg:
            self.cfg["Paths"] = {}

        for key, var in self.vars.items():
            value = var.get().strip()
            if value:
                section = self.section_map.get(key, "Interface")
                if section not in self.cfg:
                    self.cfg[section] = {}
                self.cfg[section][key] = value

        save_config(self.cfg)
        messagebox.showinfo(
            "Сохранено",
            "Настройки сохранены в config.ini.\n"
            "Перезапустите приложение для применения изменений."
        )
        self.dialog.destroy()
