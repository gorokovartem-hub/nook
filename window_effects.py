"""Lightweight, static edge glow for Nook windows.

The effect is rendered once per window size (with a short resize debounce).
It does not run an animation loop and the Canvas stays behind the UI.
"""
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter, ImageTk


def apply_edge_gradient(window, color="#4ade80", strength=15, background="#111111"):
    """Apply a subtle theme-colored glow around the window edges."""
    try:
        old_canvas = getattr(window, "_nook_edge_gradient_canvas", None)
        if old_canvas is not None:
            try:
                old_canvas.destroy()
            except tk.TclError:
                pass

        canvas = tk.Canvas(
            window,
            highlightthickness=0,
            bd=0,
            relief="flat",
            bg=background,
        )
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Lower the widget in the Tk window stack (Canvas.lower() is a
        # different method and requires a canvas item/tag).
        window.tk.call("lower", canvas._w)
        window._nook_edge_gradient_canvas = canvas
        window._nook_edge_gradient_photo = None
        window._nook_edge_gradient_size = None
        window._nook_edge_gradient_job = None

        value = color.lstrip("#")
        if len(value) != 6:
            raise ValueError("color must be #RRGGBB")
        rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        strength = max(0, min(24, int(strength)))

        def render(width, height):
            if width < 80 or height < 80 or strength == 0:
                canvas.delete("edge-glow")
                return

            # Render at the actual window size only when its dimensions change.
            layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer)
            inset = max(2, strength // 2)
            radius = max(18, min(width, height) // 12)
            draw.rounded_rectangle(
                (inset, inset, width - inset - 1, height - inset - 1),
                radius=radius,
                outline=(*rgb, strength),
                width=max(2, strength),
            )
            # Broad blur removes the hard line and creates a soft edge falloff.
            glow = layer.filter(ImageFilter.GaussianBlur(radius=max(12, strength)))
            photo = ImageTk.PhotoImage(glow)
            canvas.delete("edge-glow")
            canvas.create_image(0, 0, image=photo, anchor="nw", tags="edge-glow")
            canvas.image = photo
            window._nook_edge_gradient_photo = photo
            window._nook_edge_gradient_size = (width, height)

        def schedule_redraw(_event=None):
            if not canvas.winfo_exists():
                return
            job = window._nook_edge_gradient_job
            if job is not None:
                try:
                    window.after_cancel(job)
                except tk.TclError:
                    pass
            window._nook_edge_gradient_job = window.after(
                180,
                lambda: render(max(2, window.winfo_width()),
                               max(2, window.winfo_height()))
                if canvas.winfo_exists() else None,
            )

        def on_destroy(event):
            if event.widget is window:
                job = window._nook_edge_gradient_job
                if job is not None:
                    try:
                        window.after_cancel(job)
                    except tk.TclError:
                        pass

        window.bind("<Configure>", schedule_redraw, add="+")
        window.bind("<Destroy>", on_destroy, add="+")
        window.after_idle(schedule_redraw)
    except Exception as exc:
        print("[Nook] edge gradient unavailable:", exc)
