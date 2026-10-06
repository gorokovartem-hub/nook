"""Запуск: трей + скрытое окно + виджет на таскбаре."""
import threading

from window import MainWindow
from tray import TrayApp
from features.clipboard import ClipboardWatcher


def main():
    clipboard = ClipboardWatcher()
    clipboard.start()

    # Главное окно (внутри создаётся и виджет на таскбаре)
    window = MainWindow(on_hide_to_tray=lambda: None, clipboard=clipboard)
    window.root.withdraw()

    def on_quit():
        clipboard.stop()
        window.destroy()

    tray = TrayApp(window, clipboard, on_quit)

    # Трей — единственное, что в отдельном потоке (у pystray свой loop)
    threading.Thread(target=tray.run, daemon=True).start()

    # tkinter — в главном потоке
    window.run_forever()


if __name__ == "__main__":
    main()