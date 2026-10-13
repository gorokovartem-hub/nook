"""Тема: авто-определение тёмной/светлой Windows + палитра."""
import json
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
DEFAULT_SETTINGS = {
    "mode": "system",
    "preset": "system",
    "colors": {},
    "opacity": 0.92,
    "corner_radius": 12,
}
COLOR_KEYS = ("BG", "CARD", "FG", "LINE")
PRESET_NAMES = {
    "system": "Системная",
    "dark": "Тёмная",
    "light": "Светлая",
    "midnight": "Полночь",
    "ocean": "Океан",
    "forest": "Лес",
    "violet": "Фиолетовая",
    "rose": "Розовая",
    "amber": "Янтарная",
    "graphite": "Графит",
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
    return {
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
    """Selects the configured palette and refreshes imported module globals."""
    global COLORS
    preset = _SETTINGS["preset"]
    if preset == "system":
        COLORS = dict(LIGHT if is_windows_light() else DARK)
    else:
        COLORS = dict(PRESETS[preset])
    COLORS.update(_SETTINGS["colors"])
    _refresh_module_globals()
    return COLORS


def set_settings(settings):
    """Apply normalized user settings and return the previous color palette."""
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
    merged["corner_radius"] = max(0, min(24, int(merged["corner_radius"])))
    _SETTINGS = merged
    apply_palette()
    appearance = "light" if _SETTINGS["preset"] == "light" or (
        _SETTINGS["preset"] == "system" and is_windows_light()) else "dark"
    ctk.set_appearance_mode(appearance)
    return previous


def recolor_widget_tree(root, previous=None):
    """Update existing CustomTkinter controls after changing the palette."""
    roles = {
        "fg_color": ("BG", "BG_SOFT", "CARD", "CARD_HOVER", "TB_BG", "TB_TRACK"),
        "hover_color": ("BG_SOFT", "CARD_HOVER", "TB_TRACK"),
        "button_color": ("ACCENT", "FG"),
        "button_hover_color": ("FG_DIM", "ACCENT", "FG"),
        "border_color": ("LINE", "CARD"),
        "scrollbar_button_color": ("LINE", "FG_FAINT", "TB_TRACK"),
        "scrollbar_button_hover_color": ("FG_DIM", "FG_FAINT", "TB_TRACK"),
        "text_color": ("FG", "FG_DIM", "FG_FAINT", "ACCENT", "GOOD", "WARN", "BAD",
                       "TB_FG", "TB_DIM"),
        "placeholder_text_color": ("FG_DIM", "FG_FAINT", "TB_DIM"),
        "progress_color": ("FG", "GOOD", "WARN", "BAD"),
        "bg": ("BG", "BG_SOFT", "CARD", "TB_BG", "KEY_COLOR"),
    }
    old_palettes = [previous or {}, _INITIAL_COLORS, DARK, LIGHT]

    def recolor(widget):
        for option, role_names in roles.items():
            try:
                value = widget.cget(option)
            except (tk.TclError, AttributeError, ValueError):
                continue
            def replace_color(color):
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
            if replacement is not None and replacement != value:
                try:
                    widget.configure(**{option: replacement})
                except (tk.TclError, AttributeError, ValueError):
                    pass

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

        try:
            children = widget.winfo_children()
        except (tk.TclError, AttributeError):
            return
        for child in children:
            recolor(child)

    recolor(root)


def setup_appearance():
    apply_palette()
    ctk.set_appearance_mode(
        "light" if (_SETTINGS["preset"] == "light"
                    or (_SETTINGS["preset"] == "system" and is_windows_light()))
        else "dark")
    ctk.set_default_color_theme("blue")


# Применяем сразу при импорте: `from theme import BG, FG, ...` получит
# актуальные цвета, а не тёмные по умолчанию.
_SETTINGS = _load_settings()
apply_palette()
_INITIAL_COLORS = dict(COLORS)


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
        corner_radius=get_corner_radius(), **kwargs,
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