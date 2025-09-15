# UI/pages/system.py
import tkinter as tk
from .base import BasePage
from UI.theme import Fonts, Colors

class SystemPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)
        tk.Label(self.overlay, text="System Control",
                 font=getattr(Fonts, "h2b", ("Segoe UI", 16, "bold")),
                 fg=Colors.card_head, bg=Colors.page_bg).pack(pady=24)
        tk.Label(self.overlay, text="(Stub page — system-level actions here.)",
                 font=getattr(Fonts, "body", ("Segoe UI", 12)),
                 fg=Colors.muted, bg=Colors.page_bg).pack()

    def on_show(self):
        pass
