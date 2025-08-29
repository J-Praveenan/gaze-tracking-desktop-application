import tkinter as tk
from PIL import Image, ImageTk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage

class SplashPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        overlay_bg = self.overlay.cget("bg")

        # Main container filling the page
        self.center = tk.Frame(self.overlay, bg=overlay_bg)
        self.center.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.9)

        # Logo
        self.big_logo_lbl = tk.Label(self.center, bg=overlay_bg, bd=0)
        self.big_logo_lbl.pack(pady=0)

        # Wide banner card
        # Wide banner card (now tight)
        self.banner = RoundedCard(self.center, radius=10, pad=12, bg=Colors.banner_bg, tight=True)
        self.banner.pack(pady=0)   # no fill="x"

        canvas = tk.Canvas(self.banner.body, bg=self.banner.cget("bg"),
                        highlightthickness=0, bd=0)
        canvas.pack(padx=24, pady=16)

        text = "WELCOME TO LOOK TRACK VISION APPLICATION"
        font = Fonts.banner
        fill_color = Colors.pill_fg   # white
        stroke_color = "black"
        x, y = 10, 16  # position inside canvas

        # Draw stroke by layering black text around
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1), (-1,-1),(1,-1),(-1,1),(1,1)]:
            canvas.create_text(x+dx, y+dy, text=text, font=font,
                            fill=stroke_color, anchor="nw")

        # Draw main text on top
        canvas.create_text(x, y, text=text, font=font, fill=fill_color, anchor="nw")

        # Adjust canvas size automatically
        bbox = canvas.bbox("all")
        canvas.config(width=bbox[2]+10, height=bbox[3]+10)


        self.bind("<Configure>", self._resize_logo)

    def _resize_logo(self, _evt=None):
        raw = self.controller._logo_raw
        if raw is None:
            self.big_logo_lbl.config(
                text="◉", font=("Segoe UI Symbol", 100),
                fg="black", bg=self.overlay.cget("bg")
            )
            return

        # Resize proportionally
        size = max(240, min(240, int(self.winfo_width() * 0.2)))
        photo = ImageTk.PhotoImage(raw.copy().convert("RGBA").resize((size, size)))
        self.big_logo_lbl.configure(image=photo)
        self.big_logo_lbl.image = photo
        
        
    def on_show(self):
        # auto-redirect to Guide page after 3 seconds (3000 ms)
        self.after(5000, lambda: self.controller.show("GuideVideoPage"))


