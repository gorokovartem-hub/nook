"""Вкладка Настройки для nook."""
import customtkinter as ctk
from tkinter import messagebox
import theme
import config_manager as cfg_mgr

class SettingsTab:
    def __init__(self, parent, taskbar_widget=None, appearance_builder=None):
        self.parent = parent
        self.taskbar_widget = taskbar_widget
        self.appearance_builder = appearance_builder
        self.C = theme.COLORS
        self.scroll = ctk.CTkScrollableFrame(
            parent, fg_color=theme.COLORS["BG"], corner_radius=0,
            scrollbar_button_color=self.C["LINE"],
            scrollbar_button_hover_color=self.C["FG_FAINT"],
        )
        self.scroll.pack(fill="both", expand=True)
        self._build_general()
        self._build_hotkeys()
        self._build_system()
        self._build_screenshots()
        self._build_data()

    def rebuild(self):
        for w in self.scroll.winfo_children(): w.destroy()
        self.C = theme.COLORS
        self._build_general()
        self._build_hotkeys()
        self._build_system()
        self._build_screenshots()
        self._build_data()

    def _section(self, title: str):
        ctk.CTkLabel(self.scroll, text=title, font=("Segoe UI", 13, "bold"), text_color=theme.COLORS["FG"], anchor="w").pack(fill="x", pady=(16, 6))
        ctk.CTkFrame(self.scroll, height=1, fg_color=theme.COLORS["LINE"]).pack(fill="x", pady=(0, 10))

    def _row(self, label: str, widget_factory):
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=label, anchor="w", font=("Segoe UI", 12), text_color=theme.COLORS["FG"]).pack(side="left", padx=(0, 12))
        w = widget_factory(row)
        w.pack(side="right")
        return w

    def _switch(self, parent, initial: bool, command):
        var = ctk.BooleanVar(value=initial)
        sw = ctk.CTkSwitch(parent, text="", variable=var, onvalue=True, offvalue=False, command=lambda: command(var.get()), progress_color=theme.COLORS["FG"], button_color=theme.COLORS["FG"], button_hover_color=theme.COLORS["FG_DIM"], fg_color=theme.COLORS["FG_FAINT"], width=40)
        return sw

    def _build_general(self):
        if self.appearance_builder:
            self.appearance_builder(self.scroll)
        self._section("Общие")
        cfg = cfg_mgr.load_config()["general"]
        self._row("Запускать при старте Windows", lambda p: self._switch(p, cfg["autostart"], lambda v: self._set("general.autostart", v)))
        self._row("Запускать свёрнутым в трей", lambda p: self._switch(p, cfg["start_minimized"], lambda v: self._set("general.start_minimized", v)))
        self._row("Проверять обновления при запуске", lambda p: self._switch(p, cfg["check_updates"], lambda v: self._set("general.check_updates", v)))

    def _build_hotkeys(self):
        self._section("Горячие клавиши")
        hk = cfg_mgr.load_config()["hotkeys"]
        labels = {"compact": "Компактный режим", "full": "Полный режим", "toggle": "Показать/скрыть", "note": "Быстрая заметка", "screenshot": "Скриншот области"}
        for key, human in labels.items():
            self._row(human, lambda p, k=key, cur=hk[key]: self._hotkey_entry(p, k, cur))

    def _hotkey_entry(self, parent, key: str, current: str):
        entry = ctk.CTkEntry(parent, width=140, height=28, fg_color="transparent", border_color=theme.COLORS["LINE"], text_color=theme.COLORS["FG"], font=("Cascadia Mono", 11))
        entry.insert(0, current)
        def on_save(event):
            new_val = entry.get().strip().lower()
            if not new_val: return
            self._set(f"hotkeys.{key}", new_val)
            if self.taskbar_widget: self.taskbar_widget._register_hotkeys()
            self.parent.focus_set()
        entry.bind("<FocusOut>", on_save)
        entry.bind("<Return>", on_save)
        return entry

    def _build_system(self):
        self._section("Система")
        cfg = cfg_mgr.load_config()["system"]
        self._row("Скрывать в полноэкранных приложениях", lambda p: self._switch(p, cfg["hide_in_fullscreen"], lambda v: self._set("system.hide_in_fullscreen", v)))
        self._row("Звук при высокой нагрузке", lambda p: self._switch(p, cfg["sound_on_high_load"], lambda v: self._set("system.sound_on_high_load", v)))

    def _build_screenshots(self):
        self._section("Скриншоты")
        cfg = cfg_mgr.load_config()["screenshots"]
        self._row("Копировать в буфер обмена", lambda p: self._switch(p, cfg["copy_to_clipboard"], lambda v: self._set("screenshots.copy_to_clipboard", v)))

    def _build_data(self):
        self._section("Данные")
        ctk.CTkButton(self.scroll, text="Очистить все заметки", fg_color="transparent", hover_color=theme.COLORS["BG_SOFT"], text_color=theme.COLORS["FG"], border_width=1, border_color=theme.COLORS["LINE"], corner_radius=6, height=32, command=self._clear_notes).pack(anchor="w", pady=4)

    def _set(self, path: str, value):
        cfg_mgr.set_value(path, value)

    def _clear_notes(self):
        from features import notes as notes_mod
        if messagebox.askyesno("nook", "Удалить все заметки?"):
            notes_mod.clear_notes()
            messagebox.showinfo("nook", "Заметки очищены.")