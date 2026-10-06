"""Следим за буфером обмена, храним последние N значений."""
import threading
import time
import pyperclip

MAX_HISTORY = 50

class ClipboardWatcher:
    def __init__(self):
        self.history = []
        self._last = ""
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                current = pyperclip.paste()
                if current and current != self._last:
                    self._last = current
                    if current not in self.history:
                        self.history.insert(0, current)
                        self.history = self.history[:MAX_HISTORY]
            except Exception:
                pass
            time.sleep(0.7)

    def get(self, idx: int) -> str | None:
        if 0 <= idx < len(self.history):
            return self.history[idx]
        return None

    def copy_back(self, idx: int):
        val = self.get(idx)
        if val:
            pyperclip.copy(val)
            self._last = val