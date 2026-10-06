"""Тест буфера обмена — без всего лишнего."""
import ctypes
from ctypes import wintypes
from io import BytesIO
import time

from PIL import Image

# --- WinAPI ---
kernel32 = ctypes.windll.kernel32
user32   = ctypes.windll.user32

CF_DIB        = 8
GMEM_MOVEABLE = 0x0002

kernel32.GlobalAlloc.restype   = wintypes.HGLOBAL
kernel32.GlobalAlloc.argtypes  = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalLock.restype    = wintypes.LPVOID
kernel32.GlobalLock.argtypes   = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalFree.argtypes   = [wintypes.HGLOBAL]

user32.OpenClipboard.argtypes    = [wintypes.HWND]
user32.OpenClipboard.restype     = wintypes.BOOL
user32.EmptyClipboard.restype    = wintypes.BOOL
user32.SetClipboardData.restype  = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.CloseClipboard.restype    = wintypes.BOOL


def test_copy():
    print("=== 1. Создаю тестовую картинку 200x200 ===")
    img = Image.new("RGB", (200, 200), (255, 0, 0))
    for x in range(100):
        for y in range(100):
            img.putpixel((x, y), (0, 255, 0))
    print("   OK, картинка создана")

    print("=== 2. Конвертирую в BMP байты ===")
    output = BytesIO()
    img.save(output, "BMP")
    bmp_data = output.getvalue()
    output.close()
    print(f"   Полный BMP: {len(bmp_data)} байт")

    data = bmp_data[14:]   # без файлового заголовка
    print(f"   DIB данные: {len(data)} байт")

    print("=== 3. GlobalAlloc ===")
    h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    print(f"   h_global = {h_global}")
    if not h_global:
        print("   ❌ GlobalAlloc провалился")
        return

    print("=== 4. GlobalLock + memmove ===")
    p_global = kernel32.GlobalLock(h_global)
    print(f"   p_global = {p_global}")
    if not p_global:
        print("   ❌ GlobalLock провалился")
        kernel32.GlobalFree(h_global)
        return
    ctypes.memmove(p_global, data, len(data))
    kernel32.GlobalUnlock(h_global)
    print("   OK, данные скопированы в память")

    print("=== 5. OpenClipboard (с ретраями) ===")
    opened = False
    for i in range(10):
        if user32.OpenClipboard(None):
            opened = True
            print(f"   OK, открыт с попытки {i+1}")
            break
        err = ctypes.get_last_error() if hasattr(ctypes, 'get_last_error') else '?'
        print(f"   попытка {i+1}: не удалось, GetLastError={err}")
        time.sleep(0.1)

    if not opened:
        print("   ❌ не удалось открыть буфер")
        kernel32.GlobalFree(h_global)
        return

    try:
        print("=== 6. EmptyClipboard ===")
        ok = user32.EmptyClipboard()
        print(f"   EmptyClipboard = {ok}")

        print("=== 7. SetClipboardData(CF_DIB) ===")
        result = user32.SetClipboardData(CF_DIB, h_global)
        print(f"   результат = {result}  (должно быть != 0)")
        if not result:
            print("   ❌ SetClipboardData провалился")
            kernel32.GlobalFree(h_global)
            return
        print("   ✅ УСПЕХ! h_global передан Windows, освобождать не надо")
    finally:
        user32.CloseClipboard()

    print()
    print("=== 8. Проверка через PIL.ImageGrab ===")
    time.sleep(0.3)
    from PIL import ImageGrab
    check = ImageGrab.grabclipboard()
    print(f"   тип: {type(check)}")
    if isinstance(check, Image.Image):
        print(f"   ✅ В БУФЕРЕ КАРТИНКА: {check.size} px, режим {check.mode}")
    elif check is None:
        print("   ❌ буфер пустой")
    else:
        print(f"   ⚠️ в буфере что-то другое: {check}")


if __name__ == "__main__":
    test_copy()
    input("\nНажми Enter чтобы выйти...")