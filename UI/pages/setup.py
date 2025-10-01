# UI/pages/setup.py
import tkinter as tk
from pathlib import Path
import threading
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from UI.pages.base import BasePage
from UI.pages.sidebar import Sidebar
from UI.pages.guide import GuideVideoPage
from Calibration.Calibration import calibrate_gaze  # import your calibration function


def F(name, default):
    return getattr(Fonts, name, default)


class SetupPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Layout
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)

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

        # Show guide-style video
        guide_path = Path(__file__).resolve().parents[2] / "assets" / "guide.mp4"
        self.guide_video = GuideVideoPage(card.body, controller, guide_path, show_skip=False)
        self.guide_video.pack(fill="both", expand=True)

        # Replace skip button with Start Calibration
        self.start_btn = PillButton(
            self.guide_video.controls, text="START CALIBRATION",
            command=self._start_calibration
        )
        self.start_btn.pack(side="left", padx=(12, 0))


    def _start_calibration(self):
        # Launch calibration in a separate thread
        threading.Thread(target=calibrate_gaze, daemon=True).start()
