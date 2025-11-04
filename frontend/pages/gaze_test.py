import tkinter as tk
import threading
from frontend.theme import Colors, Fonts
from frontend.widgets import RoundedCard, PillButton
from frontend.pages.base import BasePage
from frontend.pages.sidebar import Sidebar
from frontend.pages.gaze_runner import main as run_gaze_test
import subprocess, sys, os
from frontend.pages import gaze_runner
import cv2 as cv

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


        # Content area
        card = RoundedCard(self.overlay, radius=18, pad=20, bg=Colors.glass_bg)
        card.grid(row=0, column=1, sticky="nsew", padx=(0, 20))

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
    
        


    # def _start_test(self):
    #     from frontend.pages import gaze_runner
    #     print("[INFO] Starting test mode session...")
    #     test_session = gaze_runner.GazeSession(enable_mouse_control=False, show_video=True)
    #     test_session.start()
        
    def _start_test(self):
        import cv2
        from frontend.pages import gaze_runner

        print("[INFO] Starting test mode session...")

        # 🔍 Read the selected camera index from configuration.json
        import json, os
        from pathlib import Path
        ROOT = Path(__file__).resolve().parents[2]
        config_path = ROOT / "Data" / "configuration.json"

        camera_index = 0  # default
        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    camera_index = config.get("camera", {}).get("index", 0)
        except Exception as e:
            print("⚠️ Failed to load config:", e)

        # 🎥 Try to open the camera safely
        cap = cv2.VideoCapture(camera_index)
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            # 🚫 Camera failed → show popup message
            popup = tk.Toplevel(self)
            popup.title("Camera Error")
            popup.configure(bg=Colors.dark_card)
            popup.geometry("480x180+700+400")
            popup.resizable(False, False)

            tk.Label(
                popup,
                text="Camera Not Available!",
                fg="white", bg=Colors.dark_card,
                font=F("h2b", ("Segoe UI", 14, "bold"))
            ).pack(pady=(20, 10))

            tk.Label(
                popup,
                text="You are selecting the wrong camera option.\n"
                    "Go to the Settings option and select the correct camera.",
                fg="#e5e7eb", bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10)),
                justify="center"
            ).pack(pady=(0, 20))

            tk.Button(
                popup,
                text="OK",
                command=popup.destroy,
                bg="#ef4444",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                width=6,
                height=18,
                cursor="hand2"
            ).pack(pady=(0, 12))

            print("[ERROR] Wrong camera selected.")
            return  # stop execution here 🚫

        # ✅ Camera works → start gaze session
        test_session = gaze_runner.GazeSession(enable_mouse_control=False, show_video=True)
        test_session.start()

        
        

 
       



