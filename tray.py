"""Трей + тултип с CPU/RAM."""
import threading
import time
import pystray
from pystray import MenuItem as Item

from features import monitor
from icons import make_icon, color_by_load


class TrayApp:
    def __init__(self, window, clipboard, on_quit):
        self.window = window
        self.clipboard = clipboard
        self.on_quit = on_quit
        self.icon = pystray.Icon(
            "trayapp",
            icon=make_icon("#4CAF50"),
            title="загрузка…",
            menu=self._build_menu(),
        )
        self._stop = threading.Event()

    def _build_menu(self):
        return pystray.Menu(
            Item("открыть", self._open, default=True),
            Item("скриншот области", self._screenshot),
            Item("быстрая заметка", self._quick_note),
            pystray.Menu.SEPARATOR,
            Item(lambda item: self._stats_item(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            Item("выход", self._quit),
        )

    def _stats_item(self):
        s = monitor.get_stats()
        bat = f"  ·  bat {s['battery']}%" if s["battery"] is not None else ""
        return f"cpu {s['cpu']}%  ·  ram {s['ram']}%{bat}"

    def _open(self, icon, item):
        self.window.root.after(0, self.window.show)

    def _screenshot(self):
        import time
        # игнорируем вызовы в первые 3 секунды после старта
        if not hasattr(self, "_started_at"):
            self._started_at = time.time()
        if time.time() - self._started_at < 3:
            print("[hotkey] игнорирую фальшивое срабатывание")
            return

        from features.screenshot import grab_region
        self.master.after(0, lambda: grab_region(
            master=self.master,
            copy_to_clipboard=True,
        ))

    def _quick_note(self, icon, item):
        from tkinter import simpledialog
        def ask():
            text = simpledialog.askstring("быстрая заметка", "что записать?")
            if text:
                from features import notes
                notes.add_note(text)
        self.window.root.after(0, ask)

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