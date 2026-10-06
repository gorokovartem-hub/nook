"""Тема: авто-определение тёмной/светлой Windows + палитра."""
import customtkinter as ctk

# ---------- Палитры ----------
DARK = {
    "BG":         "#111111",
    "BG_SOFT":    "#161616",
    "CARD":       "#151515",
    "CARD_HOVER": "#1d1d1d",
    "LINE":       "#262626",
    "FG":         "#e8e8e8",
    "FG_DIM":     "#6b6b6b",
    "FG_FAINT":   "#3a3a3a",
    "ACCENT":     "#e8e8e8",
    "GOOD":       "#5fb878",
    "WARN":       "#e0b050",
    "BAD":        "#e06c6c",
    "TB_BG":      "#1c1c1c",
    "TB_TRACK":   "#2a2a2a",
    "TB_FG":      "#e8e8e8",
    "TB_DIM":     "#7a7a7a",
}

LIGHT = {
    "BG":         "#fafafa",
    "BG_SOFT":    "#f0f0f0",
    "CARD":       "#ffffff",
    "CARD_HOVER": "#f4f4f4",
    "LINE":       "#e0e0e0",
    "FG":         "#1a1a1a",
    "FG_DIM":     "#7a7a7a",
    "FG_FAINT":   "#c0c0c0",
    "ACCENT":     "#1a1a1a",
    "GOOD":       "#2e9e5b",
    "WARN":       "#c98a1a",
    "BAD":        "#d64545",
    "TB_BG":      "#f3f3f3",
    "TB_TRACK":   "#dcdcdc",
    "TB_FG":      "#1a1a1a",
    "TB_DIM":     "#7a7a7a",
}

COLORS = dict(DARK)

# ---------- Явные константы (заполняются в apply_palette) ----------
BG = BG_SOFT = CARD = CARD_HOVER = LINE = ""
FG = FG_DIM = FG_FAINT = ACCENT = ""
GOOD = WARN = BAD = ""

# ---------- Шрифты ----------
FONT_TITLE = ("Segoe UI", 20)
FONT_H     = ("Segoe UI", 13)
FONT_BODY  = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 11)
FONT_MONO  = ("Cascadia Mono", 12)
FONT_HUGE  = ("Segoe UI Light", 56)


# ---------- Определение темы Windows ----------
def is_windows_light() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        val, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False


def _refresh_module_globals():
    global BG, BG_SOFT, CARD, CARD_HOVER, LINE
    global FG, FG_DIM, FG_FAINT, ACCENT, GOOD, WARN, BAD
    BG, BG_SOFT = COLORS["BG"], COLORS["BG_SOFT"]
    CARD, CARD_HOVER = COLORS["CARD"], COLORS["CARD_HOVER"]
    LINE = COLORS["LINE"]
    FG, FG_DIM, FG_FAINT = COLORS["FG"], COLORS["FG_DIM"], COLORS["FG_FAINT"]
    ACCENT = COLORS["ACCENT"]
    GOOD, WARN, BAD = COLORS["GOOD"], COLORS["WARN"], COLORS["BAD"]


def apply_palette():
    """Выбирает палитру по системной теме и обновляет константы."""
    global COLORS
    COLORS = dict(LIGHT if is_windows_light() else DARK)
    _refresh_module_globals()
    return COLORS


def setup_appearance():
    apply_palette()
    ctk.set_appearance_mode("light" if is_windows_light() else "dark")
    ctk.set_default_color_theme("blue")


# Применяем сразу при импорте: `from theme import BG, FG, ...` получит
# актуальные цвета, а не тёмные по умолчанию.
apply_palette()


# ---------- Хелперы ----------
def level_color(pct: float, invert: bool = False) -> str:
    """Цвет по уровню загрузки. invert=True — чем меньше, тем хуже (батарея)."""
    if invert:
        return COLORS["BAD"] if pct < 20 else COLORS["WARN"] if pct < 40 else COLORS["GOOD"]
    return COLORS["GOOD"] if pct < 60 else COLORS["WARN"] if pct < 85 else COLORS["BAD"]


# ---------- Компоненты ----------
def divider(parent):
    return ctk.CTkFrame(parent, height=1, fg_color=COLORS["LINE"], corner_radius=0)


def card(parent, **kwargs):
    return ctk.CTkFrame(
        parent, fg_color=COLORS["CARD"],
        border_width=1, border_color=COLORS["LINE"],
        corner_radius=10, **kwargs,
    )


def progress_bar(parent, color=None, height=4):
    return ctk.CTkProgressBar(
        parent, height=height, corner_radius=height // 2,
        progress_color=color or COLORS["FG"], fg_color=COLORS["FG_FAINT"],
    )


def _button(parent, text, command, defaults, kwargs):
    """Кнопка с дефолтами; переданные kwargs их переопределяют."""
    opts = {**defaults, **kwargs}
    return ctk.CTkButton(parent, text=text, command=command, **opts)


def flat_button(parent, text, command=None, **kwargs):
    return _button(parent, text, command, dict(
        fg_color="transparent", hover_color=COLORS["BG_SOFT"],
        text_color=COLORS["FG"], font=FONT_BODY,
        corner_radius=6, height=32, border_width=0,
    ), kwargs)


def line_button(parent, text, command=None, **kwargs):
    return _button(parent, text, command, dict(
        fg_color="transparent", hover_color=COLORS["BG_SOFT"],
        text_color=COLORS["FG"], font=FONT_BODY,
        border_width=1, border_color=COLORS["LINE"],
        corner_radius=6, height=34,
    ), kwargs)


def primary_button(parent, text, command=None, **kwargs):
    return _button(parent, text, command, dict(
        fg_color=COLORS["FG"], hover_color=COLORS["FG_DIM"],
        text_color=COLORS["BG"], font=FONT_BODY,
        corner_radius=6, height=34, border_width=0,
    ), kwargs)