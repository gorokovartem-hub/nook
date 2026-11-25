"""Shared subtle edge glow for Nook windows."""
import tkinter as tk
from PIL import Image, ImageTk


def apply_edge_gradient(window, color="#4ade80", strength=22):
    """Draw a soft accent glow at the window edges; the overlay never captures clicks."""
    try:
        canvas = tk.Canvas(window, highlightthickness=0, bd=0, bg="#111111")
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.lower()
        window._nook_edge_gradient_canvas = canvas

        value = color.lstrip("#")
        rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

        def redraw(_event=None):
            width = max(2, window.winfo_width())
            height = max(2, window.winfo_height())
            scale = min(1.0, 420 / max(width, height))
            w, h = max(2, int(width * scale)), max(2, int(height * scale))
            image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            pixels = image.load()
            fade = max(5.0, min(w, h) * 0.13)
            for y in range(h):
                for x in range(w):
                    edge = min(x, y, w - 1 - x, h - 1 - y)
                    t = max(0.0, 1.0 - edge / fade)
                    alpha = int(strength * (t ** 2.2))
                    if alpha:
                        pixels[x, y] = (*rgb, alpha)
            photo = ImageTk.PhotoImage(image)
            canvas.delete("edge-glow")
            canvas.create_image(0, 0, image=photo, anchor="nw", tags="edge-glow")
            canvas.image = photo
            canvas.lower()

        window.bind("<Configure>", redraw, add="+")
        window.after_idle(redraw)
    except Exception as exc:
        print("[Nook] edge gradient unavailable:", exc)
