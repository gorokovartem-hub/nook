"""Единый менеджер настроек nook.
Загружает config.json, мигрирует старый формат, сохраняет изменения.
"""
import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DEFAULT_CONFIG = {
    "version": "0.3.0",
    "general": {
        "autostart": False,
        "start_minimized": True,
        "check_updates": True,
        "language": "ru",
    },
    "hotkeys": {
        "compact": "ctrl+alt+c",
        "full": "ctrl+alt+f",
        "toggle": "ctrl+alt+w",
        "note": "ctrl+alt+n",
        "screenshot": "ctrl+alt+s",
    },
    "system": {
        "update_interval": 1200,
        "alert_threshold": 90,
        "hide_in_fullscreen": True,
        "sounds": True,
        "sound_on_high_load": True,
    },
    "screenshots": {
        "folder": "screenshots",
        "format": "png",
        "copy_to_clipboard": True,
    },
    "notifications": {
        "silent_mode": False,
    },
    "appearance": {
        "theme": "system",
        "accent_color": "#4ade80",
        "widget_mode": "full",
        "widget_x": None,
        "widget_y": None,
    },
    "desktop_cards": {
        "visible": {"system": True, "disks": True, "clock": True},
        "positions": {},
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _migrate_old_config(data: dict) -> dict:
    migrated = {}
    tw = data.get("taskbar_widget")
    if isinstance(tw, dict):
        migrated.setdefault("appearance", {})
        if "mode" in tw:
            migrated["appearance"]["widget_mode"] = tw["mode"]
        if "x" in tw:
            migrated["appearance"]["widget_x"] = tw["x"]
        if "y" in tw:
            migrated["appearance"]["widget_y"] = tw["y"]

    for k, v in data.items():
        if k != "taskbar_widget":
            migrated[k] = v
    return migrated


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return _deep_merge(DEFAULT_CONFIG, {})

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[config] ошибка чтения: {e}. Использую дефолт.")
        return _deep_merge(DEFAULT_CONFIG, {})

    if "taskbar_widget" in data or "version" not in data:
        data = _migrate_old_config(data)

    return _deep_merge(DEFAULT_CONFIG, data)


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[config] ошибка сохранения: {e}")


def get(path: str, default: Any = None) -> Any:
    cfg = load_config()
    keys = path.split(".")
    val = cfg
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val


def set_value(path: str, value: Any) -> None:
    cfg = load_config()
    keys = path.split(".")
    obj = cfg
    for k in keys[:-1]:
        if k not in obj or not isinstance(obj[k], dict):
            obj[k] = {}
        obj = obj[k]
    obj[keys[-1]] = value
    save_config(cfg)