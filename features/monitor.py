"""CPU / RAM / батарея / GPU / диск / сеть."""
import time
import psutil


# ---------- GPU ----------
_gpu_available = None
_pynvml = None


def _init_gpu():
    """Пробуем подцепить NVML. Если нет NVIDIA — вернём False."""
    global _gpu_available, _pynvml
    if _gpu_available is not None:
        return _gpu_available
    try:
        import pynvml
        pynvml.nvmlInit()
        _pynvml = pynvml
        _gpu_available = True
    except Exception:
        _gpu_available = False
    return _gpu_available


def get_gpu_load():
    """Загрузка GPU в %, или None если недоступно."""
    if not _init_gpu():
        return None
    try:
        handle = _pynvml.nvmlDeviceGetHandleByIndex(0)
        util = _pynvml.nvmlDeviceGetUtilizationRates(handle)
        return int(util.gpu)
    except Exception:
        return None


# ---------- Диск / сеть ----------
_last_disk = None
_last_net  = None
_last_time = None


def _rate(current, previous, dt):
    if previous is None or dt <= 0:
        return 0
    return max(0, (current - previous) / dt)


def get_io_rates():
    """Возвращает (disk_mb_s, net_down_mb_s, net_up_mb_s)."""
    global _last_disk, _last_net, _last_time

    now = time.time()
    disk = psutil.disk_io_counters()
    net  = psutil.net_io_counters()

    dt = (now - _last_time) if _last_time else 0

    disk_rate = 0
    down_rate = 0
    up_rate   = 0

    if disk and _last_disk and dt > 0:
        disk_rate = _rate(
            disk.read_bytes + disk.write_bytes,
            _last_disk.read_bytes + _last_disk.write_bytes,
            dt,
        ) / (1024 * 1024)

    if net and _last_net and dt > 0:
        down_rate = _rate(net.bytes_recv, _last_net.bytes_recv, dt) / (1024 * 1024)
        up_rate   = _rate(net.bytes_sent, _last_net.bytes_sent, dt) / (1024 * 1024)

    _last_disk = disk
    _last_net  = net
    _last_time = now

    return disk_rate, down_rate, up_rate


def format_speed(mb_s: float) -> str:
    """МБ/с → красивая строка."""
    if mb_s < 1:
        return f"{mb_s * 1024:.0f} KB/s"
    return f"{mb_s:.1f} MB/s"


# ---------- Основное ----------
def get_stats() -> dict:
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    disk_r, net_d, net_u = get_io_rates()

    return {
        "cpu": int(cpu),
        "ram": int(ram.percent),
        "ram_used_gb": round(ram.used / (1024 ** 3), 1),
        "ram_total_gb": round(ram.total / (1024 ** 3), 1),
        "battery": round(battery.percent) if battery else None,
        "plugged": battery.power_plugged if battery else None,
        "gpu": get_gpu_load(),
        "disk": disk_r,
        "net_down": net_d,
        "net_up": net_u,
    }