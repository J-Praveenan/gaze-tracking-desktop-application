import tkinter as tk
from tkinter import ttk
from UI.theme import Colors, Fonts


class RoundedCard(tk.Frame):
    def __init__(self, parent, border_color="#222", border_width=0,
                 radius=16, pad=12, bg=None, tight=True, **kwargs):
        self.radius = radius
        self._bg = bg or Colors.card_bg
        self._tight = tight
        self.border_color = border_color
        self.border_width = border_width
        self.pad = pad

        # prevent tkinter from seeing these
        kwargs.pop("border_color", None)
        kwargs.pop("border_width", None)

        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=0, **kwargs)

        self.canvas = tk.Canvas(self, bg=self["bg"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=self._bg)

        self.bind("<Configure>", self._draw)
        # self.body.bind("<Configure>", lambda e: self._draw())

    def _draw(self, _evt=None):
        w = max(10, self.winfo_width())

        if self._tight:
            reqh = max(10, self.body.winfo_reqheight())
            h = reqh + 2*self.pad
        else:
            h = max(10, self.winfo_height())

        self.canvas.config(width=w, height=h)
        self.canvas.delete("all")

        r = min(self.radius, h // 2, w // 2)

        # --- Background fill ---
        self.canvas.create_rectangle(r, 0, w-r, h, fill=self._bg, outline="")
        self.canvas.create_rectangle(0, r, w, h-r, fill=self._bg, outline="")
        for x, y in [(0,0), (w-2*r,0), (0,h-2*r), (w-2*r,h-2*r)]:
            self.canvas.create_oval(x, y, x+2*r, y+2*r, fill=self._bg, outline="")

        # --- Border stroke (only if border_width > 0) ---
        if self.border_width > 0:
            # top line
            self.canvas.create_line(r, 0, w-r, 0,
                                    fill=self.border_color, width=self.border_width)
            # bottom line
            self.canvas.create_line(r, h, w-r, h,
                                    fill=self.border_color, width=self.border_width)
            # left line
            self.canvas.create_line(0, r, 0, h-r,
                                    fill=self.border_color, width=self.border_width)
            # right line
            self.canvas.create_line(w, r, w, h-r,
                                    fill=self.border_color, width=self.border_width)
            # 4 arcs for corners
            self.canvas.create_arc(0, 0, 2*r, 2*r, start=90, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)
            self.canvas.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)
            self.canvas.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)
            self.canvas.create_arc(0, h-2*r, 2*r, h, start=180, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)

        # place inner body
        self.canvas.create_window(
            self.pad, self.pad, window=self.body, anchor="nw",
            width=max(1, w-2*self.pad), height=max(1, h-2*self.pad)
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
