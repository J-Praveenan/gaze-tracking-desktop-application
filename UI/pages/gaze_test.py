import tkinter as tk
import threading
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from UI.pages.base import BasePage
from UI.pages.sidebar import Sidebar

# Import the gaze detection loop
from UI.pages.gaze_runner import main as run_gaze_test


def F(name, default):
    return getattr(Fonts, name, default)


class GazeTestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Layout grid
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)

        # Sidebar
        Sidebar(self.overlay, controller).grid(
            row=0, column=0, sticky="nsw", padx=(20, 10), pady=20
        )

        # Content area
        card = RoundedCard(self.overlay, radius=18, pad=20, bg=Colors.glass_bg)
        card.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        tk.Label(card.body, text="Real-Time Gaze Test",
                 fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h1b", ("Segoe UI", 18, "bold"))).pack(pady=(10, 20))

        desc = tk.Label(
            card.body,
            text="Click below to start the gaze detection test.\n"
                 "This will open a live video window. Press 'Q' to stop.",
            fg=Colors.card_text, bg=Colors.glass_bg,
            font=F("body", ("Segoe UI", 11)), wraplength=420, justify="center"
        )
        desc.pack(pady=(0, 20))

        start_btn = PillButton(
            card.body, text="START TEST", command=self._start_test
        )
        start_btn.pack(pady=10)

    def _start_test(self):
        # Run gaze detection in a separate thread so Tkinter UI stays responsive
        threading.Thread(target=run_gaze_test, daemon=True).start()
