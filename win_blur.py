"""Модуль для включения размытия (стекла) на окнах Windows."""
import ctypes
from ctypes import wintypes
import sys

def is_windows_11() -> bool:
    if sys.platform != "win32":
        return False
    return sys.getwindowsversion().build >= 22000

def enable_blur(hwnd: int, dark_mode: bool = True, tint_color: str = None, alpha: int = None):
    if sys.platform != "win32":
        return
    
    if tint_color is None:
        tint_color = "#1c1c1c" if dark_mode else "#f3f3f3"

    # Конвертируем HEX в ABGR
    r = int(tint_color[1:3], 16)
    g = int(tint_color[3:5], 16)
    b = int(tint_color[5:7], 16)
    a = 0x66 if alpha is None else max(0, min(255, int(alpha)))  # плотность оттенка
    gradient = (a << 24) | (b << 16) | (g << 8) | r

    if is_windows_11():
        _enable_win11_acrylic(hwnd, dark_mode, gradient)
    else:
        _enable_win10_blur(hwnd, gradient)

def disable_blur(hwnd: int):
    """Выключает Acrylic/blur и возвращает окну обычный непрозрачный вид."""
    if sys.platform != "win32":
        return
    if is_windows_11():
        try:
            backdrop = ctypes.c_int(1)  # DWMSBT_NONE
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        except Exception as e:
            print("Win11 backdrop reset error:", e)
    _set_accent(hwnd, 0, 0)  # ACCENT_DISABLED

def _enable_win11_acrylic(hwnd: int, dark_mode: bool, gradient: int):
    try:
        dwmapi = ctypes.windll.dwmapi
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val = ctypes.c_int(1 if dark_mode else 0)
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val))
        
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        backdrop = ctypes.c_int(3) # Acrylic
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        
        # ПРИНУДИТЕЛЬНО применяем градиент (через старый метод Win10)
        _enable_win10_blur(hwnd, gradient)
    except Exception as e:
        print("Win11 Acrylic error:", e)

def _enable_win10_blur(hwnd: int, gradient: int):
    _set_accent(hwnd, 4, gradient)  # ACCENT_ENABLE_ACRYLICBLURBEHIND

def _set_accent(hwnd: int, state: int, gradient: int):
    try:
        class ACCENTPOLICY(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]
        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.POINTER(ACCENTPOLICY)),
                        ("SizeOfData", ctypes.c_size_t)]
        accent = ACCENTPOLICY()
        accent.AccentState = state
        accent.GradientColor = gradient
        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19 # WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.pointer(accent)
        user32 = ctypes.windll.user32
        user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception as e:
        print("Win10 Blur error:", e)