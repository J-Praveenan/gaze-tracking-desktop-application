import tkinter as tk
from tkinter import ttk
from frontend.theme import Colors, Fonts
from frontend.widgets import RoundedCard
from PIL import Image, ImageTk
import os
import subprocess
import sys
import utils.common as common 
from utils.common import speak_if_allowed, voice_tips_enabled, video_playing  




# Get the absolute project root (two levels up from this file)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

# Build paths dynamically
home_icon_path = os.path.join(ASSETS_DIR, "home.ico")
setting_icon_path = os.path.join(ASSETS_DIR, "setting.ico")
tips_icon_path = os.path.join(ASSETS_DIR, "tips.ico")
info_icon_path = os.path.join(ASSETS_DIR, "info.ico")
gaze_set_up_icon_path = os.path.join(ASSETS_DIR, "gaze_set_up.ico")
gaze_test_icon_path = os.path.join(ASSETS_DIR, "gaze_test.ico")
keyboard_icon_path = os.path.join(ASSETS_DIR, "keyboard.ico")
communicator_icon_path = os.path.join(ASSETS_DIR, "communicator.ico")
game_icon_path = os.path.join(ASSETS_DIR, "game.ico")

def F(name, default):
    return getattr(Fonts, name, default)

class Sidebar(RoundedCard):
    def __init__(self, parent, controller):
        super().__init__(parent, radius=18, pad=10, bg=Colors.dark_card, tight=False)
        self.place(relx=0.045, rely=0.45, anchor="w", relwidth=0.23, relheight=0.86)
        self.controller = controller
        self._nav_rows, self._nav_btns = {}, {}
        self._icons = {}
        self.selected_key = None
        self._build_sidebar(self.body)
        self.after(100, lambda: self.highlight_selected("home"))

    # ✅ Rebind hover highlight
    def _rebind_hover(self):
        for key, btn in self._nav_btns.items():
            btn.bind("<Enter>", lambda e, k=key: btn.configure(bg="#2b3947"))
            btn.bind("<Leave>", lambda e, k=key: (
                btn.configure(bg="#2b3947" if k == self.selected_key else Colors.sidebar_bg)
            ))

    def _build_sidebar(self, parent):
        parent.configure(bg=Colors.sidebar_bg)
        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)
        wrap.grid_rowconfigure(10, weight=1)

        def _nav_row(row_index, key, text, target_page, icon_path=None):
            cont = tk.Frame(wrap, bg=Colors.sidebar_bg)
            cont.grid(row=row_index, column=0, sticky="ew", pady=6)

            # load icon
            if icon_path and os.path.exists(icon_path):
                img = Image.open(icon_path).resize((20, 20), Image.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                self._icons[key] = icon
            else:
                icon = None

            # ✅ unified click handler
            def on_click():
                # Special case: open On-Screen Keyboard
                if key == "keyboard":
                    try:
                        # subprocess.Popen("osk.exe", shell=True)
                        # C:\Program Files\HotVirtualKeyboard
                        shortcut = r"C:\Users\Public\Desktop\Hot Virtual Keyboard.lnk"
                        subprocess.Popen(f'"{shortcut}"', shell=True)

                        root_window = self.controller.winfo_toplevel()
                        root_window.iconify()
                    except Exception as e:
                        print("Error launching On-Screen Keyboard:", e)
                    return

                # Step 1: highlight
                self.controller.selected_page_key = key
                self.highlight_selected(key)

                # Step 2: switch the page
                self.after(100, lambda: self.controller.show(target_page))
                self.after(250, lambda: self.highlight_selected(key))
                self.after(300, self._rebind_hover)

                # ✅ Step 3: voice tip (after navigation, if allowed)
                instructions = {
                    "HomePage": "You are now on the home page. You can start or stop gaze control here.",
                    "SetupPage": "This is the calibration setup page. Follow the dots with your eyes to complete calibration.",
                    "GazeTestPage": "This is the gaze test page. You can test and verify your gaze tracking.",
                    "TipsPage": "This page provides tips and guidance for better accuracy.",
                    "CommunicatorPage": "This is the communication aid page. You can select and speak messages using your gaze and blinks.",
                    "InfoPage": "This page shows detailed system information and controls.",
                    "SettingsPage": "You can configure reminders and accessibility settings here.",
                    "SokobanGamePage": "Welcome to the Sokoban game! Use your gaze to move the character and push boxes to their targets."
                }
                if target_page in instructions:
                    common.stop_speech()  # 🛑 stop previous speech first
                    speak_if_allowed(instructions[target_page])


            # ✅ Create button
            btn = tk.Button(
                cont,
                text=("  " + text),
                image=icon,
                compound="left",
                anchor="w",
                font=F("h3", ("Segoe UI", 12, "bold")),
                fg="white",
                bg=Colors.sidebar_bg,
                bd=0,
                relief="flat",
                activebackground="#31A0EB",
                activeforeground="white",
                cursor="hand2",
                command=on_click,
            )
            btn.configure(padx=12, pady=8)
            btn.bind("<Enter>", lambda e: btn.configure(bg="#2b3947"))
            btn.bind("<Leave>", lambda e: btn.configure(bg=Colors.sidebar_bg))
            btn.pack(fill="x", padx=6, pady=6)

            self._nav_rows[key] = cont
            self._nav_btns[key] = btn

        # === Sidebar navigation buttons ===
        r = 1
        _nav_row(r, "home", "Home", "HomePage", icon_path=home_icon_path); r += 1
        _nav_row(r, "setup", "Calibration", "SetupPage", icon_path=gaze_set_up_icon_path); r += 1
        _nav_row(r, "gaze_test", "Gaze Test", "GazeTestPage", icon_path=gaze_test_icon_path); r += 1
        _nav_row(r, "tips", "Tips", "TipsPage", icon_path=tips_icon_path); r += 1
        _nav_row(r, "communicator", "Communicator", "CommunicatorPage", icon_path=communicator_icon_path); r += 1
        _nav_row(r, "keyboard", "Virtual Keyboard", "KeyboardPage", icon_path=keyboard_icon_path); r += 1
        _nav_row(r, "sokoban", "Sokoban Game", "SokobanGamePage", icon_path=game_icon_path); r += 1
        # Spacer before bottom buttons
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=98, column=0, sticky="nsew");
        _nav_row(99, "info", "Information", "InfoPage", icon_path=info_icon_path); 
        _nav_row(100, "settings", "Settings", "SettingsPage", icon_path=setting_icon_path)



    # 🔹 Highlight selected sidebar item
    def highlight_selected(self, key):
        if key not in self._nav_rows:
            return
        self.selected_key = key
        for k, cont in self._nav_rows.items():
            if k == key:
                cont.configure(
                    bg=Colors.sidebar_bg,
                    highlightbackground="white",
                    highlightcolor="white",
                    highlightthickness=2,
                    bd=0,
                )
                self._nav_btns[k].configure(bg="#2b3947")
            else:
                cont.configure(bg=Colors.sidebar_bg, highlightthickness=0, bd=0)
                self._nav_btns[k].configure(bg=Colors.sidebar_bg)
