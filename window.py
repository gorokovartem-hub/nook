"""Минималистичное главное окно + виджет на таскбаре."""
import customtkinter as ctk
from tkinter import colorchooser, messagebox, simpledialog

from features import monitor, notes as notes_mod
from features.pomodoro import Pomodoro
from features.clipboard import ClipboardWatcher
from taskbar_widget import TaskbarWidget, load_config, save_config
import theme
from theme import (
    BG, BG_SOFT, CARD, CARD_HOVER, LINE, FG, FG_DIM, FG_FAINT, GOOD,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_MONO,
    setup_appearance, divider, card, progress_bar, level_color,
    flat_button, line_button, primary_button,
)

WIN_W, WIN_H = 980, 660


class MetricCard:
    """Карточка системного показателя."""

    def __init__(self, parent, label, show_bar=True):
        self.frame = card(parent)
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            inner, text=label.upper(), font=("Segoe UI Semibold", 10),
            text_color=FG_DIM, anchor="w",
        ).pack(fill="x")
        self.value = ctk.CTkLabel(inner, text="—", font=("Segoe UI Light", 36),
                                  text_color=FG, anchor="w")
        self.value.pack(fill="x", pady=(8, 6))
        self.bar = progress_bar(inner) if show_bar else None
        if self.bar:
            self.bar.set(0)
            self.bar.pack(fill="x")
        self.sub = ctk.CTkLabel(inner, text=" ", font=FONT_SMALL,
                                text_color=FG_DIM, anchor="w")
        self.sub.pack(fill="x", pady=(10 if show_bar else 2, 0))

    def update(self, text, pct=None, sub=" ", color=None):
        self.value.configure(text=text)
        self.sub.configure(text=sub)
        if self.bar is None:
            return
        if pct is None:
            self.bar.set(0)
        else:
            self.bar.set(max(0, min(1, pct / 100)))
            self.bar.configure(progress_color=color or FG)


class MainWindow:
    def __init__(self, on_hide_to_tray, clipboard: ClipboardWatcher):
        setup_appearance()
        self.on_hide = on_hide_to_tray
        self.clipboard = clipboard
        self.pomodoro = Pomodoro(on_tick=self._update_pomodoro_ui)
        self._toast_job = None
        self.desktop_widget = None
        self._quick_notes_window = None
        self._theme_save_job = None
        self.theme_settings = theme.get_settings()

        self.root = ctk.CTk()
        self.root.title("Nook")
        self._center(WIN_W, WIN_H)
        self.root.minsize(820, 560)
        self.root.configure(fg_color=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        # Виджет на таскбаре (Toplevel поверх главного Tk)
        self.taskbar_widget = TaskbarWidget(self.root)

        self._build()
        self._bind_keys()
        self._show("studio")
        self._refresh_monitor()

    def _center(self, w, h):
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 3
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _bind_keys(self):
        for i, key in enumerate(self.nav_keys, start=1):
            self.root.bind(f"<Control-Key-{i}>", lambda e, k=key: self._show(k))
        self.root.bind("<Escape>", lambda e: self.hide())
        self.root.bind("<<NookQuickNote>>", lambda _event: self.show_quick_note())

    # ---------- Каркас ----------
    def _build(self):
        shell = ctk.CTkFrame(
            self.root, fg_color=BG, corner_radius=0)
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        self.nav = {}
        self.nav_ind = {}
        items = [
            ("studio",    "◈   Обзор"),
            ("monitor",   "⌁   Система"),
            ("pomodoro",  "◷   Фокус"),
            ("notes",     "▤   Заметки"),
            ("clipboard", "▣   Буфер"),
        ]
        self.nav_keys = [k for k, _ in items]

        sidebar = ctk.CTkFrame(
            shell, fg_color=CARD, corner_radius=theme.get_corner_radius(),
            border_width=1, border_color=LINE, width=190,
        )
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(22, 28))
        ctk.CTkLabel(
            brand, text="nook", font=("Segoe UI Semibold", 25),
            text_color=FG, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand, text="DESKTOP COMPANION", font=("Segoe UI", 9),
            text_color=FG_DIM, anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            sidebar, text="РАБОЧЕЕ ПРОСТРАНСТВО",
            font=("Segoe UI Semibold", 9), text_color=FG_FAINT,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 8))

        for key, label in items:
            col = ctk.CTkFrame(sidebar, fg_color="transparent", corner_radius=8)
            col.pack(fill="x", padx=8, pady=2)
            ind = ctk.CTkFrame(
                col, width=3, height=26, fg_color="transparent",
                corner_radius=2,
            )
            ind.pack(side="left", padx=(4, 7), pady=5)
            btn = ctk.CTkButton(
                col, text=label, anchor="w",
                fg_color="transparent", hover_color=BG_SOFT,
                text_color=FG_DIM, font=FONT_BODY,
                corner_radius=8, height=38,
                command=lambda k=key: self._show(k),
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=2)
            self.nav[key] = btn
            self.nav_ind[key] = ind

        sidebar_bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=12, pady=12)
        divider(sidebar_bottom).pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            sidebar_bottom, text="Работает в фоновом режиме",
            font=("Segoe UI", 10), text_color=FG_DIM, anchor="w",
        ).pack(fill="x", padx=5, pady=(0, 8))
        flat_button(
            sidebar_bottom, "↓  Свернуть в трей", self.hide,
            height=36, text_color=FG_DIM, anchor="w",
        ).pack(fill="x")

        workspace = ctk.CTkFrame(shell, fg_color="transparent")
        workspace.pack(side="left", fill="both", expand=True)
        topbar = ctk.CTkFrame(
            workspace, fg_color="transparent", height=42)
        topbar.pack(fill="x", pady=(2, 14))
        topbar.pack_propagate(False)
        ctk.CTkLabel(
            topbar, text="Панель управления", font=("Segoe UI Semibold", 16),
            text_color=FG, anchor="w",
        ).pack(side="left", fill="y")
        ctk.CTkLabel(
            topbar, text="●  Nook активен", font=FONT_SMALL,
            text_color=GOOD, anchor="e",
        ).pack(side="right", fill="y")

        self.content = ctk.CTkFrame(
            workspace, fg_color="transparent", corner_radius=0)
        self.content.pack(fill="both", expand=True)

        self.pages = {
            "studio":    self._build_studio(),
            "monitor":   self._build_monitor(),
            "pomodoro":  self._build_pomodoro(),
            "notes":     self._build_notes(),
            "clipboard": self._build_clipboard(),
        }

    def _show(self, key):
        for k, p in self.pages.items():
            p.pack_forget()
            self.nav[k].configure(
                text_color=FG_DIM, fg_color="transparent")
            self.nav_ind[k].configure(fg_color="transparent")
        self.pages[key].pack(fill="both", expand=True)
        self.nav[key].configure(
            text_color=FG, fg_color=BG_SOFT)
        self.nav_ind[key].configure(fg_color=theme.COLORS["ACCENT"])
        if key == "clipboard":
            self._reload_clip()
        if key == "notes":
            self._reload_notes()
            self.note_entry.focus_set()

    def _page_header(self, page, title, subtitle):
        head = ctk.CTkFrame(page, fg_color="transparent", corner_radius=0)
        head.pack(fill="x", pady=(2, 22))
        texts = ctk.CTkFrame(head, fg_color="transparent", corner_radius=0)
        texts.pack(side="left")
        ctk.CTkLabel(texts, text=title, font=FONT_TITLE,
                     text_color=FG).pack(anchor="w")
        ctk.CTkLabel(texts, text=subtitle, font=FONT_BODY,
                     text_color=FG_DIM).pack(anchor="w", pady=(4, 0))
        return head

    # ---------- Nook Studio ----------
    def _build_studio(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        self._page_header(page, "Nook Studio", "управление виджетами и профилями рабочего стола")

        scroll = ctk.CTkScrollableFrame(
            page, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=LINE,
            scrollbar_button_hover_color=FG_FAINT,
        )
        scroll.pack(fill="both", expand=True)

        widgets = card(scroll)
        widgets.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(widgets, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner, text="Виджеты", font=FONT_BODY,
                     text_color=FG, anchor="w").pack(anchor="w", pady=(0, 10))

        self.studio_taskbar_var = ctk.BooleanVar(
            value=self.taskbar_widget.is_user_visible())
        ctk.CTkSwitch(
            inner, text="Виджет на панели задач",
            variable=self.studio_taskbar_var,
            command=self._studio_set_taskbar_visibility,
            font=FONT_SMALL, text_color=FG_DIM,
        ).pack(anchor="w", pady=4)

        self.studio_desktop_var = ctk.BooleanVar(
            value=bool(self.desktop_widget and self.desktop_widget.is_visible()))
        ctk.CTkSwitch(
            inner, text="Виджет рабочего стола",
            variable=self.studio_desktop_var,
            command=self._studio_set_desktop_visibility,
            font=FONT_SMALL, text_color=FG_DIM,
        ).pack(anchor="w", pady=4)

        theme_card = card(scroll)
        theme_card.pack(fill="x", pady=(0, 14))
        theme_inner = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(theme_inner, text="Оформление", font=FONT_BODY,
                     text_color=FG, anchor="w").pack(anchor="w", pady=(0, 10))

        mode_row = ctk.CTkFrame(theme_inner, fg_color="transparent")
        mode_row.pack(fill="x", pady=4)
        ctk.CTkLabel(mode_row, text="Тема", font=FONT_SMALL,
                     text_color=FG_DIM).pack(side="left")
        self.studio_theme_mode = ctk.CTkOptionMenu(
            mode_row, values=list(theme.PRESET_NAMES.values()),
            command=self._studio_set_theme_mode, width=160, height=30,
        )
        self.studio_theme_mode.set(
            theme.PRESET_NAMES[self.theme_settings["preset"]])
        self.studio_theme_mode.pack(side="right")

        color_row = ctk.CTkFrame(theme_inner, fg_color="transparent")
        color_row.pack(fill="x", pady=(10, 4))
        self.theme_color_buttons = {}
        color_titles = {
            "BG": "Фон", "CARD": "Карточка",
            "FG": "Текст / акцент", "LINE": "Граница",
        }
        for color_key, title in color_titles.items():
            button = ctk.CTkButton(
                color_row, text=title, width=104, height=30,
                command=lambda key=color_key: self._studio_choose_theme_color(key),
                fg_color=theme.COLORS[color_key],
                hover_color=theme.COLORS[color_key],
                text_color=theme.COLORS["FG"],
                border_width=1, border_color=theme.COLORS["LINE"],
                corner_radius=min(theme.get_corner_radius(), 12),
            )
            button.pack(side="left", padx=(0, 6))
            self.theme_color_buttons[color_key] = button
        flat_button(
            color_row, "сбросить цвета", self._studio_reset_theme_colors,
            width=112, text_color=FG_DIM,
        ).pack(side="right")

        self.studio_opacity_value = ctk.CTkLabel(
            theme_inner, text="", font=FONT_SMALL, text_color=FG_DIM)
        self.studio_opacity_value.pack(anchor="w", pady=(10, 0))
        self.studio_opacity = ctk.CTkSlider(
            theme_inner, from_=0.45, to=1.0, number_of_steps=11,
            command=self._studio_set_theme_opacity,
        )
        self.studio_opacity.set(self.theme_settings["opacity"])
        self.studio_opacity.pack(fill="x", pady=(2, 8))

        self.studio_radius_value = ctk.CTkLabel(
            theme_inner, text="", font=FONT_SMALL, text_color=FG_DIM)
        self.studio_radius_value.pack(anchor="w")
        self.studio_radius = ctk.CTkSlider(
            theme_inner, from_=0, to=24, number_of_steps=12,
            command=self._studio_set_theme_radius,
        )
        self.studio_radius.set(self.theme_settings["corner_radius"])
        self.studio_radius.pack(fill="x", pady=(2, 0))
        self._studio_update_theme_labels()

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(row, text="Виджет панели задач", font=FONT_SMALL,
                     text_color=FG_DIM).pack(side="left")
        self.studio_mode = ctk.CTkOptionMenu(
            row, values=["Полный", "Компактный"],
            command=self._studio_set_taskbar_mode,
            width=140, height=30,
        )
        self.studio_mode.set(
            "Компактный" if self.taskbar_widget.mode == "compact" else "Полный")
        self.studio_mode.pack(side="right")

        panels = card(scroll)
        panels.pack(fill="x", pady=(0, 14))
        panel_inner = ctk.CTkFrame(panels, fg_color="transparent")
        panel_inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(panel_inner, text="Карточки рабочего стола", font=FONT_BODY,
                     text_color=FG, anchor="w").pack(anchor="w", pady=(0, 10))
        section_state = self.desktop_widget if self.desktop_widget else None
        self.studio_system_var = ctk.BooleanVar(
            value=(section_state.is_widget_visible("sys")
                   if section_state else True))
        self.studio_disks_var = ctk.BooleanVar(
            value=(section_state.is_widget_visible("disk")
                   if section_state else True))
        self.studio_clock_var = ctk.BooleanVar(
            value=(section_state.is_widget_visible("clock")
                   if section_state else True))
        ctk.CTkSwitch(
            panel_inner, text="Карточка «Система»",
            variable=self.studio_system_var,
            command=self._studio_set_sections,
            font=FONT_SMALL, text_color=FG_DIM,
        ).pack(anchor="w", pady=4)
        ctk.CTkSwitch(
            panel_inner, text="Карточка «Диски»",
            variable=self.studio_disks_var,
            command=self._studio_set_sections,
            font=FONT_SMALL, text_color=FG_DIM,
        ).pack(anchor="w", pady=4)
        ctk.CTkSwitch(
            panel_inner, text="Карточка «Часы»",
            variable=self.studio_clock_var,
            command=self._studio_set_sections,
            font=FONT_SMALL, text_color=FG_DIM,
        ).pack(anchor="w", pady=4)

        profiles = card(scroll)
        profiles.pack(fill="x", pady=(0, 14))
        profile_inner = ctk.CTkFrame(profiles, fg_color="transparent")
        profile_inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(profile_inner, text="Профили раскладки", font=FONT_BODY,
                     text_color=FG, anchor="w").pack(anchor="w", pady=(0, 10))
        self.profile_names = self._studio_profile_names()
        self.profile_menu = ctk.CTkOptionMenu(
            profile_inner,
            values=self.profile_names or ["нет сохранённых профилей"],
            width=220, height=30,
        )
        self.profile_menu.pack(side="left", padx=(0, 8))
        if not self.profile_names:
            self.profile_menu.configure(state="disabled")
        flat_button(
            profile_inner, "сохранить текущую", self._studio_save_profile,
            width=140, text_color=FG,
        ).pack(side="left", padx=(0, 8))
        line_button(
            profile_inner, "применить", self._studio_apply_profile, width=100,
        ).pack(side="left")

        return page

    def _studio_update_theme_labels(self):
        self.studio_opacity_value.configure(
            text=f"Прозрачность виджетов: "
                 f"{round(self.theme_settings['opacity'] * 100)}%")
        self.studio_radius_value.configure(
            text=f"Скругление углов: "
                 f"{self.theme_settings['corner_radius']} px")
        for key, button in self.theme_color_buttons.items():
            color = self.theme_settings["colors"].get(key, theme.COLORS[key])
            button.configure(
                fg_color=color, hover_color=color,
                text_color=theme.COLORS["FG"],
                border_color=theme.COLORS["LINE"],
            )

    def _studio_theme_changed(self, persist=False):
        previous = theme.set_settings(self.theme_settings)
        self._sync_theme_constants()
        theme.recolor_widget_tree(self.root, previous)
        if self._quick_notes_window and self._quick_notes_window.winfo_exists():
            theme.recolor_widget_tree(self._quick_notes_window, previous)
        self.root.configure(fg_color=theme.COLORS["BG"])
        self.taskbar_widget.apply_theme()
        if self.desktop_widget:
            self.desktop_widget.apply_theme()
        self._studio_update_theme_labels()
        if persist:
            if self._theme_save_job:
                self.root.after_cancel(self._theme_save_job)
                self._theme_save_job = None
            self._save_theme_settings()
        else:
            if self._theme_save_job:
                self.root.after_cancel(self._theme_save_job)
            self._theme_save_job = self.root.after(
                250, self._save_theme_settings)

    @staticmethod
    def _sync_theme_constants():
        global BG, BG_SOFT, CARD, CARD_HOVER, LINE
        global FG, FG_DIM, FG_FAINT, GOOD
        BG = theme.BG
        BG_SOFT = theme.BG_SOFT
        CARD = theme.CARD
        CARD_HOVER = theme.CARD_HOVER
        LINE = theme.LINE
        FG = theme.FG
        FG_DIM = theme.FG_DIM
        FG_FAINT = theme.FG_FAINT
        GOOD = theme.GOOD

    def _save_theme_settings(self):
        self._theme_save_job = None
        config = load_config()
        config["theme"] = theme.get_settings()
        save_config(config)

    def _studio_set_theme_mode(self, value):
        self.theme_settings["preset"] = next(
            key for key, name in theme.PRESET_NAMES.items() if name == value)
        self.theme_settings["colors"] = {}
        self._studio_theme_changed(persist=True)

    def _studio_choose_theme_color(self, color_key):
        current = self.theme_settings["colors"].get(
            color_key, theme.COLORS[color_key])
        _rgb, color = colorchooser.askcolor(
            color=current, title="Выберите цвет", parent=self.root)
        if not color:
            return
        self.theme_settings["colors"][color_key] = color
        self._studio_theme_changed(persist=True)

    def _studio_reset_theme_colors(self):
        self.theme_settings["colors"] = {}
        self._studio_theme_changed(persist=True)

    def _studio_set_theme_opacity(self, value):
        self.theme_settings["opacity"] = round(float(value), 2)
        self._studio_theme_changed()

    def _studio_set_theme_radius(self, value):
        self.theme_settings["corner_radius"] = round(float(value))
        self._studio_theme_changed()

    def _studio_set_taskbar_visibility(self):
        self.taskbar_widget.set_visibility(self.studio_taskbar_var.get())

    def _studio_set_desktop_visibility(self):
        if self.desktop_widget:
            self.desktop_widget.set_visibility(self.studio_desktop_var.get())

    def _studio_set_taskbar_mode(self, value):
        self.taskbar_widget._set_mode(
            "compact" if value == "Компактный" else "full")

    def _studio_set_sections(self):
        if self.desktop_widget:
            self.desktop_widget.set_widget_visibility(
                "sys", self.studio_system_var.get())
            self.desktop_widget.set_widget_visibility(
                "disk", self.studio_disks_var.get())
            self.desktop_widget.set_widget_visibility(
                "clock", self.studio_clock_var.get())

    def refresh_studio_controls(self):
        self.studio_taskbar_var.set(self.taskbar_widget.is_user_visible())
        self.studio_mode.set(
            "Компактный" if self.taskbar_widget.mode == "compact" else "Полный")
        if self.desktop_widget:
            self.studio_desktop_var.set(self.desktop_widget.is_visible())
            self.studio_system_var.set(
                self.desktop_widget.is_widget_visible("sys"))
            self.studio_disks_var.set(
                self.desktop_widget.is_widget_visible("disk"))
            self.studio_clock_var.set(
                self.desktop_widget.is_widget_visible("clock"))

    @staticmethod
    def _studio_profile_names():
        profiles = load_config().get("desktop_profiles", {})
        return sorted(profiles) if isinstance(profiles, dict) else []

    def _studio_refresh_profiles(self, selected=None):
        self.profile_names = self._studio_profile_names()
        self.profile_menu.configure(
            values=self.profile_names or ["нет сохранённых профилей"],
            state="normal" if self.profile_names else "disabled",
        )
        if selected in self.profile_names:
            self.profile_menu.set(selected)
        elif self.profile_names:
            self.profile_menu.set(self.profile_names[0])
        else:
            self.profile_menu.set("нет сохранённых профилей")

    def _studio_save_profile(self):
        name = simpledialog.askstring(
            "Сохранить раскладку", "Название профиля:", parent=self.root)
        if not name or not name.strip():
            return
        desktop = self.desktop_widget
        config = load_config()
        profiles = config.setdefault("desktop_profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}
            config["desktop_profiles"] = profiles
        if name.strip() in profiles and not messagebox.askyesno(
                "Перезаписать профиль",
                f"Профиль «{name.strip()}» уже существует. Перезаписать?",
                parent=self.root):
            return
        profiles[name.strip()] = {
            "taskbar": {
                "mode": self.taskbar_widget.mode,
                "visible": self.taskbar_widget.is_user_visible(),
            },
            "desktop": desktop.get_layout() if desktop else {"visible": False},
        }
        save_config(config)
        self._studio_refresh_profiles(name.strip())

    def _studio_apply_profile(self):
        name = self.profile_menu.get()
        profiles = load_config().get("desktop_profiles", {})
        if not isinstance(profiles, dict):
            return
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            return
        taskbar = profile.get("taskbar", {})
        if not isinstance(taskbar, dict):
            taskbar = {}
        if taskbar.get("mode") in ("compact", "full"):
            self.taskbar_widget._set_mode(taskbar["mode"])
            self.studio_mode.set(
                "Компактный" if taskbar["mode"] == "compact" else "Полный")
        if "visible" in taskbar:
            self.taskbar_widget.set_visibility(bool(taskbar["visible"]))
            self.studio_taskbar_var.set(bool(taskbar["visible"]))

        desktop = profile.get("desktop", {})
        if not isinstance(desktop, dict):
            desktop = {}
        if self.desktop_widget:
            if isinstance(desktop.get("widgets"), dict):
                self.desktop_widget.apply_layout(desktop)
            else:
                legacy = self.desktop_widget.get_layout()
                legacy["visible"] = bool(desktop.get("visible", True))
                x, y = desktop.get("x"), desktop.get("y")
                if isinstance(x, int) and isinstance(y, int):
                    system_height = (
                        self.desktop_widget.HEAD_H
                        + 3 * self.desktop_widget.ROW_H + 6
                    )
                    disk_height = (
                        self.desktop_widget.HEAD_H
                        + max(1, len(self.desktop_widget._disks))
                        * self.desktop_widget.ROW_H + 6
                    )
                    offsets = {
                        "sys": 0,
                        "disk": system_height + self.desktop_widget.GAP,
                        "clock": system_height + self.desktop_widget.GAP
                                 + disk_height + self.desktop_widget.GAP,
                    }
                    for key, offset in offsets.items():
                        legacy["widgets"][key].update(
                            x=x, y=y + offset, visible=True)
                self.desktop_widget.apply_layout(legacy)
            self.studio_desktop_var.set(self.desktop_widget.is_visible())
            self.studio_system_var.set(
                self.desktop_widget.is_widget_visible("sys"))
            self.studio_disks_var.set(
                self.desktop_widget.is_widget_visible("disk"))
            self.studio_clock_var.set(
                self.desktop_widget.is_widget_visible("clock"))

    # ---------- Система ----------
    def _build_monitor(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        head = self._page_header(
            page, "Система", "Загрузка компонентов и активность устройств")
        self.monitor_power = ctk.CTkLabel(
            head, text="Ожидание данных", font=FONT_SMALL,
            text_color=FG_DIM, anchor="e",
        )
        self.monitor_power.pack(side="right", fill="y")

        grid = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
        grid.pack(fill="x", pady=(0, 12))
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="m")

        self.m_cpu = MetricCard(grid, "Процессор")
        self.m_ram = MetricCard(grid, "Оперативная память")
        self.m_gpu = MetricCard(grid, "Графический процессор")
        self.m_disk = MetricCard(grid, "Диск · чтение и запись", show_bar=False)
        self.m_net_down = MetricCard(grid, "Сеть · загрузка", show_bar=False)
        self.m_net_up = MetricCard(grid, "Сеть · отдача", show_bar=False)
        metrics = (
            self.m_cpu, self.m_ram, self.m_gpu,
            self.m_disk, self.m_net_down, self.m_net_up,
        )
        for i, metric in enumerate(metrics):
            row, column = divmod(i, 3)
            metric.frame.grid(
                row=row, column=column, sticky="nsew",
                padx=(0 if column == 0 else 6, 0 if column == 2 else 6),
                pady=(0, 12 if row == 0 else 0),
            )
        return page

    def _refresh_monitor(self):
        # пока окно скрыто в трей — не тратим ресурсы
        if self.root.state() != "withdrawn":
            s = monitor.get_stats()
            self.m_cpu.update(f"{s['cpu']}%", s["cpu"],
                              sub="Общая загрузка процессора",
                              color=level_color(s["cpu"]))
            self.m_ram.update(
                f"{s['ram']}%", s["ram"],
                sub=f"{s['ram_used_gb']} из {s['ram_total_gb']} ГБ",
                color=level_color(s["ram"]),
            )
            if s["gpu"] is not None:
                self.m_gpu.update(
                    f"{s['gpu']}%", s["gpu"], sub="Загрузка графического процессора",
                    color=level_color(s["gpu"]),
                )
            else:
                self.m_gpu.update("—", None, sub="Датчик GPU недоступен")
            self.m_disk.update(
                monitor.format_speed(s["disk"]), sub="Чтение и запись")
            self.m_net_down.update(
                monitor.format_speed(s["net_down"]), sub="Входящий трафик")
            self.m_net_up.update(
                monitor.format_speed(s["net_up"]), sub="Исходящий трафик")
            if s["battery"] is not None:
                power = " · подключено к сети" if s["plugged"] else " · от батареи"
                self.monitor_power.configure(
                    text=f"Питание  {s['battery']}%{power}",
                    text_color=GOOD if s["plugged"] else FG_DIM,
                )
            else:
                self.monitor_power.configure(
                    text="Батарея не обнаружена", text_color=FG_DIM)
        self.root.after(2000, self._refresh_monitor)

    # ---------- Таймер ----------
    def _build_pomodoro(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        self._page_header(page, "Фокус", "Работай короткими спринтами и отдыхай вовремя")

        layout = ctk.CTkFrame(page, fg_color="transparent")
        layout.pack(fill="both", expand=True)
        layout.grid_columnconfigure(0, weight=7, uniform="focus")
        layout.grid_columnconfigure(1, weight=4, uniform="focus")
        layout.grid_rowconfigure(0, weight=1)

        focus_card = card(layout)
        focus_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        inner = ctk.CTkFrame(focus_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=24)

        self.pomo_phase = ctk.CTkLabel(
            inner, text="ГОТОВ К РАБОТЕ",
            font=("Segoe UI Semibold", 11), text_color=FG_DIM)
        self.pomo_phase.pack(pady=(8, 0))

        self.pomo_time = ctk.CTkLabel(
            inner, text="25:00", font=("Segoe UI Light", 76),
            text_color=FG)
        self.pomo_time.pack(expand=True, pady=(6, 0))

        self.pomo_bar = progress_bar(inner, color=theme.COLORS["ACCENT"], height=6)
        self.pomo_bar.set(0)
        self.pomo_bar.pack(fill="x", pady=(0, 22))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        self.pomo_start_button = primary_button(
            btns, "Начать фокус", self._start_pomo, height=42)
        self.pomo_start_button.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.pomo_pause_button = line_button(
            btns, "Пауза", self._pause_pomo, height=42)
        self.pomo_pause_button.pack(side="left", padx=(0, 8))
        self.pomo_pause_button.configure(state="disabled")
        line_button(
            btns, "Сброс", self._reset_pomo, height=42,
            text_color=FG_DIM,
        ).pack(side="left")

        info_card = card(layout)
        info_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        info = ctk.CTkFrame(info_card, fg_color="transparent")
        info.pack(fill="both", expand=True, padx=20, pady=22)
        ctk.CTkLabel(
            info, text="ЦИКЛ ФОКУСА", font=("Segoe UI Semibold", 10),
            text_color=FG_DIM, anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text="25 + 5 минут", font=("Segoe UI Semibold", 19),
            text_color=FG, anchor="w",
        ).pack(fill="x", pady=(8, 3))
        ctk.CTkLabel(
            info, text="После четырёх спринтов — длинный отдых.",
            font=FONT_SMALL, text_color=FG_DIM, anchor="w",
            wraplength=190, justify="left",
        ).pack(fill="x", pady=(0, 24))

        ctk.CTkLabel(
            info, text="СПРИНТЫ", font=("Segoe UI Semibold", 10),
            text_color=FG_DIM, anchor="w",
        ).pack(fill="x", pady=(0, 10))
        self.pomo_cycles = ctk.CTkLabel(
            info, text="0 завершено", font=FONT_BODY,
            text_color=FG, anchor="w",
        )
        self.pomo_cycles.pack(fill="x", pady=(0, 10))
        cycle_marks = ctk.CTkFrame(info, fg_color="transparent")
        cycle_marks.pack(fill="x", pady=(0, 8))
        self.pomo_cycle_marks = []
        for _ in range(4):
            mark = ctk.CTkFrame(
                cycle_marks, height=6, fg_color=FG_FAINT,
                corner_radius=3,
            )
            mark.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.pomo_cycle_marks.append(mark)
        ctk.CTkLabel(
            info, text="Короткий отдых после каждого спринта",
            font=FONT_SMALL, text_color=FG_DIM, anchor="w",
            wraplength=190, justify="left",
        ).pack(fill="x", pady=(16, 0))
        return page

    def _start_pomo(self):
        self.pomodoro.start()
        self.pomo_start_button.configure(text="Фокус идёт", state="disabled")
        self.pomo_pause_button.configure(state="normal")
        self.pomo_phase.configure(
            text=("ФОКУС" if self.pomodoro.phase == "work" else "ОТДЫХ"),
            text_color=(FG if self.pomodoro.phase == "work" else GOOD),
        )

    def _pause_pomo(self):
        self.pomodoro.pause()
        if self.pomodoro.phase != "idle":
            self.pomo_phase.configure(text="ПАУЗА", text_color=FG_DIM)
            self.pomo_start_button.configure(
                text="Продолжить фокус", state="normal")
            self.pomo_pause_button.configure(state="disabled")

    def _reset_pomo(self):
        self.pomodoro.reset()
        self.pomo_phase.configure(text="ГОТОВ К РАБОТЕ", text_color=FG_DIM)
        self.pomo_time.configure(text="25:00")
        self.pomo_bar.set(0)
        self.pomo_bar.configure(progress_color=theme.COLORS["ACCENT"])
        self.pomo_start_button.configure(text="Начать фокус", state="normal")
        self.pomo_pause_button.configure(state="disabled")
        self.pomo_cycles.configure(text="0 завершено")
        for mark in self.pomo_cycle_marks:
            mark.configure(fg_color=FG_FAINT)

    def _update_pomodoro_ui(self, remaining, phase):
        # after(0) — безопасно, даже если таймер тикает из другого потока
        self.root.after(0, lambda: self._apply_pomodoro(remaining, phase))

    def _apply_pomodoro(self, remaining, phase):
        total = {"work": 25 * 60, "short": 5 * 60, "long": 15 * 60}.get(phase, 1)
        names = {
            "work": "ФОКУС",
            "short": "КОРОТКИЙ ОТДЫХ",
            "long": "ДЛИННЫЙ ОТДЫХ",
        }
        accent = theme.COLORS["ACCENT"] if phase == "work" else GOOD
        m, s = divmod(int(remaining), 60)
        self.pomo_time.configure(text=f"{m:02d}:{s:02d}")
        self.pomo_phase.configure(text=names.get(phase, phase), text_color=accent)
        self.pomo_bar.configure(progress_color=accent)
        self.pomo_bar.set(max(0, min(1, 1 - remaining / total)))
        cycles = self.pomodoro.cycle
        self.pomo_cycles.configure(
            text=f"{cycles} завершено" if cycles != 1 else "1 завершён")
        completed = cycles % 4
        if phase == "long":
            completed = 4
        for index, mark in enumerate(self.pomo_cycle_marks):
            mark.configure(
                fg_color=accent if index < completed
                else FG_FAINT,
            )

    # ---------- Заметки ----------
    def _build_notes(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        head = self._page_header(
            page, "Заметки", "Быстрые записи доступны в трее и по Ctrl+Alt+N")
        self.notes_count = ctk.CTkLabel(
            head, text="0 записей", font=FONT_SMALL, text_color=FG_DIM)
        self.notes_count.pack(side="right", padx=(0, 12))
        flat_button(
            head, "Быстрая заметка", self.show_quick_note,
            text_color=theme.COLORS["ACCENT"],
        ).pack(side="right")
        ctk.CTkLabel(
            head, text="Ctrl+Alt+N", font=FONT_SMALL, text_color=FG_DIM,
        ).pack(side="right", padx=(0, 8))

        row = card(page)
        row.pack(fill="x", pady=(0, 14))
        self.note_entry = ctk.CTkEntry(
            row, placeholder_text="Запишите идею, задачу или напоминание…",
            fg_color="transparent", border_width=0,
            text_color=FG, font=FONT_BODY, height=40,
        )
        self.note_entry.pack(
            side="left", fill="x", expand=True, padx=(14, 4), pady=6)
        self.note_entry.bind("<Return>", lambda _event: self._add_note())
        self.note_entry.bind(
            "<Control-Return>", lambda _event: self._add_note())
        primary_button(
            row, "Добавить", self._add_note, width=100, height=34,
        ).pack(side="right", padx=(4, 8), pady=8)

        box = card(page)
        box.pack(fill="both", expand=True)
        self.notes_list = ctk.CTkScrollableFrame(
            box, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=LINE,
            scrollbar_button_hover_color=FG_FAINT,
        )
        self.notes_list.pack(fill="both", expand=True, padx=10, pady=10)
        return page

    def _add_note(self):
        text = self.note_entry.get().strip()
        if not text:
            return
        notes_mod.add_note(text)
        self.note_entry.delete(0, "end")
        self._reload_notes()

    def _reload_notes(self):
        if not hasattr(self, "notes_list"):
            return
        for widget in self.notes_list.winfo_children():
            widget.destroy()

        entries = self._read_note_entries()
        count = len(entries)
        if count % 10 == 1 and count % 100 != 11:
            count_text = f"{count} заметка"
        elif 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
            count_text = f"{count} заметки"
        else:
            count_text = f"{count} заметок"
        self.notes_count.configure(text=count_text)

        if not entries:
            ctk.CTkLabel(
                self.notes_list, text="Здесь пока пусто",
                font=("Segoe UI Semibold", 16), text_color=FG_DIM,
            ).pack(anchor="center", pady=(45, 6))
            ctk.CTkLabel(
                self.notes_list, text="Добавьте первую заметку выше или нажмите Ctrl+Alt+N",
                font=FONT_SMALL, text_color=FG_FAINT,
            ).pack(anchor="center")
        else:
            for timestamp, text in reversed(entries):
                note = card(self.notes_list)
                note.pack(fill="x", pady=(0, 8))
                content = ctk.CTkFrame(note, fg_color="transparent")
                content.pack(fill="x", padx=14, pady=11)
                ctk.CTkLabel(
                    content, text=text, font=FONT_BODY, text_color=FG,
                    anchor="w", justify="left", wraplength=660,
                ).pack(fill="x")
                ctk.CTkLabel(
                    content, text=timestamp, font=FONT_SMALL,
                    text_color=FG_DIM, anchor="w",
                ).pack(fill="x", pady=(6, 0))

        self._refresh_quick_note_history()

    @staticmethod
    def _read_note_entries():
        content = notes_mod.read_notes()
        entries = []
        for line in content.splitlines():
            if not line.strip() or line.strip() == "Пока пусто...":
                continue
            timestamp, separator, text = line.partition("] ")
            if separator and timestamp.startswith("["):
                entries.append((timestamp[1:], text))
            else:
                entries.append(("", line))
        return entries

    # ---------- Буфер ----------
    def _build_clipboard(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        head = self._page_header(page, "буфер", "клик — вернуть в буфер")
        self.clip_toast = ctk.CTkLabel(head, text="", font=FONT_BODY,
                                       text_color=GOOD)
        self.clip_toast.pack(side="right", anchor="s")

        self.clip_scroll = ctk.CTkScrollableFrame(
            page, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=LINE,
            scrollbar_button_hover_color=FG_FAINT,
        )
        self.clip_scroll.pack(fill="both", expand=True)
        return page

    def _reload_clip(self):
        for w in self.clip_scroll.winfo_children():
            w.destroy()
        if not self.clipboard.history:
            ctk.CTkLabel(self.clip_scroll, text="пусто",
                         text_color=FG_FAINT, font=FONT_BODY).pack(anchor="w")
            return
        for i, item in enumerate(self.clipboard.history):
            preview = item.replace("\n", " ").strip()[:90] or "(пробелы)"
            ctk.CTkButton(
                self.clip_scroll,
                text=f"{i + 1:02d}   {preview}", anchor="w", font=FONT_MONO,
                fg_color=CARD, hover_color=CARD_HOVER,
                border_width=1, border_color=LINE,
                text_color=FG_DIM, height=36, corner_radius=8,
                command=lambda idx=i: self._copy_back(idx),
            ).pack(fill="x", pady=3)

    def _copy_back(self, idx):
        self.clipboard.copy_back(idx)
        self.clip_toast.configure(text="скопировано ✓")
        if self._toast_job:
            self.root.after_cancel(self._toast_job)
        self._toast_job = self.root.after(
            1500, lambda: self.clip_toast.configure(text=""))

    def show_quick_note(self):
        if self._quick_notes_window and self._quick_notes_window.winfo_exists():
            self._quick_notes_window.deiconify()
            self._quick_notes_window.lift()
            self.quick_note_entry.focus_set()
            return

        win = ctk.CTkToplevel(self.root)
        self._quick_notes_window = win
        win.title("Быстрая заметка — Nook")
        win.geometry("460x540")
        win.minsize(380, 440)

        heading = ctk.CTkFrame(win, fg_color="transparent")
        heading.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(
            heading, text="Быстрая заметка", font=FONT_TITLE, text_color=FG,
        ).pack(side="left")
        ctk.CTkLabel(
            heading, text="Ctrl+Alt+N", font=FONT_SMALL, text_color=FG_DIM,
        ).pack(side="right", padx=(8, 0))

        editor = card(win)
        editor.pack(fill="x", padx=20, pady=(0, 10))
        self.quick_note_entry = ctk.CTkTextbox(
            editor, height=104, wrap="word", font=FONT_BODY,
            fg_color="transparent", border_width=0,
        )
        self.quick_note_entry.pack(fill="x", padx=10, pady=(8, 4))
        self.quick_note_entry.bind(
            "<Control-Return>", lambda _event: self._save_quick_note())
        primary_button(
            editor, "Сохранить заметку  ·  Ctrl+Enter", self._save_quick_note,
            height=36,
        ).pack(fill="x", padx=10, pady=(0, 10))

        history_head = ctk.CTkFrame(win, fg_color="transparent")
        history_head.pack(fill="x", padx=20, pady=(4, 8))
        ctk.CTkLabel(
            history_head, text="Последние заметки", font=FONT_BODY,
            text_color=FG,
        ).pack(side="left")
        flat_button(
            history_head, "Все заметки", self._show_notes_page,
            height=28, text_color=FG_DIM,
        ).pack(side="right")
        self.quick_note_history = ctk.CTkScrollableFrame(
            win, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=LINE,
            scrollbar_button_hover_color=FG_FAINT,
        )
        self.quick_note_history.pack(
            fill="both", expand=True, padx=20, pady=(0, 14))
        theme.recolor_widget_tree(win)
        win.protocol("WM_DELETE_WINDOW", win.withdraw)
        win.bind("<Destroy>", self._on_quick_note_destroy, add="+")
        self._refresh_quick_note_history()
        win.after(100, self.quick_note_entry.focus_set)

    def _show_notes_page(self):
        quick_window = self._quick_notes_window
        if quick_window and quick_window.winfo_exists():
            quick_window.withdraw()
        self.show()
        self._show("notes")

    def _on_quick_note_destroy(self, event):
        if event.widget is self._quick_notes_window:
            self._quick_notes_window = None

    def _refresh_quick_note_history(self):
        history = getattr(self, "quick_note_history", None)
        if not history or not history.winfo_exists():
            return
        for widget in history.winfo_children():
            widget.destroy()
        entries = self._read_note_entries()
        if not entries:
            ctk.CTkLabel(
                history, text="Сохранённых заметок пока нет",
                font=FONT_SMALL, text_color=FG_DIM,
            ).pack(anchor="w", padx=4, pady=12)
            return
        for timestamp, text in reversed(entries[-5:]):
            item = card(history)
            item.pack(fill="x", pady=(0, 7))
            content = ctk.CTkFrame(item, fg_color="transparent")
            content.pack(fill="x", padx=11, pady=9)
            ctk.CTkLabel(
                content, text=text, font=FONT_SMALL, text_color=FG,
                anchor="w", justify="left", wraplength=360,
            ).pack(fill="x")
            if timestamp:
                ctk.CTkLabel(
                    content, text=timestamp, font=("Segoe UI", 9),
                    text_color=FG_DIM, anchor="w",
                ).pack(fill="x", pady=(4, 0))

    def _save_quick_note(self):
        text = self.quick_note_entry.get("1.0", "end").strip()
        if not text:
            return
        notes_mod.add_note(" ".join(text.splitlines()))
        self.quick_note_entry.delete("1.0", "end")
        self._refresh_quick_note_history()
        self._reload_notes()
        self.quick_note_entry.focus_set()

    # ---------- Жизненный цикл ----------
    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh_studio_controls()
        self._reload_clip()

    def hide(self):
        self.root.withdraw()
        self.on_hide()

    def run_forever(self):
        self.root.mainloop()

    def destroy(self):
        self.pomodoro.reset()
        try:
            self.taskbar_widget.win.destroy()
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()