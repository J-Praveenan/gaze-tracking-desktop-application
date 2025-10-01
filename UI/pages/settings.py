# UI/pages/settings.py
import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage
from .sidebar import Sidebar


def F(name, default):
    return getattr(Fonts, name, default)


class SettingsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Layout: sidebar left, content right
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)  # sidebar
        self.overlay.grid_columnconfigure(1, weight=1)  # content

        # Sidebar (shared across pages)
        Sidebar(self.overlay, controller).grid(
            row=0, column=0, sticky="nsw", padx=(20, 10), pady=20
        )

        # Main content card
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
            text="Settings",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 16, "bold"))
        ).pack(anchor="w", pady=(0, 8))

        # Example placeholder content
        tk.Label(
            self.main_col.body,
            text="(Settings UI goes here — e.g., toggles, dropdowns, preferences)",
            fg=Colors.card_text,
            bg=Colors.glass_bg,
            font=F("body", ("Segoe UI", 11)),
            justify="left",
            anchor="nw",
            wraplength=600
        ).pack(fill="both", expand=True, pady=(6, 0))
