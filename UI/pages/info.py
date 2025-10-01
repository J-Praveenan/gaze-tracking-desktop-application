# UI/pages/info.py
import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage
from .sidebar import Sidebar


def F(name, default):
    return getattr(Fonts, name, default)


class InfoPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Layout: sidebar (col 0), content (col 1)
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)  # sidebar
        self.overlay.grid_columnconfigure(1, weight=1)  # content

        # Sidebar (shared navigation)
        Sidebar(self.overlay, controller).grid(
            row=0, column=0, sticky="nsw", padx=(20, 10), pady=20
        )

        # Main content area
        self.main_col = RoundedCard(
            self.overlay,
            radius=18,
            pad=20,
            bg=Colors.glass_bg,
            border_color="#4b5563",
            border_width=2
        )
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Title
        tk.Label(
            self.main_col.body,
            text="Information",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 16, "bold"))
        ).pack(anchor="w", pady=(0, 8))

        # Example content
        info_text = (
            "LOOK TRACK VISION helps you control your computer using eye gaze and voice.\n\n"
            "- Eye tracking calibration ensures accuracy\n"
            "- Blinking & gaze gestures for clicks\n"
            "- Voice typing and app control\n\n"
            "For more details, visit the documentation or contact support."
        )
        tk.Label(
            self.main_col.body,
            text=info_text,
            fg=Colors.card_text,
            bg=Colors.glass_bg,
            justify="left",
            anchor="nw",
            font=F("body", ("Segoe UI", 11)),
            wraplength=600
        ).pack(fill="both", expand=True, pady=(4, 0))
