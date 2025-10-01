import tkinter as tk
from pathlib import Path
from UI.theme import Colors
from UI.widgets import RoundedCard
from UI.pages.base import BasePage
from UI.pages.sidebar import Sidebar
from UI.pages.guide import GuideVideoPage


class TipsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Use grid (sidebar left, content right)
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)   # sidebar
        self.overlay.grid_columnconfigure(1, weight=1)   # content

        # Sidebar
        Sidebar(self.overlay, controller).grid(
            row=0, column=0, sticky="nsw", padx=(20, 10), pady=20
        )

        # Content area as rounded card
        card = RoundedCard(
            self.overlay, radius=18, 
            bg=Colors.dark_card, tight=False
        )
        card.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Embed Guide video inside the card body
        guide_path = Path(__file__).resolve().parents[2] / "assets" / "guide.mp4"
        self.guide_video = GuideVideoPage(card.body, controller, guide_path,show_skip=False)
        self.guide_video.pack(fill="both", expand=True)
