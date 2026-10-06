"""Минималистичное главное окно + виджет на таскбаре."""
import customtkinter as ctk

from features import monitor, notes as notes_mod
from features.pomodoro import Pomodoro
from features.clipboard import ClipboardWatcher
from theme import (
    BG, BG_SOFT, CARD, CARD_HOVER, LINE, FG, FG_DIM, FG_FAINT, GOOD,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_MONO,
    setup_appearance, divider, card, progress_bar, level_color,
    flat_button, line_button, primary_button,
)
from taskbar_widget import TaskbarWidget

WIN_W, WIN_H = 760, 520


class MetricCard:
    """Карточка метрики: подпись, крупное значение, полоска, подпись снизу."""

    def __init__(self, parent, label):
        self.frame = card(parent)
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        ctk.CTkLabel(inner, text=label, font=FONT_MONO,
                     text_color=FG_DIM, anchor="w").pack(fill="x")
        self.value = ctk.CTkLabel(inner, text="—", font=("Segoe UI Light", 38),
                                  text_color=FG, anchor="w")
        self.value.pack(fill="x", pady=(8, 10))
        self.bar = progress_bar(inner)
        self.bar.set(0)
        self.bar.pack(fill="x")
        self.sub = ctk.CTkLabel(inner, text=" ", font=FONT_SMALL,
                                text_color=FG_DIM, anchor="w")
        self.sub.pack(fill="x", pady=(10, 0))

    def update(self, text, pct=None, sub=" ", color=None):
        self.value.configure(text=text)
        self.sub.configure(text=sub)
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

        self.root = ctk.CTk()
        self.root.title("tray")
        self._center(WIN_W, WIN_H)
        self.root.minsize(680, 480)
        self.root.configure(fg_color=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        # Виджет на таскбаре (Toplevel поверх главного Tk)
        self.taskbar_widget = TaskbarWidget(self.root)

        self._build()
        self._bind_keys()
        self._show("monitor")
        self._refresh_monitor()

    def _center(self, w, h):
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 3
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _bind_keys(self):
        for i, key in enumerate(self.nav_keys, start=1):
            self.root.bind(f"<Control-Key-{i}>", lambda e, k=key: self._show(k))
        self.root.bind("<Escape>", lambda e: self.hide())

    # ---------- Каркас ----------
    def _build(self):
        top = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0, height=48)
        top.pack(fill="x", padx=32, pady=(20, 0))
        top.pack_propagate(False)

        self.nav = {}
        self.nav_ind = {}
        items = [
            ("monitor",   "система"),
            ("pomodoro",  "таймер"),
            ("notes",     "заметки"),
            ("clipboard", "буфер"),
        ]
        self.nav_keys = [k for k, _ in items]

        for key, label in items:
            col = ctk.CTkFrame(top, fg_color=BG, corner_radius=0)
            col.pack(side="left", padx=(0, 6), fill="y")
            btn = ctk.CTkButton(
                col, text=label, anchor="center",
                fg_color="transparent", hover_color=BG_SOFT,
                text_color=FG_DIM, font=FONT_BODY,
                corner_radius=6, height=34, width=84,
                command=lambda k=key: self._show(k),
            )
            btn.pack(pady=(4, 0))
            ind = ctk.CTkFrame(col, height=2, width=40, fg_color=BG, corner_radius=0)
            ind.pack(pady=(4, 0))
            self.nav[key] = btn
            self.nav_ind[key] = ind

        flat_button(top, "→ трей", self.hide, width=80,
                    text_color=FG_DIM).pack(side="right", pady=(4, 0))

        divider(self.root).pack(fill="x", padx=32)

        self.content = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        self.content.pack(fill="both", expand=True, padx=32, pady=(28, 28))

        self.pages = {
            "monitor":   self._build_monitor(),
            "pomodoro":  self._build_pomodoro(),
            "notes":     self._build_notes(),
            "clipboard": self._build_clipboard(),
        }

    def _show(self, key):
        for k, p in self.pages.items():
            p.pack_forget()
            self.nav[k].configure(text_color=FG_DIM)
            self.nav_ind[k].configure(fg_color=BG)
        self.pages[key].pack(fill="both", expand=True)
        self.nav[key].configure(text_color=FG)
        self.nav_ind[key].configure(fg_color=FG)
        if key == "clipboard":
            self._reload_clip()
        if key == "notes":
            self._reload_notes()
            self.note_entry.focus_set()

    def _page_header(self, page, title, subtitle):
        head = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
        head.pack(fill="x", pady=(0, 24))
        texts = ctk.CTkFrame(head, fg_color=BG, corner_radius=0)
        texts.pack(side="left")
        ctk.CTkLabel(texts, text=title, font=FONT_TITLE,
                     text_color=FG).pack(anchor="w")
        ctk.CTkLabel(texts, text=subtitle, font=FONT_BODY,
                     text_color=FG_DIM).pack(anchor="w", pady=(2, 0))
        return head

    # ---------- Система ----------
    def _build_monitor(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        self._page_header(page, "система", "обновляется каждые 2 секунды")

        grid = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="m")

        self.m_cpu = MetricCard(grid, "cpu")
        self.m_ram = MetricCard(grid, "ram")
        self.m_bat = MetricCard(grid, "bat")
        for i, m in enumerate((self.m_cpu, self.m_ram, self.m_bat)):
            m.frame.grid(row=0, column=i, sticky="nsew",
                         padx=(0 if i == 0 else 6, 0 if i == 2 else 6))
        return page

    def _refresh_monitor(self):
        # пока окно скрыто в трей — не тратим ресурсы
        if self.root.state() != "withdrawn":
            s = monitor.get_stats()
            self.m_cpu.update(f"{s['cpu']}%", s["cpu"],
                              color=level_color(s["cpu"]))
            self.m_ram.update(
                f"{s['ram']}%", s["ram"],
                sub=f"{s['ram_used_gb']} / {s['ram_total_gb']} гб",
                color=level_color(s["ram"]),
            )
            if s["battery"] is not None:
                color = GOOD if s["plugged"] else level_color(s["battery"], invert=True)
                self.m_bat.update(
                    f"{s['battery']}%", s["battery"],
                    sub="питание" if s["plugged"] else "батарея",
                    color=color,
                )
            else:
                self.m_bat.update("—", None, sub="нет батареи")
        self.root.after(2000, self._refresh_monitor)

    # ---------- Таймер ----------
    def _build_pomodoro(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        self._page_header(page, "таймер", "25 / 5 — фокус и отдых")

        box = card(page)
        box.pack(fill="x")
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=28, pady=24)

        self.pomo_phase = ctk.CTkLabel(inner, text="готов",
                                       font=FONT_MONO, text_color=FG_DIM)
        self.pomo_phase.pack(anchor="w")

        self.pomo_time = ctk.CTkLabel(inner, text="25:00",
                                      font=("Segoe UI Light", 84),
                                      text_color=FG)
        self.pomo_time.pack(anchor="w", pady=(0, 8))

        self.pomo_bar = progress_bar(inner, color=FG, height=4)
        self.pomo_bar.set(0)
        self.pomo_bar.pack(fill="x", pady=(0, 24))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(anchor="w")
        primary_button(btns, "старт", self.pomodoro.start, width=96
                       ).pack(side="left", padx=(0, 8))
        line_button(btns, "пауза", self.pomodoro.pause, width=96
                    ).pack(side="left", padx=(0, 8))
        flat_button(btns, "сброс", self._reset_pomo, width=80,
                    text_color=FG_DIM).pack(side="left")
        return page

    def _reset_pomo(self):
        self.pomodoro.reset()
        self.pomo_phase.configure(text="готов", text_color=FG_DIM)
        self.pomo_time.configure(text="25:00")
        self.pomo_bar.set(0)
        self.pomo_bar.configure(progress_color=FG)

    def _update_pomodoro_ui(self, remaining, phase):
        # after(0) — безопасно, даже если таймер тикает из другого потока
        self.root.after(0, lambda: self._apply_pomodoro(remaining, phase))

    def _apply_pomodoro(self, remaining, phase):
        total = {"work": 25 * 60, "short": 5 * 60, "long": 15 * 60}.get(phase, 1)
        names = {"work": "работа", "short": "перерыв", "long": "отдых"}
        accent = FG if phase == "work" else GOOD
        m, s = divmod(int(remaining), 60)
        self.pomo_time.configure(text=f"{m:02d}:{s:02d}")
        self.pomo_phase.configure(text=names.get(phase, phase), text_color=accent)
        self.pomo_bar.configure(progress_color=accent)
        self.pomo_bar.set(max(0, min(1, 1 - remaining / total)))

    # ---------- Заметки ----------
    def _build_notes(self):
        page = ctk.CTkFrame(self.content, fg_color=BG)
        self._page_header(page, "заметки", "сохраняются в notes.txt · enter — добавить")

        row = card(page)
        row.pack(fill="x", pady=(0, 14))
        self.note_entry = ctk.CTkEntry(
            row, placeholder_text="что записать…",
            fg_color="transparent", border_width=0,
            text_color=FG, font=FONT_BODY, height=40,
        )
        self.note_entry.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=4)
        self.note_entry.bind("<Return>", lambda e: self._add_note())
        primary_button(row, "добавить", self._add_note, width=96, height=30
                       ).pack(side="right", padx=(4, 8), pady=4)

        box = card(page)
        box.pack(fill="both", expand=True)
        self.notes_text = ctk.CTkTextbox(
            box, fg_color="transparent", border_width=0,
            text_color=FG, font=FONT_MONO, wrap="word",
        )
        self.notes_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.notes_text.configure(state="disabled")
        return page

    def _add_note(self):
        text = self.note_entry.get().strip()
        if not text:
            return
        notes_mod.add_note(text)
        self.note_entry.delete(0, "end")
        self._reload_notes()

    def _reload_notes(self):
        content = notes_mod.read_notes()
        self.notes_text.configure(state="normal")
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", content if content.strip() else "пока пусто")
        self.notes_text.configure(state="disabled")

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

    # ---------- Жизненный цикл ----------
    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
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