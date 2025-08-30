import tkinter as tk
from tkinter import ttk
from UI.theme import Colors, Fonts


class RoundedCard(tk.Frame):
    def __init__(self, parent, radius=16, pad=12, bg=None, tight=True, **kwargs):
        self.radius = radius
        self._bg = bg or Colors.card_bg
        self._tight = tight
        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=0, **kwargs)

        self.canvas = tk.Canvas(self, bg=self["bg"], bd=0, highlightthickness=0)
        if self._tight:
            # old behavior: hug content
            self.canvas.pack()
        else:
            # NEW: let the canvas fill the frame
            self.canvas.pack(fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=self._bg)
        self.pad = pad

        self.bind("<Configure>", self._draw)
        self.body.bind("<Configure>", lambda e: self._draw())

    def _draw(self, _evt=None):
        if self._tight:
            reqw = max(10, self.body.winfo_reqwidth())
            reqh = max(10, self.body.winfo_reqheight())
            w = reqw + 2 * self.pad
            h = reqh + 2 * self.pad
        else:
            # Use the frame’s current size
            w = max(10, self.winfo_width())
            h = max(10, self.winfo_height())

        # Keep canvas in sync in BOTH modes
        self.canvas.config(width=w, height=h)

        self.canvas.delete("all")
        r = min(self.radius, h // 2, w // 2)

        # rounded rect
        self.canvas.create_rectangle(r, 0, w - r, h, fill=self._bg, outline="")
        self.canvas.create_rectangle(0, r, w, h - r, fill=self._bg, outline="")
        for x, y in [(0, 0), (w - 2*r, 0), (0, h - 2*r), (w - 2*r, h - 2*r)]:
            self.canvas.create_oval(x, y, x + 2*r, y + 2*r, fill=self._bg, outline="")

        # inner body window stretches with the card
        self.canvas.create_window(
            self.pad, self.pad, window=self.body, anchor="nw",
            width=max(1, w - 2*self.pad), height=max(1, h - 2*self.pad)
        )

class TitleBar(tk.Frame):
    """Header with logo + title and a thin bottom border."""
    def __init__(self, parent, logo_img=None, title_text=""):
        super().__init__(parent, bg="#dbeafe", height=48, highlightthickness=0)
        self.pack_propagate(False)
        self.logo = tk.Label(self, image=logo_img, bg=self["bg"])
        self.logo.image = logo_img
        self.logo.pack(side="left", padx=(10, 8), pady=6)
        self.title = tk.Label(self, text=title_text, font=("Segoe UI", 14, "bold"),
                              bg=self["bg"], fg="#111827")
        self.title.pack(side="left")
        self.border = tk.Frame(parent, bg="#1d4ed8", height=2)
        self.border.pack(fill="x", side="top")

    def set_logo(self, img):
        if img is None: return
        self.logo.configure(image=img)
        self.logo.image = img

class PillButton(tk.Button):
    """Rounded style button (visual)."""
    def __init__(self, parent, text, command=None):
        super().__init__(parent, text=text, command=command,
                         font=("Segoe UI", 10, "bold"),
                         fg=Colors.pill_fg, bg=Colors.pill_bg, activebackground="#2563eb",
                         bd=0, padx=18, pady=8, cursor="hand2")
