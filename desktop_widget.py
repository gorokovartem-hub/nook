"""Независимые виджеты рабочего стола: система, диски и часы."""

import ctypes
import time
import tkinter as tk

import psutil

import theme
from taskbar_widget import load_config, save_config

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
HWND_BOTTOM = 1
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]
WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница",
            "Суббота", "Воскресенье"]

GIB = 1024 ** 3
WIDGETS = ("sys", "disk", "clock")
TITLES = {"sys": "СИСТЕМА", "disk": "ДИСКИ", "clock": "ЧАСЫ"}


class DesktopWidget:
    W = 250
    MARGIN = 16
    GAP = 8
    PAD = 14
    HEAD_H = 34
    ROW_H = 32
    CLOCK_H = 116
    RADIUS = 12
    KEY_COLOR = "#010203"
    TICK_MS = 1000
    KEEP_MS = 3000
    DISK_REFRESH_S = 30
    DRAG_THRESHOLD = 3
    SNAP_DISTANCE = 18
    SNAP_GAP = 8

    def __init__(self, master: tk.Tk, stats_source=None):
        """stats_source returns a dictionary compatible with monitor.get_stats()."""
        self.master = master
        self.stats_source = stats_source
        self._alive = True
        self._global_hidden = False
        self._disks = []
        self._disks_ts = 0.0

        cfg = load_config().get("desktop_widget", {})
        if not isinstance(cfg, dict):
            cfg = {}
        self._global_hidden = not cfg.get("visible", True)
        saved_widgets = cfg.get("widgets", {})
        if not isinstance(saved_widgets, dict):
            saved_widgets = {}

        self._refresh_disks(force=True)
        screen_w = master.winfo_screenwidth()
        legacy_x = cfg.get("x")
        legacy_y = cfg.get("y")
        default_x = legacy_x if isinstance(legacy_x, int) else screen_w - self.W - self.MARGIN
        default_y = legacy_y if isinstance(legacy_y, int) else self.MARGIN
        offsets = {
            "sys": 0,
            "disk": self.HEAD_H + 3 * self.ROW_H + 6 + self.GAP,
            "clock": (self.HEAD_H + 3 * self.ROW_H + 6 + self.GAP)
                     + (self.HEAD_H + max(1, len(self._disks)) * self.ROW_H + 6
                        + self.GAP),
        }

        theme.apply_palette()
        self.windows = {}
        for key in WIDGETS:
            saved = saved_widgets.get(key, {})
            if not isinstance(saved, dict):
                saved = {}
            x = saved.get("x", default_x)
            y = saved.get("y", default_y + offsets[key])
            visible = bool(saved.get("visible", True))
            self._create_widget(key, x, y, visible)

        self._tick()
        self._keep_loop()

    def _create_widget(self, key, x, y, visible):
        height = self._height(key)
        win = tk.Toplevel(self.master)
        win.overrideredirect(True)
        win.configure(bg=self.KEY_COLOR)
        win.attributes("-alpha", 0.0)
        try:
            win.attributes("-transparentcolor", self.KEY_COLOR)
        except tk.TclError:
            pass
        canvas = tk.Canvas(
            win, width=self.W, height=height, bg=self.KEY_COLOR,
            highlightthickness=0, bd=0,
        )
        canvas.pack(fill="both", expand=True)
        state = {
            "win": win,
            "canvas": canvas,
            "visible": visible,
            "press": None,
            "dragging": False,
        }
        self.windows[key] = state
        x, y = self._clamp(key, x, y)
        win.geometry(f"{self.W}x{height}+{x}+{y}")
        win.update_idletasks()
        self._apply_winapi_styles(win)
        canvas.bind("<ButtonPress-1>", lambda event, k=key: self._on_press(k, event))
        canvas.bind("<B1-Motion>", lambda event, k=key: self._on_drag(k, event))
        canvas.bind("<ButtonRelease-1>", lambda event, k=key: self._on_release(k, event))
        canvas.bind("<Button-3>", lambda event, k=key: self._on_right_click(k, event))
        self._draw(key)
        if self._global_hidden or not visible:
            win.withdraw()
        win.attributes("-alpha", theme.get_opacity())
        self._send_bottom(win)

    def _ok(self):
        return self._alive

    def _apply_winapi_styles(self, win):
        try:
            hwnd = user32.GetParent(win.winfo_id())
            ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        except Exception as e:
            print("desktop_widget styles:", e)

    @staticmethod
    def _send_bottom(win):
        try:
            hwnd = user32.GetParent(win.winfo_id())
            user32.SetWindowPos(
                hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        except Exception as e:
            print("desktop_widget z-order:", e)

    @staticmethod
    def _round_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _stats(self):
        if self.stats_source:
            try:
                stats = self.stats_source()
                if stats:
                    return stats
            except Exception as e:
                print("desktop_widget stats source:", e)
        try:
            from features import monitor
            return monitor.get_stats()
        except Exception as e:
            print("desktop_widget monitor:", e)
            return {"cpu": 0, "ram": 0}

    def _refresh_disks(self, force=False):
        now = time.time()
        if not force and now - self._disks_ts < self.DISK_REFRESH_S:
            return
        self._disks_ts = now
        disks = []
        try:
            for partition in psutil.disk_partitions(all=False):
                if "cdrom" in partition.opts or not partition.fstype:
                    continue
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                except OSError:
                    continue
                name = partition.device.rstrip("\\/")
                disks.append((name, usage.used / GIB, usage.total / GIB))
        except Exception as e:
            print("desktop_widget disks:", e)
        self._disks = disks[:5]

    def _height(self, key):
        if key == "sys":
            return self.HEAD_H + 3 * self.ROW_H + 6
        if key == "disk":
            return self.HEAD_H + max(1, len(self._disks)) * self.ROW_H + 6
        return self.CLOCK_H

    def _clamp(self, key, x, y):
        win = self.windows[key]["win"]
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        height = self._height(key)
        x = max(0, min(int(x), screen_w - self.W))
        y = max(0, min(int(y), screen_h - height))
        return x, y

    def _snap_position(self, key, x, y):
        win = self.windows[key]["win"]
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        height = self._height(key)
        x, y = self._clamp(key, x, y)

        x_targets = [self.MARGIN, screen_w - self.W - self.MARGIN]
        y_targets = [self.MARGIN, screen_h - height - self.MARGIN]
        for other_key, state in self.windows.items():
            if other_key == key or not state["visible"]:
                continue
            other = state["win"]
            other_x, other_y = other.winfo_x(), other.winfo_y()
            other_h = self._height(other_key)
            x_targets.extend((
                other_x,
                other_x + self.W - self.W,
                other_x + self.W + self.SNAP_GAP,
                other_x - self.W - self.SNAP_GAP,
            ))
            y_targets.extend((
                other_y,
                other_y + other_h - height,
                other_y + other_h + self.SNAP_GAP,
                other_y - height - self.SNAP_GAP,
            ))

        def closest_snap(value, targets, maximum):
            nearby = [
                target for target in targets
                if 0 <= target <= maximum
                and abs(value - target) <= self.SNAP_DISTANCE
            ]
            return min(nearby, key=lambda target: abs(value - target)) if nearby else value

        x = closest_snap(x, x_targets, screen_w - self.W)
        y = closest_snap(y, y_targets, screen_h - height)
        return self._clamp(key, x, y)

    def _draw(self, key, stats=None):
        state = self.windows[key]
        canvas = state["canvas"]
        palette = theme.COLORS
        height = self._height(key)
        canvas.configure(height=height)
        canvas.delete("all")
        self._round_rect(
            canvas, 1, 1, self.W - 1, height - 1,
            min(theme.get_corner_radius(), height // 2),
            fill=palette["CARD"], outline=palette["LINE"],
        )
        canvas.create_text(
            self.PAD, self.HEAD_H // 2 + 1, text=TITLES[key], anchor="w",
            fill=palette["FG"], font=("Segoe UI Semibold", 9),
        )

        if key == "sys":
            stats = stats or self._stats()
            gpu = stats.get("gpu")
            values = [
                ("CPU", stats.get("cpu", 0)),
                ("RAM", stats.get("ram", 0)),
                ("GPU", gpu),
            ]
            for index, (label, value) in enumerate(values):
                display = f"{value}%" if value is not None else "—"
                self._metric_row(canvas, self.HEAD_H + index * self.ROW_H,
                                 label, value, display)
        elif key == "disk":
            self._refresh_disks()
            if not self._disks:
                canvas.create_text(
                    self.PAD, self.HEAD_H + 14, text="нет данных", anchor="w",
                    fill=palette["FG_DIM"], font=("Segoe UI", 9),
                )
            for index, (name, used, total) in enumerate(self._disks):
                pct = used / total * 100 if total else 0
                self._metric_row(
                    canvas, self.HEAD_H + index * self.ROW_H, name, pct,
                    f"{used:.0f} GB / {total:.0f} GB",
                )
        else:
            current = time.localtime()
            canvas.create_text(
                self.PAD, 18, text="ЧАСЫ", anchor="w",
                fill=palette["FG_DIM"], font=("Segoe UI Semibold", 9),
            )
            canvas.create_text(
                self.PAD, 52, text=time.strftime("%H:%M", current), anchor="w",
                fill=palette["FG"], font=("Segoe UI Light", 28),
            )
            canvas.create_text(
                self.PAD, 85,
                text=f"{current.tm_mday} {MONTHS[current.tm_mon - 1]} {current.tm_year}",
                anchor="w", fill=palette["FG"], font=("Segoe UI", 9),
            )
            canvas.create_text(
                self.PAD, 102, text=WEEKDAYS[current.tm_wday], anchor="w",
                fill=palette["FG_DIM"], font=("Segoe UI", 9),
            )

    def _metric_row(self, canvas, y, label, pct, value_text):
        palette = theme.COLORS
        canvas.create_text(
            self.PAD, y + 8, text=label, anchor="w",
            fill=palette["FG_DIM"], font=("Segoe UI", 9),
        )
        canvas.create_text(
            self.W - self.PAD, y + 8, text=value_text, anchor="e",
            fill=palette["FG"], font=("Segoe UI", 9),
        )
        x1, x2, bar_y = self.PAD, self.W - self.PAD, y + 24
        canvas.create_line(
            x1, bar_y, x2, bar_y, width=4, capstyle="round",
            fill=palette["FG_FAINT"],
        )
        if pct:
            pct = max(0.0, min(100.0, float(pct)))
            fill_x = x1 + (x2 - x1) * pct / 100
            if fill_x - x1 >= 2:
                color = palette["BAD"] if pct >= 85 else palette["FG"]
                canvas.create_line(
                    x1, bar_y, fill_x, bar_y, width=4, capstyle="round",
                    fill=color,
                )

    def _tick(self):
        if not self._alive:
            return
        try:
            if not self._global_hidden:
                self._refresh_disks()
                stats = self._stats() if self.windows["sys"]["visible"] else None
                for key, state in self.windows.items():
                    if not state["visible"]:
                        continue
                    height = self._height(key)
                    win = state["win"]
                    if win.winfo_height() != height:
                        x, y = self._clamp(key, win.winfo_x(), win.winfo_y())
                        win.geometry(f"{self.W}x{height}+{x}+{y}")
                    self._draw(key, stats)
        except tk.TclError:
            self._alive = False
            return
        self.master.after(self.TICK_MS, self._tick)

    def _keep_loop(self):
        if not self._alive:
            return
        try:
            if not self._global_hidden:
                for state in self.windows.values():
                    if state["visible"] and not state["dragging"]:
                        self._send_bottom(state["win"])
            self.master.after(self.KEEP_MS, self._keep_loop)
        except tk.TclError:
            self._alive = False

    def _on_press(self, key, event):
        state = self.windows[key]
        state["press"] = (
            event.x_root, event.y_root,
            state["win"].winfo_x(), state["win"].winfo_y(),
        )
        state["dragging"] = False

    def _on_drag(self, key, event):
        state = self.windows[key]
        press = state["press"]
        if not press:
            return
        px, py, wx, wy = press
        if not state["dragging"]:
            if (abs(event.x_root - px) < self.DRAG_THRESHOLD and
                    abs(event.y_root - py) < self.DRAG_THRESHOLD):
                return
            state["dragging"] = True
        x, y = self._snap_position(
            key, wx + event.x_root - px, wy + event.y_root - py)
        state["win"].geometry(f"+{x}+{y}")

    def _on_release(self, key, _event):
        state = self.windows[key]
        was_dragging = state["dragging"]
        state["press"] = None
        state["dragging"] = False
        if was_dragging:
            win = state["win"]
            x, y = self._snap_position(key, win.winfo_x(), win.winfo_y())
            win.geometry(f"+{x}+{y}")
            self._save()
            self._send_bottom(win)

    def _on_right_click(self, key, event):
        palette = theme.COLORS
        menu = tk.Menu(
            self.windows[key]["win"], tearoff=0,
            bg=palette["TB_BG"], fg=palette["TB_FG"],
            activebackground=palette["TB_TRACK"],
            activeforeground=palette["GOOD"],
            bd=0, relief="flat", font=("Segoe UI", 10),
        )
        menu.add_command(
            label="Сбросить позиции карточек", command=self.reset_position)
        menu.add_command(
            label="Скрыть эту карточку",
            command=lambda: self.set_widget_visibility(key, False))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def is_visible(self):
        return not self._global_hidden

    def apply_theme(self):
        for key, state in self.windows.items():
            state["win"].attributes("-alpha", theme.get_opacity())
            self._draw(key)

    def set_visibility(self, visible):
        self._global_hidden = not bool(visible)
        for key, state in self.windows.items():
            if self._global_hidden or not state["visible"]:
                state["win"].withdraw()
            else:
                state["win"].deiconify()
                self._draw(key)
                self._send_bottom(state["win"])
        self._save()

    def is_widget_visible(self, key):
        return self.windows[key]["visible"]

    def set_widget_visibility(self, key, visible):
        state = self.windows[key]
        state["visible"] = bool(visible)
        if self._global_hidden or not state["visible"]:
            state["win"].withdraw()
        else:
            state["win"].deiconify()
            self._draw(key)
            self._send_bottom(state["win"])
        self._save()

    def get_layout(self):
        return {
            "visible": self.is_visible(),
            "widgets": {
                key: {
                    "x": state["win"].winfo_x(),
                    "y": state["win"].winfo_y(),
                    "visible": state["visible"],
                }
                for key, state in self.windows.items()
            },
        }

    def apply_layout(self, layout):
        if not isinstance(layout, dict):
            return
        saved_widgets = layout.get("widgets", {})
        if not isinstance(saved_widgets, dict):
            saved_widgets = {}
        for key, state in self.windows.items():
            saved = saved_widgets.get(key, {})
            if isinstance(saved, dict):
                x, y = saved.get("x"), saved.get("y")
                if isinstance(x, int) and isinstance(y, int):
                    x, y = self._clamp(key, x, y)
                    state["win"].geometry(f"+{x}+{y}")
                if "visible" in saved:
                    state["visible"] = bool(saved["visible"])
        self._global_hidden = not bool(layout.get("visible", True))
        self.set_visibility(not self._global_hidden)

    def reset_position(self):
        screen_w = self.master.winfo_screenwidth()
        default_x = screen_w - self.W - self.MARGIN
        positions = {
            "sys": self.MARGIN,
            "disk": self.MARGIN + self.HEAD_H + 3 * self.ROW_H + 6 + self.GAP,
            "clock": self.MARGIN + (self.HEAD_H + 3 * self.ROW_H + 6 + self.GAP)
                     + (self.HEAD_H + max(1, len(self._disks)) * self.ROW_H + 6
                        + self.GAP),
        }
        self._global_hidden = False
        for key, state in self.windows.items():
            state["visible"] = True
            x, y = self._clamp(key, default_x, positions[key])
            state["win"].geometry(f"{self.W}x{self._height(key)}+{x}+{y}")
            state["win"].deiconify()
            self._draw(key)
            self._send_bottom(state["win"])
        self._save()

    def destroy(self):
        self._alive = False
        try:
            self._save()
        except tk.TclError:
            pass
        for state in self.windows.values():
            try:
                state["win"].destroy()
            except tk.TclError:
                pass

    def _save(self):
        try:
            config = load_config()
            config["desktop_widget"] = {
                "visible": not self._global_hidden,
                "widgets": {
                    key: {
                        "x": state["win"].winfo_x(),
                        "y": state["win"].winfo_y(),
                        "visible": state["visible"],
                    }
                    for key, state in self.windows.items()
                },
            }
            save_config(config)
        except (tk.TclError, OSError) as e:
            print("desktop_widget save:", e)
