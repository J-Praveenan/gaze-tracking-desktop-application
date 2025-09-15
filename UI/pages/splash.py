import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage


class SplashPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # ---- TUNING KNOBS ----
        self.BANNER_WIDTH  = 0.80   # fraction of center width (0..1)
        self.BANNER_HEIGHT = 120     # px strip height (try 50–70)
        self.BANNER_RADIUS = 8
        self.BANNER_PAD    = 2
        self.BANNER_FONT   = getattr(Fonts, "banner", ("Segoe UI", 18, "bold"))
        # ----------------------

        overlay_bg = self.overlay.cget("bg")

        # Column container
        self.center = tk.Frame(self.overlay, bg=overlay_bg)
        self.center.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.96)

        # Logo
        self.big_logo_lbl = tk.Label(self.center, bg=overlay_bg, bd=0)
        self.big_logo_lbl.pack(pady=(0, 16))

        # Banner wrapper (we control width via symmetric padx)
        self.banner_wrap = tk.Frame(self.center, bg=overlay_bg)
        self.banner_wrap.pack(fill="x")

        # Rounded card (NON-tight)
        self.banner = RoundedCard(
            self.banner_wrap,
            radius=self.BANNER_RADIUS,
            pad=self.BANNER_PAD,
            bg=Colors.banner_bg,
            tight=False,
        )
        # ✅ Give the CARD a height and stop it shrinking
        self.banner.configure(height=self.BANNER_HEIGHT + 2 * self.BANNER_PAD)
        self.banner.pack(fill="x")
        self.banner.pack_propagate(False)

        # Body fill
        self.banner.body.configure(bg=Colors.banner_bg)
        self.banner.body.pack_propagate(False)

        # Canvas draws the stroked text
        self.canvas = tk.Canvas(self.banner.body, bg=Colors.banner_bg,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.text = "WELCOME TO LOOK TRACK VISION APPLICATION"
        self.font = self.BANNER_FONT

        # Redraw / resize hooks
        self.center.bind("<Configure>", self._on_center_resize)
        self.canvas.bind("<Configure>", lambda e: self._draw_banner())
        self.bind("<Configure>", self._resize_logo)

    # ---------- layout / drawing ----------

    def _on_center_resize(self, _evt=None):
        """Keep banner at a % of center width using symmetric padx."""
        cw = max(1, self.center.winfo_width())
        side_pad = int((1.0 - self.BANNER_WIDTH) * cw / 2)
        self.banner_wrap.pack_configure(padx=side_pad)

        # ensure the strip is tall enough for the font + outline
        try:
            f = tkfont.Font(self, self.font)
            needed = f.metrics("ascent") + f.metrics("descent") + 12
            desired = max(self.BANNER_HEIGHT, needed)
            self.banner.configure(height=desired + 2 * self.BANNER_PAD)
        except Exception:
            pass

        self._draw_banner()

    def _draw_banner(self):
        """Draw centered white text with black outline."""
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 2 or h <= 2:
            return

        x, y = w // 2, h // 2
        fill_color = Colors.pill_fg
        stroke_color = "black"

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
            c.create_text(x+dx, y+dy, text=self.text, font=self.font,
                          fill=stroke_color, anchor="c")
        c.create_text(x, y, text=self.text, font=self.font,
                      fill=fill_color, anchor="c")

    def _resize_logo(self, _evt=None):
        raw = self.controller._logo_raw
        if raw is None:
            self.big_logo_lbl.config(image="", text="LOGO",
                                     font=("Segoe UI", 34, "bold"),
                                     fg="white", bg=self.overlay.cget("bg"))
            return
        size = int(self.winfo_width() * 0.15)
        size = max(120, min(200, size))
        photo = ImageTk.PhotoImage(raw.copy().convert("RGBA").resize((size, size)))
        self.big_logo_lbl.configure(image=photo, text="")
        self.big_logo_lbl.image = photo

    def on_show(self):
        self.after(5000, lambda: self.controller.show("GuideVideoPage"))
