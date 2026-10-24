"""Тема: авто-определение тёмной/светлой Windows + палитра."""
import json
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from i18n import tr

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
MAGIC_COLOR = "#010203"
DEFAULT_SETTINGS = {
    "mode": "system",
    "preset": "system",
    "colors": {},
    "opacity": 0.92,
    "corner_radius": 12,
    "glass": True,
    "glass_density": 0.40,
}
COLOR_KEYS = ("BG", "CARD", "FG", "LINE")
PRESET_NAMES = {
    "system": tr("Системная"),
    "dark": tr("Тёмная"),
    "light": tr("Светлая"),
    "midnight": tr("Полночь"),
    "ocean": tr("Океан"),
    "forest": tr("Лес"),
    "violet": tr("Фиолетовая"),
    "rose": tr("Розовая"),
    "amber": tr("Янтарная"),
    "graphite": tr("Графит"),
}

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


def _make_preset(base, **overrides):
    palette = dict(base)
    palette.update(overrides)
    return palette


PRESETS = {
    "dark": DARK,
    "light": LIGHT,
    "midnight": _make_preset(
        DARK, BG="#0b1020", BG_SOFT="#10182b", CARD="#141f38",
        CARD_HOVER="#1b2948", LINE="#263756", FG="#e7efff",
        FG_DIM="#91a4c4", FG_FAINT="#354766", ACCENT="#83b9ff",
        TB_BG="#111b30", TB_TRACK="#263756", TB_FG="#e7efff",
        TB_DIM="#91a4c4",
    ),
    "ocean": _make_preset(
        DARK, BG="#08191e", BG_SOFT="#0d2229", CARD="#102a32",
        CARD_HOVER="#173640", LINE="#21434c", FG="#e2f5f4",
        FG_DIM="#86b6b3", FG_FAINT="#315258", ACCENT="#62d4c2",
        TB_BG="#10282e", TB_TRACK="#21434c", TB_FG="#e2f5f4",
        TB_DIM="#86b6b3",
    ),
    "forest": _make_preset(
        DARK, BG="#101a13", BG_SOFT="#17231a", CARD="#1b2b20",
        CARD_HOVER="#24382a", LINE="#304936", FG="#e8f3e7",
        FG_DIM="#9ab39a", FG_FAINT="#3b5540", ACCENT="#8fd18e",
        TB_BG="#1a2a1e", TB_TRACK="#304936", TB_FG="#e8f3e7",
        TB_DIM="#9ab39a",
    ),
    "violet": _make_preset(
        DARK, BG="#17111f", BG_SOFT="#20172b", CARD="#281d35",
        CARD_HOVER="#352542", LINE="#483454", FG="#f2eafa",
        FG_DIM="#b5a1c7", FG_FAINT="#59466b", ACCENT="#c49af2",
        TB_BG="#251b31", TB_TRACK="#483454", TB_FG="#f2eafa",
        TB_DIM="#b5a1c7",
    ),
    "rose": _make_preset(
        DARK, BG="#1d1116", BG_SOFT="#28171e", CARD="#321d26",
        CARD_HOVER="#412630", LINE="#593540", FG="#fae9ed",
        FG_DIM="#c49ba5", FG_FAINT="#704653", ACCENT="#ef91aa",
        TB_BG="#2d1b22", TB_TRACK="#593540", TB_FG="#fae9ed",
        TB_DIM="#c49ba5",
    ),
    "amber": _make_preset(
        DARK, BG="#1c1710", BG_SOFT="#292116", CARD="#34291a",
        CARD_HOVER="#433521", LINE="#5b472b", FG="#f8f0df",
        FG_DIM="#c5b28d", FG_FAINT="#705b39", ACCENT="#e8ba68",
        TB_BG="#302619", TB_TRACK="#5b472b", TB_FG="#f8f0df",
        TB_DIM="#c5b28d",
    ),
    "graphite": _make_preset(
        DARK, BG="#17191c", BG_SOFT="#202327", CARD="#272b30",
        CARD_HOVER="#32373d", LINE="#41474f", FG="#edf0f2",
        FG_DIM="#a0a8b0", FG_FAINT="#515961", ACCENT="#c4cbd2",
        TB_BG="#25292e", TB_TRACK="#41474f", TB_FG="#edf0f2",
        TB_DIM="#a0a8b0",
    ),
}

COLORS = dict(DARK)
BASE_COLORS = dict(DARK)   # палитра до наложения «стекла»
_SETTINGS = dict(DEFAULT_SETTINGS)

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


# ---------- Стекло ----------
def _rgb(color: str):
    h = color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(c1: str, c2: str, t: float) -> str:
    """Смешивает два #rrggbb: t=0 → c1, t=1 → c2."""
    a, b = _rgb(c1), _rgb(c2)
    r, g, bl = (round(x + (y - x) * t) for x, y in zip(a, b))
    return f"#{r:02x}{g:02x}{bl:02x}"


def _is_dark(color: str) -> bool:
    r, g, b = _rgb(color)
    return (r * 299 + g * 587 + b * 114) / 1000 < 128


def _glassify(base: dict, custom: dict) -> dict:
    """Накладывает стекло на любую палитру.

    Фон слегка подкрашивается акцентом (это же цвет оттенка Acrylic),
    карточки «приподнимаются», граница становится светлой кромкой,
    GLOSS — внутренний блик. Цвета, выбранные вручную, не трогаем.
    """
    p = dict(base)
    white, black = "#ffffff", "#000000"
    dark = _is_dark(base["BG"])
    # светлая тема: фон чуть темнее, иначе на светлых обоях всё сливается
    bg = _mix(base["BG"], base["ACCENT"], 0.05 if dark else 0.10)
    p["BG"] = bg
    if dark:
        p["BG_SOFT"] = _mix(bg, white, 0.05)
        p["CARD"] = _mix(base["CARD"], white, 0.05)
        p["CARD_HOVER"] = _mix(p["CARD"], white, 0.07)
        p["LINE"] = _mix(bg, white, 0.24)
        p["GLOSS"] = _mix(bg, white, 0.12)
    else:
        p["BG_SOFT"] = _mix(bg, black, 0.04)
        p["CARD"] = _mix(base["CARD"], bg, 0.35)
        p["CARD_HOVER"] = _mix(p["CARD"], black, 0.05)
        p["LINE"] = _mix(bg, black, 0.28)
        p["GLOSS"] = white
        p["FG_DIM"] = _mix(base["FG_DIM"], black, 0.25)
    p["TB_BG"] = p["CARD"]
    p["TB_TRACK"] = p["LINE"]
    p.update(custom)
    return p


def is_glass() -> bool:
    return bool(_SETTINGS.get("glass")) and is_dark_theme()

def get_tint_alpha() -> int:
    """Плотность оттенка Acrylic (0–255): чем выше, тем меньше стекло прозрачно."""
    return round(255 * _SETTINGS["glass_density"])


def is_dark_theme() -> bool:
    """Тёмная ли тема на самом деле (для Acrylic и DWM), а не по имени пресета."""
    return _is_dark(BASE_COLORS["BG"])


def _refresh_module_globals():
    global BG, BG_SOFT, CARD, CARD_HOVER, LINE
    global FG, FG_DIM, FG_FAINT, ACCENT, GOOD, WARN, BAD
    BG, BG_SOFT = COLORS["BG"], COLORS["BG_SOFT"]
    CARD, CARD_HOVER = COLORS["CARD"], COLORS["CARD_HOVER"]
    LINE = COLORS["LINE"]
    FG, FG_DIM, FG_FAINT = COLORS["FG"], COLORS["FG_DIM"], COLORS["FG_FAINT"]
    ACCENT = COLORS["ACCENT"]
    GOOD, WARN, BAD = COLORS["GOOD"], COLORS["WARN"], COLORS["BAD"]


def _load_settings():
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        saved = config.get("theme", {}) if isinstance(config, dict) else {}
    except FileNotFoundError:
        saved = {}
    except (OSError, json.JSONDecodeError) as e:
        print("theme settings:", e)
        saved = {}
    if not isinstance(saved, dict):
        saved = {}
    colors = saved.get("colors", {})
    if not isinstance(colors, dict):
        colors = {}
    valid_colors = {
        key: value for key, value in colors.items()
        if key in COLOR_KEYS and isinstance(value, str)
        and len(value) == 7 and value.startswith("#")
        and all(char in "0123456789abcdefABCDEF" for char in value[1:])
    }
    preset = saved.get("preset", saved.get("mode", "system"))
    if preset not in PRESET_NAMES:
        preset = "system"
    try:
        opacity = max(0.45, min(1.0, float(saved.get("opacity", 0.92))))
        radius = max(0, min(24, int(saved.get("corner_radius", 12))))
    except (TypeError, ValueError):
        opacity, radius = 0.92, 12
    try:
        glass_density = max(0.05, min(1.0, float(saved.get("glass_density", 0.40))))
    except (TypeError, ValueError):
        glass_density = 0.40
    return {
        "glass": bool(saved.get("glass", True)),
        "glass_density": glass_density,
        "mode": preset if preset in ("system", "dark", "light") else "dark",
        "preset": preset,
        "colors": valid_colors,
        "opacity": opacity,
        "corner_radius": radius,
    }


def get_settings():
    return {
        **_SETTINGS,
        "colors": dict(_SETTINGS["colors"]),
    }


def get_opacity() -> float:
    return _SETTINGS["opacity"]


def get_corner_radius() -> int:
    return _SETTINGS["corner_radius"]


def apply_palette():
    """Выбирает палитру и обновляет глобальные константы модуля."""
    global COLORS, BASE_COLORS
    preset = _SETTINGS["preset"]
    if preset == "system":
        base = dict(LIGHT if is_windows_light() else DARK)
    else:
        base = dict(PRESETS[preset])
    base.update(_SETTINGS["colors"])
    base["GLOSS"] = base["CARD"]
    BASE_COLORS = base
    # Стекло применяем только к тёмным палитрам — на светлой оно даёт грязь
    use_glass = is_glass() and _is_dark(base["BG"])
    COLORS = (_glassify(base, _SETTINGS["colors"])
              if use_glass else dict(base))
    _refresh_module_globals()
    return COLORS


def set_settings(settings):
    """Применяет настройки и возвращает предыдущую палитру."""
    global _SETTINGS
    previous = dict(COLORS)
    merged = {**DEFAULT_SETTINGS, **settings}
    if "preset" not in settings:
        legacy_mode = settings.get("mode", "system")
        merged["preset"] = (
            legacy_mode if legacy_mode in PRESET_NAMES else "system")
    if merged["preset"] not in PRESET_NAMES:
        merged["preset"] = "system"
    merged["mode"] = (
        merged["preset"] if merged["preset"] in ("system", "dark", "light")
        else "dark"
    )
    colors = merged.get("colors", {})
    merged["colors"] = {
        key: value for key, value in colors.items()
        if key in COLOR_KEYS and isinstance(value, str)
        and len(value) == 7 and value.startswith("#")
        and all(char in "0123456789abcdefABCDEF" for char in value[1:])
    }
    merged["mode"] = merged["mode"] if merged["mode"] in (
        "system", "dark", "light") else "system"
    merged["opacity"] = max(0.45, min(1.0, float(merged["opacity"])))
    merged["glass"] = bool(merged["glass"])
    merged["glass_density"] = max(0.05, min(1.0, float(merged["glass_density"])))
    merged["corner_radius"] = max(0, min(24, int(merged["corner_radius"])))
    _SETTINGS = merged
    apply_palette()
    appearance = "light" if _SETTINGS["preset"] == "light" or (
        _SETTINGS["preset"] == "system" and is_windows_light()) else "dark"
    ctk.set_appearance_mode(appearance)
    return previous


def recolor_widget_tree(root, previous=None):
    """Обновляет существующие виджеты после смены палитры."""
    roles = {
        "fg_color": tuple(COLORS),
        "hover_color": tuple(COLORS),
        "bg_color": tuple(COLORS),
        "button_color": ("ACCENT", "FG"),
        "button_hover_color": ("FG_DIM", "ACCENT", "FG"),
        "border_color": ("LINE", "CARD"),
        "scrollbar_button_color": ("LINE", "FG_FAINT", "TB_TRACK"),
        "scrollbar_button_hover_color": ("FG_DIM", "FG_FAINT", "TB_TRACK"),
        "text_color": ("FG", "FG_DIM", "FG_FAINT", "ACCENT", "GOOD", "WARN", "BAD",
                       "TB_FG", "TB_DIM"),
        "placeholder_text_color": ("FG_DIM", "FG_FAINT", "TB_DIM"),
        "progress_color": ("FG", "ACCENT", "GOOD", "WARN", "BAD"),
        "bg": (*COLORS, "KEY_COLOR"),
    }

    old_palettes = [previous or {}, _INITIAL_COLORS, DARK, LIGHT, {"MAGIC": MAGIC_COLOR}]
    recolored = set()

    def is_ctk_widget(widget):
        return widget.__class__.__module__.startswith("customtkinter")

    def recolor(widget):
        widget_id = id(widget)
        if widget_id in recolored:
            return
        recolored.add(widget_id)

        # --- 1. Чистый Tk: Frame, Canvas (только если это не CTk) ---
        if isinstance(widget, (tk.Frame, tk.Canvas)) and not is_ctk_widget(widget):
            try:
                current_bg = widget.cget("bg")
                for role in ("BG", "CARD", "BG_SOFT"):
                    if any(palette.get(role) == current_bg for palette in old_palettes):
                        widget.configure(bg=COLORS.get(role, current_bg))
                        break
            except (tk.TclError, AttributeError):
                pass

                # --- 2. CustomTkinter ---
        for option, role_names in roles.items():
            try:
                value = widget.cget(option)
            except (tk.TclError, AttributeError, ValueError):
                continue

            def replace_color(color):
                if not isinstance(color, str):
                    return color
                if color == "transparent" or color == MAGIC_COLOR:
                    return color
                
                for role in role_names:
                    if any(palette.get(role) == color for palette in old_palettes):
                        return COLORS.get(role, color)
                return color

            if isinstance(value, str):
                replacement = replace_color(value)
            elif isinstance(value, (tuple, list)):
                replacement = tuple(replace_color(color) for color in value)
            else:
                continue
                
            # --- ФИКС ДЛЯ КНОПОК ---
            if isinstance(widget, ctk.CTkButton) and option == "text_color":
                # Если у кнопки заливка цвета FG (белая в тёмной теме, чёрная в светлой),
                # то текст должен быть цвета BG. Иначе он сольется.
                bg_color = widget.cget("fg_color")
                if bg_color == COLORS["FG"]:
                    replacement = COLORS["BG"]

            if replacement is not None and replacement != value:
                try:
                    widget.configure(**{option: replacement})
                except (tk.TclError, AttributeError, ValueError):
                    pass

        # --- 3. Switch / Slider ---
        if isinstance(widget, ctk.CTkSwitch):
            try:
                widget.configure(
                    fg_color=COLORS["LINE"],
                    progress_color=COLORS["ACCENT"],
                    button_color=COLORS["FG"],
                    button_hover_color=COLORS["FG_DIM"],
                )
            except (tk.TclError, AttributeError, ValueError):
                pass
        elif isinstance(widget, ctk.CTkSlider):
            try:
                widget.configure(
                    fg_color=COLORS["LINE"],
                    progress_color=COLORS["ACCENT"],
                    button_color=COLORS["FG"],
                    button_hover_color=COLORS["FG_DIM"],
                )
            except (tk.TclError, AttributeError, ValueError):
                pass

        # --- 4. Скругления ---
        if isinstance(widget, ctk.CTkFrame):
            radius = get_corner_radius()
        elif isinstance(widget, (ctk.CTkButton, ctk.CTkOptionMenu, ctk.CTkEntry)):
            radius = min(get_corner_radius(), 12)
        else:
            radius = None
        if radius is not None:
            try:
                corner = int(widget.cget("corner_radius"))
                if (not isinstance(widget, ctk.CTkFrame) or corner > 0
                        or widget.cget("fg_color") == COLORS["CARD"]):
                    widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, ValueError):
                pass

        # --- 5. ЖЁСТКИЙ ФИКС ДЛЯ СКРОЛЛ-ФРЕЙМОВ И ТЕКСТОВЫХ ПОЛЕЙ ---
        if isinstance(widget, ctk.CTkScrollableFrame):
            try:
                widget.configure(fg_color=COLORS["BG"])
                if hasattr(widget, "_parent_frame"):
                    widget._parent_frame.configure(fg_color=COLORS["BG"])
                if hasattr(widget, "_parent_canvas"):
                    widget._parent_canvas.configure(bg=COLORS["BG"])
            except Exception:
                pass
        elif isinstance(widget, (ctk.CTkTextbox, ctk.CTkEntry)):
            try:
                widget.configure(fg_color=COLORS["BG"])
                if hasattr(widget, "_textbox") and hasattr(widget._textbox, "configure"):
                    widget._textbox.configure(bg=COLORS["BG"])
                if hasattr(widget, "_canvas") and hasattr(widget._canvas, "configure"):
                    widget._canvas.configure(bg=COLORS["BG"])
            except Exception:
                pass
        elif isinstance(widget, ctk.CTk):
            try:
                widget.configure(fg_color=COLORS["BG"])
            except Exception:
                pass

        # --- 6. Рекурсия ---
        try:
            children = widget.winfo_children()
        except (tk.TclError, AttributeError):
            children = ()
        for child in children:
            recolor(child)

    recolor(root)
    try:
        root.update_idletasks()
    except Exception:
        pass


def setup_appearance():
    apply_palette()
    ctk.set_appearance_mode(
        "light" if (_SETTINGS["preset"] == "light"
                    or (_SETTINGS["preset"] == "system" and is_windows_light()))
        else "dark")
    ctk.set_default_color_theme("blue")


# Применяем сразу при импорте
_SETTINGS = _load_settings()
apply_palette()
_INITIAL_COLORS = dict(COLORS)


# ---------- Хелперы ----------
def level_color(pct: float, invert: bool = False) -> str:
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
        corner_radius=get_corner_radius(), **kwargs,
    )


def progress_bar(parent, color=None, height=4):
    return ctk.CTkProgressBar(
        parent, height=height, corner_radius=height // 2,
        progress_color=color or COLORS["FG"], fg_color=COLORS["FG_FAINT"],
    )


def _button(parent, text, command, defaults, kwargs):
    opts = {**defaults, **kwargs}
    return ctk.CTkButton(parent, text=text, command=command, **opts)


def flat_button(parent, text, command=None, **kwargs):
    return _button(parent, text, command, dict(
        fg_color="transparent", hover_color=COLORS["BG_SOFT"],
        text_color=COLORS["FG"], font=FONT_BODY,
        corner_radius=min(get_corner_radius(), 12), height=32, border_width=0,
    ), kwargs)


def line_button(parent, text, command=None, **kwargs):
    return _button(parent, text, command, dict(
        fg_color="transparent", hover_color=COLORS["BG_SOFT"],
        text_color=COLORS["FG"], font=FONT_BODY,
        border_width=1, border_color=COLORS["LINE"],
        corner_radius=min(get_corner_radius(), 12), height=34,
    ), kwargs)


def primary_button(parent, text, command=None, **kwargs):
    return _button(parent, text, command, dict(
        fg_color=COLORS["FG"], hover_color=COLORS["FG_DIM"],
        text_color=COLORS["BG"], font=FONT_BODY,
        corner_radius=min(get_corner_radius(), 12), height=34, border_width=0,
    ), kwargs)