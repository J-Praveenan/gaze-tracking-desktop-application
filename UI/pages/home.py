import tkinter as tk
from tkinter import ttk, messagebox
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Sidebar
        self.sidebar = RoundedCard(self.overlay, radius=24, pad=0, bg=Colors.sidebar_bg)
        self.sidebar.place(relx=0.05, rely=0.53, anchor="w", relwidth=0.22, relheight=0.74)
        self._sidebar_menu(self.sidebar.body)

        # Main column
        self.main = tk.Frame(self.overlay, bg=self.overlay.cget("bg"), padx=10, pady=10)        
        self.main.place(relx=0.72, rely=0.52, anchor="center", relwidth=0.68, relheight=0.76)

        # Welcome
        top = RoundedCard(self.main, radius=16)
        top.pack(fill="x", pady=(0, 12))
        tk.Label(
            top.body,
            text=("Welcome to LOOK TRACK VISION\n"
                  "A smart assistant that lets you control your computer with just your eyes and voice.\n"
                  "Whether you're browsing, chatting, or presenting, it's all hands-free, intuitive, and empowering."),
            justify="center", font=Fonts.h3, fg=Colors.card_text, bg=top.cget("bg"),
            wraplength=720
        ).pack(padx=8, pady=10)

        # Control Mode
        mode = RoundedCard(self.main, radius=16)
        mode.pack(fill="x", pady=8)
        tk.Label(mode.body, text="Control Mode", font=Fonts.h2b, bg=mode.cget("bg"),
                 fg=Colors.card_head).pack(anchor="w")
        tk.Label(mode.body, text="Select how you want to control apps using your gaze – automatic or manual.",
                 font=Fonts.body, bg=mode.cget("bg"), fg=Colors.muted).pack(anchor="w", pady=(2, 10))
        self.mode_var = tk.StringVar(value="auto")
        ttk.Radiobutton(mode.body, text="Auto Control", value="auto", variable=self.mode_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(mode.body, text="Manual Control", value="manual", variable=self.mode_var).pack(anchor="w", pady=(0, 8))

        # Voice Tips
        voice = RoundedCard(self.main, radius=16)
        voice.pack(fill="x", pady=8)
        tk.Label(voice.body, text="Voice Tips", font=Fonts.h2b, bg=voice.cget("bg"),
                 fg=Colors.card_head).pack(anchor="w")
        tk.Label(voice.body, text="Turn voice tips ON or OFF while using gaze control.",
                 font=Fonts.body, bg=voice.cget("bg"), fg=Colors.muted).pack(anchor="w", pady=(2, 10))
        self.voice_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(voice.body, text="Turn ON", value=True, variable=self.voice_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(voice.body, text="Turn OFF", value=False, variable=self.voice_var).pack(anchor="w", pady=(0, 8))

        # Hide to tray (dark)
        tray = RoundedCard(self.main, radius=16, bg=Colors.dark_card)
        tray.pack(fill="x", pady=8)
        tk.Label(tray.body, text="Hide to tray", font=Fonts.h2b, bg=tray.cget("bg"),
                 fg="#ffffff").pack(anchor="w")
        tk.Label(tray.body, text="When enabled, the app will minimize and continue running in the background.",
                 font=Fonts.body, bg=tray.cget("bg"), fg="#cfd8e3").pack(anchor="w", pady=(2, 10))
        self.tray_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tray.body, text="Enable", variable=self.tray_var).pack(anchor="w", pady=(0, 8))

        # Tips
        tips = RoundedCard(self.main, radius=16)
        tips.pack(fill="x", pady=8)
        tk.Label(
            tips.body,
            text=("Look Up   : Move to the option above\n"
                  "Look Down : Move to the option below\n"
                  "Look Left : Go to the previous section or tab\n"
                  "Look Right: Go to the next section or tab\n"
                  "Blink     : Select / Toggle the highlighted option"),
            justify="left", font=Fonts.body, fg=Colors.tips, bg=tips.cget("bg")
        ).pack(anchor="w", pady=6)

        # Start application
        self.start_btn = PillButton(self.main, text="START APPLICATION   ⏻", command=self._start_app)
        self.start_btn.pack(anchor="se", pady=6)

    def _sidebar_menu(self, parent):
        items = [
            ("Home", True),
            ("Set Up Gaze Tracking", False),
            ("Apps Control", False),
            ("System Control", False),
            ("Tips", False),
            ("Information", False),
            ("Settings", False),
        ]
        for text, active in items:
            style = "NavActive.TButton" if active else "Nav.TButton"
            ttk.Button(parent, text=f"  {text}", style=style).pack(fill="x", padx=14, pady=(10, 0))

    def _start_app(self):
        # Hook to your gaze backend (main.py) here if desired
        messagebox.showinfo("LOOK TRACK VISION", "Start Application clicked.\nHook this to start your backend.")

    def on_show(self):
        pass
