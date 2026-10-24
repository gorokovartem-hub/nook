"""Трей + тултип с CPU/RAM."""
import threading
import time
import pystray
from pystray import MenuItem as Item

from features import monitor
from i18n import tr
from icons import make_icon, color_by_load
from config_manager import load_config

class TrayApp:
    def __init__(self, window, clipboard, on_quit):
        self.window = window
        self.clipboard = clipboard
        self.on_quit = on_quit
        self._stop = threading.Event()
        
        # Создаём иконку с меню
        self.icon = pystray.Icon(
            "trayapp",
            icon=make_icon("#4ade80"),
            title="nook",
            menu=self._build_menu(),
        )

    def _build_menu(self):
        """Генерирует меню с актуальными хоткеями и переводами."""
        cfg = load_config()["hotkeys"]

        return pystray.Menu(
            Item(tr("открыть"), self._open, default=True),
            Item(tr("скриншот области"), self._screenshot),
            Item(tr("быстрая заметка"), self._quick_note),
            pystray.Menu.SEPARATOR,
            Item(lambda item: self._stats_item(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            Item(f"{tr('компакт')} ({cfg.get('compact', 'ctrl+alt+c').upper()})", 
                 lambda: self.window.taskbar_widget._set_mode("compact")),
            Item(f"{tr('полный')} ({cfg.get('full', 'ctrl+alt+f').upper()})", 
                 lambda: self.window.taskbar_widget._set_mode("full")),
            pystray.Menu.SEPARATOR,
            Item(tr("выход"), self._quit),
        )

    def refresh_menu(self):
        """Пересоздает меню (вызывается после смены хоткеев)."""
        if self.icon:
            self.icon.menu = self._build_menu()
            self.icon.update_menu()

    def _stats_item(self):
        s = monitor.get_stats()
        bat = f"  ·  bat {s['battery']}%" if s["battery"] is not None else ""
        return f"cpu {s['cpu']}%  ·  ram {s['ram']}%{bat}"

    def _open(self, icon, item):
        self.window.root.after(0, self.window.show)

    def _screenshot(self, icon=None, item=None):
        # игнорируем вызовы в первые 3 секунды после старта
        if not hasattr(self, "_started_at"):
            self._started_at = time.time()
        if time.time() - self._started_at < 3:
            print("[hotkey] игнорирую фальшивое срабатывание")
            return

        from features.screenshot import grab_region
        self.window.root.after(0, lambda: grab_region(
            master=self.window.root,
            copy_to_clipboard=True,
        ))

    def _quick_note(self, icon, item):
        self.window.root.after(0, self.window.show_quick_note)

    def _quit(self, icon, item):
        self._stop.set()
        self.icon.stop()
        self.window.root.after(0, self.on_quit)

    def _update_loop(self):
        while not self._stop.is_set():
            try:
                s = monitor.get_stats()
                self.icon.icon = make_icon(color_by_load(s["cpu"]))
                self.icon.title = f"cpu {s['cpu']}%  ·  ram {s['ram']}%"
                self.icon.update_menu()
            except Exception as e:
                print("monitor error:", e)
            time.sleep(1)

    def run(self):
        threading.Thread(target=self._update_loop, daemon=True).start()
        self.icon.run()