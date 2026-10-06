"""Помидорный таймер: 25/5/15 + уведомления."""
import threading
import time
from plyer import notification

WORK = 25 * 60
SHORT = 5 * 60
LONG = 15 * 60
CYCLES_BEFORE_LONG = 4


class Pomodoro:
    def __init__(self, on_tick=None, on_finish=None):
        self.on_tick = on_tick       # callback(remaining_sec, phase)
        self.on_finish = on_finish   # callback(phase)
        self.phase = "idle"          # idle / work / short / long
        self.remaining = 0
        self.cycle = 0
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        if self.phase == "idle":
            self.phase = "work"
            self.remaining = WORK
        self._stop.clear()
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def pause(self):
        self._stop.set()

    def reset(self):
        self._stop.set()
        self.phase = "idle"
        self.remaining = 0
        self.cycle = 0

    def _run(self):
        while not self._stop.is_set() and self.remaining > 0:
            time.sleep(1)
            if self._stop.is_set():
                return
            self.remaining -= 1
            if self.on_tick:
                self.on_tick(self.remaining, self.phase)
        if self.remaining <= 0:
            self._next_phase()

    def _next_phase(self):
        finished = self.phase
        if self.on_finish:
            self.on_finish(finished)

        if finished == "work":
            self.cycle += 1
            if self.cycle % CYCLES_BEFORE_LONG == 0:
                self.phase = "long"
                self.remaining = LONG
                notify("🍅 Длинный перерыв!", "15 минут отдыха")
            else:
                self.phase = "short"
                self.remaining = SHORT
                notify("🍅 Перерыв", "5 минут отдыха")
        else:
            self.phase = "work"
            self.remaining = WORK
            notify("🍅 Работа!", "25 минут фокуса")

        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()


def notify(title: str, message: str):
    try:
        notification.notify(title=title, message=message, timeout=5, app_name="TrayApp")
    except Exception as e:
        print("Уведомление не сработало:", e)