"""Виджет CPU/RAM/GPU/диск/сеть на панели задач."""
import ctypes
import ctypes.wintypes as wt
import tkinter as tk
from collections import deque

from features import monitor, hotkeys
import theme
from config_manager import load_config, save_config
import win_blur
from i18n import tr  # <--- ДОБАВЛЕН ИМПОРТ ДЛЯ ПЕРЕВОДА

# ============================================================
#  WinAPI
# ============================================================
user32 = ctypes.windll.user32
FindWindowW = user32.FindWindowW
FindWindowW.restype = wt.HWND
FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]

GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = wt.HWND

GetClassNameW = user32.GetClassNameW
GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]

GWL_EXSTYLE      = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

GetWindowLongW = user32.GetWindowLongW
SetWindowLongW = user32.SetWindowLongW

MonitorFromWindow = user32.MonitorFromWindow
MonitorFromWindow.restype = wt.HANDLE
MonitorFromWindow.argtypes = [wt.HWND, wt.DWORD]
MONITOR_DEFAULTTONEAREST = 2
GetMonitorInfoW = user32.GetMonitorInfoW

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize",    wt.DWORD),
        ("rcMonitor", wt.RECT),
        ("rcWork",    wt.RECT),
        ("dwFlags",   wt.DWORD),
    ]

# ============================================================
#  Хелперы
# ============================================================
def color_for(v: float) -> str:
    if v < 50:
        return "#4ade80"
    if v < 80:
        return "#fbbf24"
    return "#f87171"

def get_taskbar_rect():
    hwnd = FindWindowW("Shell_TrayWnd", None)
    if not hwnd:
        return None
    r = wt.RECT()
    GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom

def _is_fullscreen(hwnd) -> bool:
    if not hwnd:
        return False
    cls_buf = ctypes.create_unicode_buffer(256)
    GetClassNameW(hwnd, cls_buf, 256)
    if cls_buf.value in ("Progman", "WorkerW", "Shell_TrayWnd", "TrayNotifyWnd"):
        return False
    rect = wt.RECT()
    if not GetWindowRect(hwnd, ctypes.byref(rect)):
        return False
    hmon = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not hmon:
        return False
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if not GetMonitorInfoW(hmon, ctypes.byref(mi)):
        return False
    mon = mi.rcMonitor
    return (
        abs(rect.left   - mon.left)   <= 2 and
        abs(rect.top    - mon.top)    <= 2 and
        abs(rect.right  - mon.right)  <= 2 and
        abs(rect.bottom - mon.bottom) <= 2
    )

def is_foreground_fullscreen() -> bool:
    return _is_fullscreen(GetForegroundWindow())

# ============================================================
#  Виджет
# ============================================================
class TaskbarWidget:
    SIZE_COMPACT = (150, 30)
    SIZE_FULL    = (260, 56)

    HIST_LEN     = 45
    BAR_W        = 90
    BAR_H        = 14
    UPDATE_MS    = 1200
    FS_CHECK_MS  = 400

    SNAP_GRID    = 10
    SNAP_EDGE    = 60

    def __init__(self, master: tk.Tk):
        self.master = master
        theme.apply_palette()

        cfg = load_config()
        self.mode    = cfg["appearance"].get("widget_mode", "full")
        self.saved_x = cfg["appearance"].get("widget_x")
        
        # Инициализация stats для desktop_widget
        self.stats = monitor.get_stats()

        self.cpu_h = deque([0] * self.HIST_LEN, maxlen=self.HIST_LEN)
        self.ram_h = deque([0] * self.HIST_LEN, maxlen=self.HIST_LEN)

        self.cpu_anim = 0.0
        self.ram_anim = 0.0

        self._drag_offset_x = 0
        self._dragging = False
        self._hidden_by_fs = False
        self._tooltip = None
        self._tooltip_visible = False

        # Цвета
        self.C_BG    = theme.COLORS["TB_BG"]
        self.C_TRACK = theme.COLORS["TB_TRACK"]
        self.C_FG    = theme.COLORS["TB_FG"]
        self.C_DIM   = theme.COLORS["TB_DIM"]
        self.C_HIGHLIGHT = self._lighter(self.C_BG, 25)

        # --- ОКНО ---
        W, H = self._size_for_mode()
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        
        self.win.configure(bg="#000000")
        try: self.win.wm_attributes("-transparentcolor", "#000000")
        except Exception: pass
        self.win.geometry(f"{W}x{H}")

        self.canvas = tk.Canvas(
            self.win, width=W, height=H,
            bg=self.C_BG, highlightthickness=0, bd=0,
            cursor="fleur",
        )
        self.canvas.pack(fill="both", expand=True)

        self.win.update_idletasks()
        
        # СТЕКЛО (если включено в теме)
        self._apply_glass()

        self._apply_winapi_styles()
        self._place_on_taskbar(self.saved_x)

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>",        self._on_right_click)
        self.canvas.bind("<Enter>",           self._show_tooltip)
        self.canvas.bind("<Leave>",           self._hide_tooltip)

        s = monitor.get_stats()
        self.cpu_anim = float(s["cpu"])
        self.ram_anim = float(s["ram"])

        self.win.attributes("-alpha", 1.0)

        self._tick()
        self._animate_loop()
        self._fs_watch()
        self._register_hotkeys()

    @staticmethod
    def _lighter(hex_color: str, amount: int) -> str:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _apply_glass(self):
        hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
        self.win.attributes("-alpha", 1.0)
        if theme.is_glass():
            win_blur.enable_blur(hwnd, dark_mode=theme.is_dark_theme(), tint_color=self.C_BG, alpha=theme.get_tint_alpha())
        else:
            win_blur.disable_blur(hwnd)

    def apply_theme(self):
        self.C_BG    = theme.COLORS["TB_BG"]
        self.C_TRACK = theme.COLORS["TB_TRACK"]
        self.C_FG    = theme.COLORS["TB_FG"]
        self.C_DIM   = theme.COLORS["TB_DIM"]
        self.C_HIGHLIGHT = self._lighter(self.C_BG, 25)
        self.canvas.configure(bg=self.C_BG)
        self.win.configure(bg="#000000")
        try: self.win.wm_attributes("-transparentcolor", "#000000")
        except Exception: pass
        self._apply_glass()
        self._draw()

    def is_user_visible(self) -> bool:
        return self.win.state() != "withdrawn"

    def set_visibility(self, visible: bool):
        if visible:
            self.win.deiconify()
            self.win.attributes("-topmost", True)
            self._hidden_by_fs = False
        else:
            self.win.withdraw()

    def _register_hotkeys(self):
        from config_manager import load_config
        try:
            import keyboard
            keyboard.remove_all_hotkeys()
        except Exception: pass
        cfg = load_config()["hotkeys"]
        hotkeys.register(cfg["compact"], lambda: self.master.after(0, self._set_mode, "compact"))
        hotkeys.register(cfg["full"], lambda: self.master.after(0, self._set_mode, "full"))
        hotkeys.register(cfg["toggle"], lambda: self.master.after(0, self._toggle_visibility))
        hotkeys.register(cfg["screenshot"], self._screenshot)

    def _screenshot(self):
        from features.screenshot import grab_region
        self.master.after(0, lambda: grab_region(master=self.master, copy_to_clipboard=True))

    def _set_mode(self, mode: str):
        if self.mode == mode: return
        self.mode = mode
        W, H = self._size_for_mode()
        self.canvas.configure(width=W, height=H)
        x, y = self.win.winfo_x(), self.win.winfo_y()
        self.win.geometry(f"{W}x{H}+{x}+{y}")
        self._save_position()
        self._draw()

    def _toggle_visibility(self):
        if self.win.state() == "withdrawn":
            self.win.deiconify()
            self.win.attributes("-topmost", True)
        else:
            self.win.withdraw()

    def _fs_watch(self):
        try:
            fs = is_foreground_fullscreen()
            if fs and not self._hidden_by_fs:
                self.win.withdraw()
                self._hidden_by_fs = True
            elif not fs and self._hidden_by_fs:
                self.win.deiconify()
                self.win.attributes("-topmost", True)
                self._hidden_by_fs = False
        except Exception: pass
        self.win.after(self.FS_CHECK_MS, self._fs_watch)

    def _size_for_mode(self):
        return self.SIZE_COMPACT if self.mode == "compact" else self.SIZE_FULL

    def _toggle_mode(self):
        self._set_mode("compact" if self.mode == "full" else "full")

    def _apply_winapi_styles(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            ex = GetWindowLongW(hwnd, GWL_EXSTYLE)
            SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        except Exception: pass

    def _place_on_taskbar(self, saved_x=None):
        rect = get_taskbar_rect()
        W, H = self._size_for_mode()
        if not rect:
            sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
            self.win.geometry(f"{W}x{H}+{sw - 500}+{sh - H - 10}")
            return
        left, top, right, bottom = rect
        h = bottom - top
        if saved_x is None:
            x = right - 320 - W
        else:
            x = max(left, min(saved_x, right - W))
        y = top + (h - H) // 2
        self.win.geometry(f"{W}x{H}+{x}+{y}")

    def _save_position(self):
        cfg = load_config()
        cfg["appearance"]["widget_mode"] = self.mode
        cfg["appearance"]["widget_x"] = self.win.winfo_x()
        cfg["appearance"]["widget_y"] = self.win.winfo_y()
        save_config(cfg)

    def _reset_position(self):
        self._place_on_taskbar(None)
        self._save_position()

    def _on_press(self, event):
        self._drag_offset_x = event.x_root - self.win.winfo_x()
        self._dragging = False
        self.win.attributes("-alpha", 0.8)

    def _on_drag(self, event):
        self._dragging = True
        W, _ = self._size_for_mode()
        rect = get_taskbar_rect()
        if not rect: return
        left, top, right, bottom = rect
        new_x = event.x_root - self._drag_offset_x
        new_x = max(left, min(new_x, right - W))
        y = self.win.winfo_y()
        dist_left = new_x - left
        dist_right = (right - W) - new_x
        if dist_left <= self.SNAP_EDGE or dist_right <= self.SNAP_EDGE:
            self.canvas.configure(bg=self.C_HIGHLIGHT)
        else:
            self.canvas.configure(bg=self.C_BG)
        self.win.geometry(f"+{new_x}+{y}")

    def _on_release(self, event):
        self.win.attributes("-alpha", 1.0)
        self.canvas.configure(bg=self.C_BG)
        if not self._dragging:
            self._open_main()
            return
        W, _ = self._size_for_mode()
        rect = get_taskbar_rect()
        x, y = self.win.winfo_x(), self.win.winfo_y()
        if rect:
            left, top, right, bottom = rect
            dist_left = x - left
            dist_right = (right - W) - x
            if dist_left <= self.SNAP_EDGE: x = left
            elif dist_right <= self.SNAP_EDGE: x = right - W
            else: x = round(x / self.SNAP_GRID) * self.SNAP_GRID
            x = max(left, min(x, right - W))
        self.win.geometry(f"+{x}+{y}")
        self._save_position()
        self._dragging = False

    def _open_main(self):
        try: self.master.after(0, self._do_open_main)
        except Exception: pass

    def _do_open_main(self):
        try:
            self.master.deiconify()
            self.master.lift()
            self.master.focus_force()
        except Exception: pass

    def _show_tooltip(self, _event):
        if self._tooltip_visible: return
        s = monitor.get_stats()
        lines = [
            f"{tr('CPU')}     {s['cpu']}%", 
            f"{tr('RAM')}     {s['ram']}%  ({s['ram_used_gb']}/{s['ram_total_gb']} GB)"
        ]
        if s.get("gpu") is not None: 
            lines.append(f"{tr('GPU')}     {s['gpu']}%")
        lines.append(f"{tr('Диск')}    {monitor.format_speed(s['disk'])}")
        lines.append(f"{tr('Сеть')} ↓  {monitor.format_speed(s['net_down'])}")
        lines.append(f"{tr('Сеть')} ↑  {monitor.format_speed(s['net_up'])}")
        if s.get("battery") is not None:
            lines.append(f"{tr('Батарея')} {s['battery']}%  {'⚡' if s['plugged'] else '🔋'}")
        
        text = "\n".join(lines)
        tip = tk.Toplevel(self.win)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        lbl = tk.Label(tip, text=text, justify="left", bg=self.C_BG, fg=self.C_FG, font=("Cascadia Mono", 9), padx=10, pady=8, bd=1, relief="solid")
        lbl.pack()
        tip.update_idletasks()
        tw, th = tip.winfo_width(), tip.winfo_height()
        x = self.win.winfo_x() + (self.win.winfo_width() - tw) // 2
        y = self.win.winfo_y() - th - 6
        tip.geometry(f"+{x}+{y}")
        self._tooltip = tip
        self._tooltip_visible = True

    def _hide_tooltip(self, _event=None):
        if self._tooltip is not None:
            try: self._tooltip.destroy()
            except Exception: pass
            self._tooltip = None
        self._tooltip_visible = False

    def _on_right_click(self, event):
        from config_manager import load_config
        cfg = load_config()["hotkeys"]
        menu = tk.Menu(self.win, tearoff=0, bg=self.C_BG, fg=self.C_FG, activebackground=self.C_TRACK, activeforeground="#4ade80", bd=0, relief="flat", font=("Segoe UI", 10))
        
        mode_label = tr("Компактный") if self.mode == "full" else tr("Полный")
        compact_hk = cfg.get("compact", "ctrl+alt+c").upper()
        full_hk = cfg.get("full", "ctrl+alt+f").upper()
        
        menu.add_command(label=f"{tr('Режим')}: {mode_label}", command=self._toggle_mode)
        menu.add_separator()
        menu.add_command(label=f"{tr('Компакт')} ({compact_hk})", command=lambda: self._set_mode("compact"))
        menu.add_command(label=f"{tr('Полный')} ({full_hk})", command=lambda: self._set_mode("full"))
        menu.add_separator()
        menu.add_command(label=tr("Сбросить позицию"), command=self._reset_position)
        menu.add_separator()
        menu.add_command(label=tr("Открыть окно"), command=self._open_main)
        menu.add_separator()
        menu.add_command(label=tr("Выход"), command=self._quit)
        try: menu.tk_popup(event.x_root, event.y_root)
        finally: menu.grab_release()

    def _quit(self):
        try: self.master.after(0, self.master.quit)
        except Exception: pass

    def _tick(self):
        s = monitor.get_stats()
        self.stats = s  # <--- ОБНОВЛЯЕМ СТАТЫ ЗДЕСЬ
        self.cpu_h.append(s["cpu"])
        self.ram_h.append(s["ram"])
        self.win.after(self.UPDATE_MS, self._tick)

    def _animate_loop(self):
        cpu_target = self.cpu_h[-1]
        ram_target = self.ram_h[-1]
        self.cpu_anim += (cpu_target - self.cpu_anim) * 0.25
        self.ram_anim += (ram_target - self.ram_anim) * 0.25
        if abs(cpu_target - self.cpu_anim) < 0.3: self.cpu_anim = cpu_target
        if abs(ram_target - self.ram_anim) < 0.3: self.ram_anim = ram_target
        self._draw()
        self.win.after(80, self._animate_loop)

    def _draw(self):
        c = self.canvas
        c.delete("all")
        W, H = self._size_for_mode()
        c.create_rectangle(0, 0, W, H, fill=self.C_BG, outline="")
        if theme.is_glass():
            c.create_rectangle(0, 0, W - 1, H - 1, outline=theme.COLORS["LINE"])
            c.create_rectangle(2, 2, W - 3, H - 3, outline=theme.COLORS["GLOSS"])
        cpu_val = int(round(self.cpu_anim))
        ram_val = int(round(self.ram_anim))
        if self.mode == "compact": self._draw_compact(cpu_val, ram_val)
        else: self._draw_full(cpu_val, ram_val)

    def _draw_compact(self, cpu, ram):
        c = self.canvas
        W, H = self.SIZE_COMPACT
        mid = H // 2
        c.create_text(14, mid, text="CPU", anchor="w", fill=self.C_DIM, font=("Segoe UI", 8, "bold"))
        c.create_text(40, mid, text=f"{cpu:>3}%", anchor="w", fill=color_for(cpu), font=("Cascadia Mono", 11, "bold"))
        c.create_text(W // 2, mid, text="·", anchor="center", fill=self.C_TRACK, font=("Segoe UI", 12))
        c.create_text(W // 2 + 12, mid, text="RAM", anchor="w", fill=self.C_DIM, font=("Segoe UI", 8, "bold"))
        c.create_text(W // 2 + 38, mid, text=f"{ram:>3}%", anchor="w", fill=color_for(ram), font=("Cascadia Mono", 11, "bold"))

    def _draw_full(self, cpu, ram):
        c = self.canvas
        W, H = self.SIZE_FULL
        self._draw_metric(x=12, y=22, name="CPU", value=cpu, hist=self.cpu_h)
        c.create_line(130, 6, 130, 40, fill=self.C_TRACK)
        self._draw_metric(x=142, y=22, name="RAM", value=ram, hist=self.ram_h)
        s = monitor.get_stats()
        parts = []
        if s.get("gpu") is not None: parts.append(f"GPU {s['gpu']}%")
        parts.append(f"D {monitor.format_speed(s['disk'])}")
        parts.append(f"↓ {monitor.format_speed(s['net_down'])}")
        parts.append(f"↑ {monitor.format_speed(s['net_up'])}")
        info = "  ·  ".join(parts)
        c.create_text(W // 2, H - 10, text=info, anchor="center", fill=self.C_DIM, font=("Cascadia Mono", 8))

    def _draw_metric(self, x, y, name, value, hist):
        c = self.canvas
        color = color_for(value)
        c.create_text(x, y - 9, text=name, anchor="w", fill=self.C_DIM, font=("Segoe UI", 8, "bold"))
        c.create_text(x + 28, y - 9, text=f"{value:>3}%", anchor="w", fill=color, font=("Cascadia Mono", 11, "bold"))
        gw, gh = self.BAR_W, self.BAR_H
        gy = y - gh // 2 + 6
        n = len(hist)
        if n < 2: return
        step = gw / (n - 1)
        pts = []
        for i, v in enumerate(hist):
            px = x + i * step
            py = gy + gh - (v / 100.0) * gh
            pts.extend([px, py])
        poly = [x, gy + gh] + pts + [x + gw, gy + gh]
        c.create_polygon(poly, fill=color, outline="", stipple="gray50")
        c.create_line(pts, fill=color, width=2, smooth=True, splinesteps=12)
        last_x = x + gw
        last_y = gy + gh - (value / 100.0) * gh
        c.create_oval(last_x - 3, last_y - 3, last_x + 3, last_y + 3, fill=color, outline=self.C_BG, width=1.5)

    def destroy(self):
        self._hide_tooltip()
        try: self._save_position()
        except Exception: pass
        try: self.win.destroy()
        except Exception: pass