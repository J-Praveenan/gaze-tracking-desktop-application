# UI/pages/setup.py
import tkinter as tk
from .base import BasePage
from UI.theme import Fonts, Colors

class SetupPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)
        tk.Label(self.overlay, text="Set Up Gaze Tracking",
                 font=getattr(Fonts, "h2b", ("Segoe UI", 16, "bold")),
                 fg=Colors.card_head, bg=Colors.page_bg).pack(pady=24)
        tk.Label(self.overlay, text="(Stub page — wire up your real UI here.)",
                 font=getattr(Fonts, "body", ("Segoe UI", 12)),
                 fg=Colors.muted, bg=Colors.page_bg).pack()

    def on_show(self):
        pass
