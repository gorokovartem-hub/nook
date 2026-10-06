"""Глобальные хоткеи через keyboard. Требует админа на Windows."""
_available = None
_kb = None
_reason = ""


def _init():
    global _available, _kb, _reason
    if _available is not None:
        return _available
    try:
        import keyboard
        _kb = keyboard
        _available = True
        return True
    except ImportError:
        _reason = "модуль keyboard не установлен (pip install keyboard)"
        _available = False
        return False
    except Exception as e:
        _reason = f"ошибка импорта keyboard: {e}"
        _available = False
        return False


def register(hotkey: str, callback) -> bool:
    if not _init():
        return False
    try:
        _kb.add_hotkey(hotkey, callback, suppress=False)
        return True
    except Exception as e:
        print(f"Не удалось зарегистрировать {hotkey}: {e}")
        return False


def register_all(bindings: dict) -> None:
    if not _init():
        print(f"Хоткеи недоступны: {_reason}")
        return
    for hk, cb in bindings.items():
        register(hk, cb)
    print(f"Хоткеи зарегистрированы: {', '.join(bindings.keys())}")


def is_available() -> bool:
    return _init()