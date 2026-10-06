"""
Скриншот области с эффектом прожектора.

Внутри выделения:
    оригинальное изображение.

Снаружи:
    мягкое затемнение.

ЛКМ:
    выделение области.

ПКМ:
    сброс выделения.

Esc:
    отмена.

Примагничивание:
    стороны выделения автоматически прилипают
    к краям экрана.

После выделения:
    PNG сохраняется в screenshots;
    изображение копируется в буфер обмена Windows.
"""

import ctypes
from ctypes import wintypes
from pathlib import Path
from datetime import datetime
from io import BytesIO
import time
import tkinter as tk

import mss
from PIL import Image, ImageTk


# ============================================================
# НАСТРОЙКИ
# ============================================================

SHOTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "screenshots"
)

SHOTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# Сила затемнения:
# 0.55 = 45% затемнения
# 0.70 = слабее
# 0.40 = сильнее
DARK_FACTOR = 0.55

# Минимальный размер скриншота
MIN_SIZE = 5

# Расстояние, на котором сторона начинает прилипать
# к краю экрана.
SNAP_DISTANCE = 12


# ============================================================
# WINDOWS CLIPBOARD
# ============================================================

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

CF_DIB = 8
GMEM_MOVEABLE = 0x0002


kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalAlloc.argtypes = [
    wintypes.UINT,
    ctypes.c_size_t
]

kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalLock.argtypes = [
    wintypes.HGLOBAL
]

kernel32.GlobalUnlock.argtypes = [
    wintypes.HGLOBAL
]

kernel32.GlobalFree.argtypes = [
    wintypes.HGLOBAL
]


user32.OpenClipboard.argtypes = [
    wintypes.HWND
]
user32.OpenClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.restype = wintypes.BOOL

user32.SetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [
    wintypes.UINT,
    wintypes.HANDLE
]

user32.CloseClipboard.restype = wintypes.BOOL


def _copy_image_to_clipboard(
    pil_image: Image.Image
) -> bool:
    """
    Копирует PIL Image в Windows Clipboard
    в формате CF_DIB.
    """

    h_global = None

    try:
        output = BytesIO()

        pil_image.convert("RGB").save(
            output,
            "BMP"
        )

        # Убираем BMP FILE HEADER.
        # CF_DIB использует только DIB.
        data = output.getvalue()[14:]

        output.close()

        h_global = kernel32.GlobalAlloc(
            GMEM_MOVEABLE,
            len(data)
        )

        if not h_global:
            print(
                "[clipboard] GlobalAlloc = 0"
            )
            return False

        p_global = kernel32.GlobalLock(
            h_global
        )

        if not p_global:
            print(
                "[clipboard] GlobalLock = NULL"
            )

            kernel32.GlobalFree(
                h_global
            )

            h_global = None
            return False

        ctypes.memmove(
            p_global,
            data,
            len(data)
        )

        kernel32.GlobalUnlock(
            h_global
        )

        # Clipboard иногда занят другим приложением.
        opened = False

        for _ in range(20):

            if user32.OpenClipboard(None):
                opened = True
                break

            time.sleep(0.05)

        if not opened:

            print(
                "[clipboard] "
                "OpenClipboard провалился"
            )

            kernel32.GlobalFree(
                h_global
            )

            h_global = None
            return False

        try:

            user32.EmptyClipboard()

            result = user32.SetClipboardData(
                CF_DIB,
                h_global
            )

            if not result:

                print(
                    "[clipboard] "
                    "SetClipboardData = 0"
                )

                kernel32.GlobalFree(
                    h_global
                )

                h_global = None
                return False

            # После успешного SetClipboardData
            # память принадлежит Windows.
            h_global = None

            print(
                "[clipboard] OK"
            )

            return True

        finally:

            user32.CloseClipboard()

    except Exception as e:

        print(
            "[clipboard] Ошибка:",
            e
        )

        if h_global:

            try:
                kernel32.GlobalFree(
                    h_global
                )
            except Exception:
                pass

        return False


# ============================================================
# SCREENSHOT
# ============================================================

def grab_region(
    master=None,
    copy_to_clipboard=True
):
    """
    Показывает окно выбора области.

    ВАЖНО:
    если функция вызывается из уже работающего
    Tkinter-приложения, используется его root.

    Второй tk.Tk() НЕ создаётся.
    """

    print(
        "[screenshot] СТАРТ, master =",
        master
    )

    # ========================================================
    # ПОЛУЧАЕМ СУЩЕСТВУЮЩИЙ TK ROOT
    # ========================================================

    own_root = False

    if master is None:

        try:
            master = tk._default_root
        except Exception:
            master = None

    # Если Tk root действительно отсутствует,
    # создаём его один раз.
    if master is None:

        master = tk.Tk()
        master.withdraw()

        own_root = True

    # ========================================================
    # КООРДИНАТЫ
    # ========================================================

    coords = {
        "x1": 0,
        "y1": 0,
        "x2": 0,
        "y2": 0
    }

    cancelled = {
        "value": False
    }

    # ========================================================
    # SCREEN CAPTURE
    # ========================================================

    print(
        "[screenshot] Снимаю экран..."
    )

    try:

        with mss.mss() as sct:

            # Основной монитор
            monitor = sct.monitors[1]

            full = sct.grab(
                monitor
            )

            full_img = Image.frombytes(
                "RGB",
                full.size,
                full.rgb
            )

            sw = monitor["width"]
            sh = monitor["height"]

            mon_left = monitor["left"]
            mon_top = monitor["top"]

    except Exception as e:

        print(
            "[screenshot] "
            "Ошибка mss:",
            e
        )

        if own_root:
            master.destroy()

        return None

    print(
        f"[screenshot] "
        f"Экран: {sw}x{sh}"
    )

    # ========================================================
    # DARK IMAGE
    # ========================================================

    dark_img = full_img.point(
        lambda p: int(
            p * DARK_FACTOR
        )
    )

    # ========================================================
    # OVERLAY
    # ========================================================

    overlay = tk.Toplevel(
        master
    )

    overlay.overrideredirect(
        True
    )

    overlay.attributes(
        "-topmost",
        True
    )

    # Не используем alpha.
    # Это предотвращает чёрный экран / проблемы
    # с композицией Windows.
    overlay.configure(
        bg="#000000"
    )

    overlay.geometry(
        f"{sw}x{sh}+"
        f"{mon_left}+{mon_top}"
    )

    # ========================================================
    # CANVAS
    # ========================================================

    canvas = tk.Canvas(
        overlay,
        width=sw,
        height=sh,
        bg="#000000",
        highlightthickness=0,
        bd=0,
        cursor="crosshair"
    )

    canvas.pack(
        fill="both",
        expand=True
    )

    # ========================================================
    # PHOTOIMAGE
    # ========================================================

    # ВАЖНО:
    # PhotoImage привязан именно к overlay.
    #
    # Это исправляет:
    # _tkinter.TclError:
    # image "pyimage1" does not exist
    #

    tk_dark = ImageTk.PhotoImage(
        dark_img,
        master=overlay
    )

    # ========================================================
    # DARK BACKGROUND
    # ========================================================

    dark_layer = canvas.create_image(
        0,
        0,
        image=tk_dark,
        anchor="nw"
    )

    # ========================================================
    # BRIGHT LAYER
    # ========================================================

    bright_layer = canvas.create_image(
        0,
        0,
        image=tk_dark,
        anchor="nw",
        state="hidden"
    )

    # ========================================================
    # IMAGE REFERENCES
    # ========================================================

    canvas._image_refs = [
        tk_dark
    ]

    # ========================================================
    # SELECTION BORDER
    # ========================================================

    sel_outer = canvas.create_rectangle(
        0,
        0,
        0,
        0,
        outline="#4ade80",
        width=2,
        state="hidden"
    )

    sel_inner = canvas.create_rectangle(
        0,
        0,
        0,
        0,
        outline="#ffffff",
        width=1,
        state="hidden"
    )

    # ========================================================
    # CORNERS
    # ========================================================

    S = 9

    corners = [

        canvas.create_rectangle(
            0,
            0,
            0,
            0,
            fill="#4ade80",
            outline="",
            state="hidden"
        ),

        canvas.create_rectangle(
            0,
            0,
            0,
            0,
            fill="#4ade80",
            outline="",
            state="hidden"
        ),

        canvas.create_rectangle(
            0,
            0,
            0,
            0,
            fill="#4ade80",
            outline="",
            state="hidden"
        ),

        canvas.create_rectangle(
            0,
            0,
            0,
            0,
            fill="#4ade80",
            outline="",
            state="hidden"
        )
    ]

    # ========================================================
    # HINT
    # ========================================================

    hint = canvas.create_text(
        sw // 2,
        30,
        text=(
            "Выдели область  ·  "
            "Esc — отмена  ·  "
            "ПКМ — сброс"
        ),
        fill="#e8e8e8",
        font=("Segoe UI", 11)
    )

    # ========================================================
    # SIZE
    # ========================================================

    size_text = canvas.create_text(
        0,
        0,
        text="",
        anchor="nw",
        fill="#4ade80",
        font=(
            "Cascadia Mono",
            10,
            "bold"
        ),
        state="hidden"
    )

    size_bg = canvas.create_rectangle(
        0,
        0,
        0,
        0,
        fill="#1c1c1c",
        outline="#4ade80",
        width=1,
        state="hidden"
    )

    # ========================================================
    # SNAP
    # ========================================================

    def snap_coordinate(
        value,
        maximum
    ):
        """
        Примагничивает одну координату
        к ближайшему краю экрана.
        """

        if abs(value) <= SNAP_DISTANCE:
            return 0

        if abs(maximum - value) <= SNAP_DISTANCE:
            return maximum

        return value

    def snap_selection(
        x1,
        y1,
        x2,
        y2,
        moving_x,
        moving_y
    ):
        """
        Магнит для выделения.

        Важно:
        магнитится именно та сторона,
        которую сейчас двигает курсор.

        Это предотвращает ситуацию, когда
        противоположная сторона неожиданно
        прыгает к краю.
        """

        # ----------------------------------------------------
        # Горизонталь
        # ----------------------------------------------------

        if abs(
            moving_x - x1
        ) <= abs(
            moving_x - x2
        ):

            # Двигается левая сторона.
            if abs(x1) <= SNAP_DISTANCE:
                x1 = 0

            elif abs(sw - x1) <= SNAP_DISTANCE:
                x1 = sw

        else:

            # Двигается правая сторона.
            if abs(x2) <= SNAP_DISTANCE:
                x2 = 0

            elif abs(sw - x2) <= SNAP_DISTANCE:
                x2 = sw

        # ----------------------------------------------------
        # Вертикаль
        # ----------------------------------------------------

        if abs(
            moving_y - y1
        ) <= abs(
            moving_y - y2
        ):

            # Двигается верхняя сторона.
            if abs(y1) <= SNAP_DISTANCE:
                y1 = 0

            elif abs(sh - y1) <= SNAP_DISTANCE:
                y1 = sh

        else:

            # Двигается нижняя сторона.
            if abs(y2) <= SNAP_DISTANCE:
                y2 = 0

            elif abs(sh - y2) <= SNAP_DISTANCE:
                y2 = sh

        return (
            x1,
            y1,
            x2,
            y2
        )

    # ========================================================
    # HELPERS
    # ========================================================

    def hide_selection():

        canvas.itemconfig(
            bright_layer,
            state="hidden"
        )

        canvas.itemconfig(
            sel_outer,
            state="hidden"
        )

        canvas.itemconfig(
            sel_inner,
            state="hidden"
        )

        for c in corners:

            canvas.itemconfig(
                c,
                state="hidden"
            )

        canvas.itemconfig(
            size_bg,
            state="hidden"
        )

        canvas.itemconfig(
            size_text,
            state="hidden"
        )

    def update_bright(
        x1,
        y1,
        x2,
        y2
    ):

        width = x2 - x1
        height = y2 - y1

        if width < 2 or height < 2:

            canvas.itemconfig(
                bright_layer,
                state="hidden"
            )

            return

        # Защита от выхода за экран.
        x1 = max(
            0,
            min(x1, sw)
        )

        y1 = max(
            0,
            min(y1, sh)
        )

        x2 = max(
            0,
            min(x2, sw)
        )

        y2 = max(
            0,
            min(y2, sh)
        )

        if x2 <= x1 or y2 <= y1:

            canvas.itemconfig(
                bright_layer,
                state="hidden"
            )

            return

        # Берём оригинальный участок.
        crop = full_img.crop(
            (
                x1,
                y1,
                x2,
                y2
            )
        )

        # PhotoImage создаём в том же Tk-интерпретаторе.
        tk_crop = ImageTk.PhotoImage(
            crop,
            master=overlay
        )

        # Сохраняем ссылки.
        canvas._image_refs = [
            tk_dark,
            tk_crop
        ]

        canvas.itemconfig(
            bright_layer,
            image=tk_crop,
            state="normal"
        )

        canvas.coords(
            bright_layer,
            x1,
            y1
        )

        # Правильный порядок слоёв.
        canvas.tag_raise(
            bright_layer
        )

        canvas.tag_raise(
            sel_outer
        )

        canvas.tag_raise(
            sel_inner
        )

        for c in corners:
            canvas.tag_raise(c)

        canvas.tag_raise(
            size_bg
        )

        canvas.tag_raise(
            size_text
        )

        canvas.tag_raise(
            hint
        )

    def update_corners(
        x1,
        y1,
        x2,
        y2
    ):

        canvas.coords(
            corners[0],
            x1,
            y1,
            x1 + S,
            y1 + S
        )

        canvas.coords(
            corners[1],
            x2 - S,
            y1,
            x2,
            y1 + S
        )

        canvas.coords(
            corners[2],
            x1,
            y2 - S,
            x1 + S,
            y2
        )

        canvas.coords(
            corners[3],
            x2 - S,
            y2 - S,
            x2,
            y2
        )

    def update_size(
        x1,
        y1,
        x2,
        y2,
        mx,
        my
    ):

        width = abs(
            x2 - x1
        )

        height = abs(
            y2 - y1
        )

        canvas.itemconfig(
            size_text,
            text=f"{width} × {height}"
        )

        tx = mx + 18
        ty = my + 18

        if tx + 90 > sw:
            tx = mx - 100

        if ty + 30 > sh:
            ty = my - 35

        canvas.coords(
            size_text,
            tx + 6,
            ty + 4
        )

        bbox = canvas.bbox(
            size_text
        )

        if bbox:

            canvas.coords(
                size_bg,
                bbox[0] - 6,
                bbox[1] - 3,
                bbox[2] + 6,
                bbox[3] + 3
            )

    def render(
        x1,
        y1,
        x2,
        y2,
        mx,
        my
    ):

        update_bright(
            x1,
            y1,
            x2,
            y2
        )

        canvas.coords(
            sel_outer,
            x1,
            y1,
            x2,
            y2
        )

        canvas.coords(
            sel_inner,
            x1 + 2,
            y1 + 2,
            x2 - 2,
            y2 - 2
        )

        update_corners(
            x1,
            y1,
            x2,
            y2
        )

        update_size(
            x1,
            y1,
            x2,
            y2,
            mx,
            my
        )

        canvas.itemconfig(
            sel_outer,
            state="normal"
        )

        canvas.itemconfig(
            sel_inner,
            state="normal"
        )

        for c in corners:

            canvas.itemconfig(
                c,
                state="normal"
            )

        canvas.itemconfig(
            size_bg,
            state="normal"
        )

        canvas.itemconfig(
            size_text,
            state="normal"
        )

    # ========================================================
    # EVENTS
    # ========================================================

    def on_press(event):

        x = event.x_root - mon_left
        y = event.y_root - mon_top

        x = max(
            0,
            min(x, sw)
        )

        y = max(
            0,
            min(y, sh)
        )

        # Если начинаем возле края,
        # сразу магнитим стартовую точку.
        x = snap_coordinate(
            x,
            sw
        )

        y = snap_coordinate(
            y,
            sh
        )

        coords["x1"] = x
        coords["y1"] = y
        coords["x2"] = x
        coords["y2"] = y

        render(
            x,
            y,
            x,
            y,
            x,
            y
        )

    def on_drag(event):

        x = event.x_root - mon_left
        y = event.y_root - mon_top

        x = max(
            0,
            min(x, sw)
        )

        y = max(
            0,
            min(y, sh)
        )

        coords["x2"] = x
        coords["y2"] = y

        # Текущая область.
        x1 = min(
            coords["x1"],
            coords["x2"]
        )

        y1 = min(
            coords["y1"],
            coords["y2"]
        )

        x2 = max(
            coords["x1"],
            coords["x2"]
        )

        y2 = max(
            coords["y1"],
            coords["y2"]
        )

        # ====================================================
        # MAGNET
        # ====================================================

        x1, y1, x2, y2 = snap_selection(
            x1,
            y1,
            x2,
            y2,
            x,
            y
        )

        # ====================================================
        # РЕНДЕР
        # ====================================================

        render(
            x1,
            y1,
            x2,
            y2,
            x,
            y
        )

    def on_release(event):

        x = event.x_root - mon_left
        y = event.y_root - mon_top

        x = max(
            0,
            min(x, sw)
        )

        y = max(
            0,
            min(y, sh)
        )

        coords["x2"] = x
        coords["y2"] = y

        # Финальное применение магнита.
        x1 = min(
            coords["x1"],
            coords["x2"]
        )

        y1 = min(
            coords["y1"],
            coords["y2"]
        )

        x2 = max(
            coords["x1"],
            coords["x2"]
        )

        y2 = max(
            coords["y1"],
            coords["y2"]
        )

        x1, y1, x2, y2 = snap_selection(
            x1,
            y1,
            x2,
            y2,
            x,
            y
        )

        coords["x1"] = x1
        coords["y1"] = y1
        coords["x2"] = x2
        coords["y2"] = y2

        try:
            overlay.grab_release()
        except Exception:
            pass

        overlay.destroy()

    def on_escape(event=None):

        cancelled["value"] = True

        coords["x1"] = 0
        coords["y1"] = 0
        coords["x2"] = 0
        coords["y2"] = 0

        try:
            overlay.grab_release()
        except Exception:
            pass

        overlay.destroy()

    def on_right_click(event):

        coords["x1"] = 0
        coords["y1"] = 0
        coords["x2"] = 0
        coords["y2"] = 0

        hide_selection()

    # ========================================================
    # BINDINGS
    # ========================================================

    canvas.bind(
        "<ButtonPress-1>",
        on_press
    )

    canvas.bind(
        "<B1-Motion>",
        on_drag
    )

    canvas.bind(
        "<ButtonRelease-1>",
        on_release
    )

    canvas.bind(
        "<Button-3>",
        on_right_click
    )

    overlay.bind(
        "<Escape>",
        on_escape
    )

    # ========================================================
    # SHOW
    # ========================================================

    overlay.update_idletasks()

    overlay.lift()

    overlay.focus_force()

    try:
        overlay.grab_set()
    except Exception:
        pass

    # ========================================================
    # WAIT
    # ========================================================

    master.wait_window(
        overlay
    )

    # ========================================================
    # CANCELLED
    # ========================================================

    if cancelled["value"]:

        print(
            "[screenshot] ОТМЕНА"
        )

        if own_root:

            try:
                master.destroy()
            except Exception:
                pass

        return None

    if own_root:

        try:
            master.destroy()
        except Exception:
            pass

    # ========================================================
    # NORMALIZE COORDINATES
    # ========================================================

    x1 = min(
        coords["x1"],
        coords["x2"]
    )

    y1 = min(
        coords["y1"],
        coords["y2"]
    )

    x2 = max(
        coords["x1"],
        coords["x2"]
    )

    y2 = max(
        coords["y1"],
        coords["y2"]
    )

    width = x2 - x1
    height = y2 - y1

    print(
        f"[screenshot] "
        f"Область: {width} x {height}"
    )

    if (
        width < MIN_SIZE
        or height < MIN_SIZE
    ):

        print(
            "[screenshot] "
            "Слишком маленькая, отмена"
        )

        return None

    # ========================================================
    # CROP
    # ========================================================

    img = full_img.crop(
        (
            x1,
            y1,
            x2,
            y2
        )
    )

    # ========================================================
    # SAVE
    # ========================================================

    fname = (
        SHOTS_DIR
        / (
            f"shot_"
            f"{datetime.now():%Y%m%d_%H%M%S}.png"
        )
    )

    try:

        img.save(
            fname,
            "PNG"
        )

    except Exception as e:

        print(
            "[screenshot] "
            "Ошибка сохранения:",
            e
        )

        return None

    print(
        f"[screenshot] "
        f"Файл: {fname}"
    )

    # ========================================================
    # CLIPBOARD
    # ========================================================

    if copy_to_clipboard:

        print(
            "[screenshot] "
            "Копирую в буфер..."
        )

        ok = _copy_image_to_clipboard(
            img
        )

        print(
            "[screenshot] "
            "В буфер:",
            "OK" if ok else "ПРОВАЛ"
        )

    print(
        "[screenshot] ГОТОВО"
    )

    return fname


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    result = grab_region()

    if result:

        print(
            f"Готово: {result}"
        )

    else:

        print(
            "Скриншот отменён."
        )