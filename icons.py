"""Генерация иконок для трея на лету."""
from PIL import Image, ImageDraw


def make_icon(color: str = "#4CAF50") -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, size - 4, size - 4), fill=color)
    return img


def color_by_load(cpu: float) -> str:
    if cpu < 30:
        return "#4CAF50"
    if cpu < 70:
        return "#FFC107"
    return "#F44336"