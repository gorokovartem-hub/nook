"""Виджет CPU/RAM/GPU/диск/сеть на панели задач."""
import ctypes
import ctypes.wintypes as wt
import json
import tkinter as tk
import tkinter.font as tkfont
from collections import deque
from pathlib import Path

from features import monitor, hotkeys
import theme


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
    """Цвет по загрузке — из текущей палитры (читаем в момент вызова)."""
    pal = theme.COLORS
    if v < 50:
        return pal["GOOD"]
    if v < 80:
        return pal["WARN"]
    return pal["BAD"]


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
#  Конфиг
# ============================================================
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print("save_config:", e)


# ============================================================
#  Виджет
# ============================================================
class TaskbarWidget:
    SIZE_COMPACT = (150, 30)
    SIZE_FULL    = (260, 56)

    HIST_LEN     = 45
    BAR_W        = 100
    BAR_H        = 14
    UPDATE_MS    = 1200
    FS_CHECK_MS  = 400
    ANIM_MS      = 60
    KEEP_MS      = 2000      # переутверждаем topmost и позицию
    TIP_DELAY_MS = 350
    DRAG_THRESHOLD = 3       # px: меньше — это клик, а не перетаскивание
    RADIUS       = 9

    SNAP_GRID    = 10
    SNAP_EDGE    = 60

    # цвет-ключ прозрачности (вокруг скруглённой «таблетки»)
    KEY_COLOR    = "#010203"

    def __init__(self, master: tk.Tk):
        self.master = master

        theme.apply_palette()

        cfg = load_config().get("taskbar_widget", {})
        self.mode = cfg.get("mode", "full")
        if self.mode not in ("compact", "full"):
            self.mode = "full"
        self.saved_x = cfg.get("x", None)

        self._alive = True
        self._dirty = True

        self.stats = {
            "cpu": 0, "ram": 0, "ram_used_gb": 0, "ram_total_gb": 0,
            "disk": 0, "net_down": 0, "net_up": 0,
            "battery": None, "plugged": False,
        }
        self._poll()

        self.cpu_h = deque([0] * self.HIST_LEN, maxlen=self.HIST_LEN)
        self.ram_h = deque([0] * self.HIST_LEN, maxlen=self.HIST_LEN)
        self.cpu_anim = float(self.stats["cpu"])
        self.ram_anim = float(self.stats["ram"])

        self._press_x = 0
        self._drag_offset_x = 0
        self._dragging = False
        self._hover = False
        self._hidden_by_fs = False
        self._hidden_by_user = False

        self._tooltip = None
        self._tooltip_label = None
        self._tooltip_job = None

        pal = theme.COLORS
        self.C_BG     = pal["TB_BG"]
        self.C_TRACK  = pal["TB_TRACK"]
        self.C_FG     = pal["TB_FG"]
        self.C_DIM    = pal["TB_DIM"]
        self.C_BORDER = self.C_TRACK
        self.C_HOVER     = self._shade(self.C_BG, 10)
        self.C_HIGHLIGHT = self._shade(self.C_BG, 25)
        self._bg_now = self.C_BG

        W, H = self._size_for_mode()
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.configure(bg=self.KEY_COLOR)
        try:
            self.win.attributes("-transparentcolor", self.KEY_COLOR)
        except tk.TclError:
            pass
        self.win.geometry(f"{W}x{H}")

        self.canvas = tk.Canvas(
            self.win, width=W, height=H,
            bg=self.KEY_COLOR, highlightthickness=0, bd=0,
            cursor="fleur",
        )
        self.canvas.pack(fill="both", expand=True)

        # шрифты нижней строки: подбираем размер под ширину
        self._info_fonts = {
            s: tkfont.Font(root=self.win, family="Cascadia Mono", size=s)
            for s in (8, 7, 6)
        }

        self.win.update_idletasks()
        self._apply_winapi_styles()
        self._place_on_taskbar(self.saved_x)

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>",        self._on_right_click)
        self.canvas.bind("<Enter>",           self._on_enter)
        self.canvas.bind("<Leave>",           self._on_leave)

        self.win.attributes("-alpha", 1.0)

        self._draw()
        self._tick()
        self._animate_loop()
        self._fs_watch()
        self._keep_loop()
        self._register_hotkeys()

    # --------------------------------------------------------
    #  утилиты
    # --------------------------------------------------------
    @staticmethod
    def _shade(hex_color: str, amount: int) -> str:
        """Чуть светлее на тёмном фоне и чуть темнее на светлом."""
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        lum = (r * 299 + g * 587 + b * 114) / 1000
        k = -amount if lum > 128 else amount
        r, g, b = (max(0, min(255, v + k)) for v in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _round_rect(c, x1, y1, x2, y2, r, **kw):
        pts = [
            x1 + r, y1,  x2 - r, y1,  x2, y1,
            x2, y1 + r,  x2, y2 - r,  x2, y2,
            x2 - r, y2,  x1 + r, y2,  x1, y2,
            x1, y2 - r,  x1, y1 + r,  x1, y1,
        ]
        return c.create_polygon(pts, smooth=True, **kw)

    def _ok(self) -> bool:
        if not self._alive:
            return False
        try:
            return bool(self.win.winfo_exists())
        except tk.TclError:
            self._alive = False
            return False

    def _after(self, ms, fn):
        if not self._ok():
            return
        try:
            self.win.after(ms, fn)
        except tk.TclError:
            self._alive = False

    def _visible(self) -> bool:
        return not (self._hidden_by_fs or self._hidden_by_user)

    def _poll(self):
        """Единственное место, где опрашиваем monitor.get_stats()."""
        try:
            self.stats = monitor.get_stats()
        except Exception as e:
            print("get_stats:", e)

    # ---------- хоткеи ----------
    def _register_hotkeys(self):
        hotkeys.register_all({
            "ctrl+alt+c": lambda: self.master.after(0, self._set_mode, "compact"),
            "ctrl+alt+f": lambda: self.master.after(0, self._set_mode, "full"),
            "ctrl+alt+w": lambda: self.master.after(0, self._toggle_visibility),
            "ctrl+alt+s": self._screenshot,
        })

    def _screenshot(self):
        from features.screenshot import grab_region
        self.master.after(0, lambda: grab_region(
            master=self.master,
            copy_to_clipboard=True,
        ))

    # ---------- режимы ----------
    def _size_for_mode(self):
        return self.SIZE_COMPACT if self.mode == "compact" else self.SIZE_FULL

    def _set_mode(self, mode: str):
        if self.mode == mode or not self._ok():
            return
        self.mode = mode
        W, H = self._size_for_mode()
        self.canvas.configure(width=W, height=H)
        self._apply_geometry(self.win.winfo_x())
        self._save_position()
        self._dirty = True
        self._draw()

    def _toggle_mode(self):
        self._set_mode("compact" if self.mode == "full" else "full")

    # ---------- видимость ----------
    def _sync_visibility(self):
        try:
            if self._visible():
                if self.win.state() == "withdrawn":
                    self.win.deiconify()
                self.win.attributes("-topmost", True)
                self._dirty = True
            else:
                self._hide_tooltip()
                if self.win.state() != "withdrawn":
                    self.win.withdraw()
        except tk.TclError:
            pass

    def _toggle_visibility(self):
        self._hidden_by_user = not self._hidden_by_user
        self._sync_visibility()

    def _fs_watch(self):
        if not self._ok():
            return
        try:
            fs = is_foreground_fullscreen()
            if fs != self._hidden_by_fs:
                self._hidden_by_fs = fs
                self._sync_visibility()
        except Exception as e:
            print("fs_watch:", e)
        self._after(self.FS_CHECK_MS, self._fs_watch)

    def _keep_loop(self):
        """Периодически: topmost поверх панели задач + подстройка позиции."""
        if not self._ok():
            return
        try:
            if self._visible() and not self._dragging:
                self.win.attributes("-topmost", True)
                self.win.lift()
                self._apply_geometry(self.win.winfo_x())
        except tk.TclError:
            pass
        self._after(self.KEEP_MS, self._keep_loop)

    # ---------- WinAPI ----------
    def _apply_winapi_styles(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            ex = GetWindowLongW(hwnd, GWL_EXSTYLE)
            SetWindowLongW(
                hwnd, GWL_EXSTYLE,
                ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
            )
        except Exception as e:
            print("winapi styles:", e)

    # ---------- позиционирование ----------
    def _apply_geometry(self, x=None):
        """Ставит окно по центру высоты панели, x — в пределах панели."""
        W, H = self._size_for_mode()
        rect = get_taskbar_rect()
        if not rect:
            return
        left, top, right, bottom = rect
        if x is None:
            x = right - 320 - W
        x = max(left, min(x, right - W))
        y = top + ((bottom - top) - H) // 2
        geo = f"{W}x{H}+{x}+{y}"
        if geo != self.win.geometry():
            self.win.geometry(geo)

    def _place_on_taskbar(self, saved_x=None):
        rect = get_taskbar_rect()
        W, H = self._size_for_mode()

        if not rect:
            sw = self.win.winfo_screenwidth()
            sh = self.win.winfo_screenheight()
            self.win.geometry(f"{W}x{H}+{sw - 500}+{sh - H - 10}")
            return

        self._apply_geometry(saved_x)

    def _save_position(self):
        cfg = load_config()
        cfg.setdefault("taskbar_widget", {})
        cfg["taskbar_widget"]["mode"] = self.mode
        cfg["taskbar_widget"]["x"] = self.win.winfo_x()
        save_config(cfg)

    def _reset_position(self):
        self._place_on_taskbar(None)
        self._save_position()

    # ---------- мышь ----------
    def _on_enter(self, _event):
        self._hover = True
        if not self._dragging:
            self._bg_now = self.C_HOVER
            self._dirty = True
            self._schedule_tooltip()

    def _on_leave(self, _event):
        self._hover = False
        self._hide_tooltip()
        if not self._dragging:
            self._bg_now = self.C_BG
            self._dirty = True

    def _on_press(self, event):
        self._press_x = event.x_root
        self._drag_offset_x = event.x_root - self.win.winfo_x()
        self._dragging = False
        self._hide_tooltip()
        self.win.attributes("-alpha", 0.7)

    def _on_drag(self, event):
        if not self._dragging:
            if abs(event.x_root - self._press_x) < self.DRAG_THRESHOLD:
                return
            self._dragging = True

        W, _ = self._size_for_mode()
        rect = get_taskbar_rect()
        if not rect:
            return
        left, top, right, bottom = rect

        new_x = event.x_root - self._drag_offset_x
        new_x = max(left, min(new_x, right - W))
        y = self.win.winfo_y()

        near_edge = (
            new_x - left <= self.SNAP_EDGE or
            (right - W) - new_x <= self.SNAP_EDGE
        )
        bg = self.C_HIGHLIGHT if near_edge else self.C_BG
        if bg != self._bg_now:
            self._bg_now = bg
            self._dirty = True
            self._draw()

        self.win.geometry(f"+{new_x}+{y}")

    def _on_release(self, event):
        self.win.attributes("-alpha", 1.0)
        self._bg_now = self.C_HOVER if self._hover else self.C_BG
        self._dirty = True

        if not self._dragging:
            self._draw()
            self._open_main()
            return

        W, _ = self._size_for_mode()
        rect = get_taskbar_rect()
        x = self.win.winfo_x()
        y = self.win.winfo_y()

        if rect:
            left, top, right, bottom = rect
            if x - left <= self.SNAP_EDGE:
                x = left
            elif (right - W) - x <= self.SNAP_EDGE:
                x = right - W
            else:
                x = round(x / self.SNAP_GRID) * self.SNAP_GRID
                x = max(left, min(x, right - W))

        self.win.geometry(f"+{x}+{y}")
        self._save_position()
        self._dragging = False
        self._draw()

    def _open_main(self):
        try:
            self.master.after(0, self._do_open_main)
        except Exception:
            pass

    def _do_open_main(self):
        try:
            self.master.deiconify()
            self.master.lift()
            self.master.focus_force()
        except Exception:
            pass

    # ---------- tooltip ----------
    def _tooltip_text(self) -> str:
        s = self.stats
        lines = [
            f"CPU     {s['cpu']}%",
            f"RAM     {s['ram']}%  ({s['ram_used_gb']}/{s['ram_total_gb']} GB)",
        ]
        if s.get("gpu") is not None:
            lines.append(f"GPU     {s['gpu']}%")
        lines.append(f"Диск    {monitor.format_speed(s['disk'])}")
        lines.append(f"Сеть ↓  {monitor.format_speed(s['net_down'])}")
        lines.append(f"Сеть ↑  {monitor.format_speed(s['net_up'])}")
        if s.get("battery") is not None:
            plug = "⚡" if s["plugged"] else "🔋"
            lines.append(f"Батарея {s['battery']}%  {plug}")
        return "\n".join(lines)

    def _schedule_tooltip(self):
        self._cancel_tooltip_job()
        self._tooltip_job = self.win.after(self.TIP_DELAY_MS, self._create_tooltip)

    def _cancel_tooltip_job(self):
        if self._tooltip_job is not None:
            try:
                self.win.after_cancel(self._tooltip_job)
            except Exception:
                pass
            self._tooltip_job = None

    def _create_tooltip(self):
        self._tooltip_job = None
        if self._tooltip is not None or self._dragging or not self._hover:
            return
        if not self._ok() or not self._visible():
            return

        tip = tk.Toplevel(self.win)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg=self.C_BORDER)      # 1px рамка через фон

        lbl = tk.Label(
            tip, text=self._tooltip_text(), justify="left",
            bg=self.C_BG, fg=self.C_FG,
            font=("Cascadia Mono", 9),
            padx=10, pady=8, bd=0,
        )
        lbl.pack(padx=1, pady=1)

        tip.update_idletasks()
        tw, th = tip.winfo_width(), tip.winfo_height()
        sw = tip.winfo_screenwidth()
        x = self.win.winfo_x() + (self.win.winfo_width() - tw) // 2
        x = max(4, min(x, sw - tw - 4))
        y = self.win.winfo_y() - th - 6
        if y < 0:  # панель сверху — показываем под виджетом
            y = self.win.winfo_y() + self.win.winfo_height() + 6
        tip.geometry(f"+{x}+{y}")

        self._tooltip = tip
        self._tooltip_label = lbl

    def _refresh_tooltip(self):
        if self._tooltip is not None and self._tooltip_label is not None:
            try:
                self._tooltip_label.configure(text=self._tooltip_text())
            except tk.TclError:
                pass

    def _hide_tooltip(self, _event=None):
        self._cancel_tooltip_job()
        if self._tooltip is not None:
            try:
                self._tooltip.destroy()
            except Exception:
                pass
            self._tooltip = None
            self._tooltip_label = None

    # ---------- контекстное меню ----------
    def _on_right_click(self, event):
        self._hide_tooltip()
        menu = tk.Menu(
            self.win, tearoff=0,
            bg=self.C_BG, fg=self.C_FG,
            activebackground=self.C_TRACK,
            activeforeground=theme.COLORS["GOOD"],
            bd=0, relief="flat",
            font=("Segoe UI", 10),
        )
        mode_label = "Компактный вид" if self.mode == "full" else "Полный вид"
        menu.add_command(label=mode_label, command=self._toggle_mode)
        menu.add_command(label="Сбросить позицию", command=self._reset_position)
        menu.add_command(label="Скрыть  (Ctrl+Alt+W)",
                         command=self._toggle_visibility)
        menu.add_separator()
        menu.add_command(label="Скриншот  (Ctrl+Alt+S)", command=self._screenshot)
        menu.add_command(label="Открыть окно", command=self._open_main)
        menu.add_separator()
        menu.add_command(label="Выход", command=self._quit)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _quit(self):
        try:
            self.master.after(0, self.master.quit)
        except Exception:
            pass

    # ---------- данные ----------
    def _tick(self):
        if not self._ok():
            return
        if self._visible() or self._tooltip is not None:
            self._poll()
            self.cpu_h.append(self.stats["cpu"])
            self.ram_h.append(self.stats["ram"])
            self._dirty = True
            self._refresh_tooltip()
        self._after(self.UPDATE_MS, self._tick)

    # ---------- анимация ----------
    @staticmethod
    def _ease(cur: float, target: float) -> float:
        cur += (target - cur) * 0.25
        return float(target) if abs(target - cur) < 0.3 else cur

    def _animate_loop(self):
        if not self._ok():
            return
        if self._visible():
            cpu = self._ease(self.cpu_anim, self.cpu_h[-1])
            ram = self._ease(self.ram_anim, self.ram_h[-1])
            if cpu != self.cpu_anim or ram != self.ram_anim:
                self._dirty = True
            self.cpu_anim, self.ram_anim = cpu, ram
            if self._dirty:
                self._draw()
        self._after(self.ANIM_MS, self._animate_loop)

    # ---------- рисование ----------
    def _draw(self):
        self._dirty = False
        c = self.canvas
        c.delete("all")

        W, H = self._size_for_mode()
        self._round_rect(
            c, 1, 1, W - 1, H - 1, self.RADIUS,
            fill=self._bg_now, outline=self.C_BORDER,
        )

        cpu_val = int(round(self.cpu_anim))
        ram_val = int(round(self.ram_anim))
        if self.mode == "compact":
            self._draw_compact(cpu_val, ram_val)
        else:
            self._draw_full(cpu_val, ram_val)

    def _draw_compact(self, cpu, ram):
        c = self.canvas
        W, H = self.SIZE_COMPACT
        mid = H // 2

        c.create_text(14, mid, text="CPU", anchor="w",
                      fill=self.C_DIM, font=("Segoe UI", 8, "bold"))
        c.create_text(40, mid, text=f"{cpu:>3}%", anchor="w",
                      fill=color_for(cpu), font=("Cascadia Mono", 11, "bold"))

        c.create_text(W // 2, mid, text="·", anchor="center",
                      fill=self.C_TRACK, font=("Segoe UI", 12))

        c.create_text(W // 2 + 12, mid, text="RAM", anchor="w",
                      fill=self.C_DIM, font=("Segoe UI", 8, "bold"))
        c.create_text(W // 2 + 38, mid, text=f"{ram:>3}%", anchor="w",
                      fill=color_for(ram), font=("Cascadia Mono", 11, "bold"))

    def _draw_full(self, cpu, ram):
        c = self.canvas
        W, H = self.SIZE_FULL

        self._draw_metric(x=12, y=22, name="CPU",
                          value=cpu, hist=self.cpu_h)
        c.create_line(130, 8, 130, 40, fill=self.C_TRACK)
        self._draw_metric(x=142, y=22, name="RAM",
                          value=ram, hist=self.ram_h)

        s = self.stats
        parts = []
        if s.get("gpu") is not None:
            parts.append(f"GPU {s['gpu']}%")
        parts.append(f"D {monitor.format_speed(s['disk'])}")
        parts.append(f"↓ {monitor.format_speed(s['net_down'])}")
        parts.append(f"↑ {monitor.format_speed(s['net_up'])}")
        info = "  ·  ".join(parts)

        # уменьшаем шрифт, пока строка не влезет в ширину виджета
        font = self._info_fonts[6]
        for size in (8, 7, 6):
            if self._info_fonts[size].measure(info) <= W - 16:
                font = self._info_fonts[size]
                break

        c.create_line(10, H - 19, W - 10, H - 19, fill=self.C_TRACK)
        c.create_text(
            W // 2, H - 9,
            text=info, anchor="center",
            fill=self.C_DIM, font=font,
        )

    def _draw_metric(self, x, y, name, value, hist):
        c = self.canvas
        color = color_for(value)

        c.create_text(x, y - 9, text=name, anchor="w",
                      fill=self.C_DIM, font=("Segoe UI", 8, "bold"))
        c.create_text(x + 28, y - 9, text=f"{value:>3}%", anchor="w",
                      fill=color, font=("Cascadia Mono", 11, "bold"))

        gw = self.BAR_W
        gh = self.BAR_H
        gy = y - gh // 2 + 6

        # базовая линия графика
        c.create_line(x, gy + gh, x + gw, gy + gh, fill=self.C_TRACK)

        n = len(hist)
        if n < 2:
            return

        step = gw / (n - 1)
        pts = []
        for i, v in enumerate(hist):
            v = max(0.0, min(100.0, float(v)))
            pts.extend([x + i * step, gy + gh - (v / 100.0) * gh])

        poly = [x, gy + gh] + pts + [x + gw, gy + gh]
        c.create_polygon(poly, fill=color, outline="", stipple="gray25")
        c.create_line(pts, fill=color, width=1.3,
                      smooth=True, splinesteps=12)

        cy = gy + gh - (max(0.0, min(100.0, float(value))) / 100.0) * gh
        c.create_oval(x + gw - 3, cy - 3, x + gw + 3, cy + 3,
                      fill=color, outline=self._bg_now, width=1)

    # ---------- очистка ----------
    def destroy(self):
        self._alive = False
        self._hide_tooltip()
        try:
            self._save_position()
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass