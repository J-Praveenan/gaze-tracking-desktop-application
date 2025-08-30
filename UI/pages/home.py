import tkinter as tk
from tkinter import ttk, messagebox
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage

import sys, subprocess, threading
from pathlib import Path


class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Sidebar
        self.sidebar = RoundedCard(self.overlay, radius=24, pad=0, bg=Colors.sidebar_bg)
        self.sidebar.place(relx=0.05, rely=0.53, anchor="w", relwidth=0.22, relheight=0.74)
        self.sidebar_buttons = {}  # keep refs so we can disable/enable
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
            ("Home", True, None),
            ("Set Up Gaze Tracking", False, self._run_calibration),  # wired
            ("Gaze Tracker", False, self._run_gaze_tracker),
            ("Apps Control", False, None),
            ("System Control", False, None),
            ("Tips", False, None),
            ("Information", False, None),
            ("Settings", False, None),
        ]
        for text, active, cmd in items:
            style = "NavActive.TButton" if active else "Nav.TButton"
            btn = ttk.Button(parent, text=f"  {text}", style=style, command=cmd)
            btn.pack(fill="x", padx=14, pady=(10, 0))
            self.sidebar_buttons[text] = btn

    def _start_app(self):
        messagebox.showinfo("LOOK TRACK VISION", "Start Application clicked.\nHook this to start your backend.")

    def _run_calibration(self):
        """Launch Calibration/Calibration.py in a separate process so Tk stays responsive."""
        calib_path = self._find_calibration_script()
        if not calib_path:
            messagebox.showerror("Calibration", "Could not find Calibration.py (looked under ./Calibration/).")
            return

        btn = self.sidebar_buttons.get("Set Up Gaze Tracking")
        if btn:
            btn.state(['disabled'])

        def work():
            rc = -1
            try:
                rc = subprocess.run([sys.executable, "-u", str(calib_path)]).returncode
            except Exception:
                rc = -1

            def done():
                if btn:
                    btn.state(['!disabled'])
                if rc == 0:
                    messagebox.showinfo("Calibration", "Calibration complete. Thresholds saved.")
                else:
                    messagebox.showwarning("Calibration", "Calibration cancelled or failed. Check console output.")
            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()
        
        
        
    def _run_gaze_tracker(self):
        """
        Launch main.py in a separate process so the Tk UI stays responsive.
        """
        main_path = self._find_main_script()
        if not main_path:
            messagebox.showerror("Gaze Tracker", "Could not find main.py.")
            return

        btn = self.sidebar_buttons.get("Gaze Tracker")
        if btn:
            btn.state(['disabled'])

        def work():
            rc = -1
            try:
                # -u for unbuffered prints; run with same interpreter
                rc = subprocess.run([sys.executable, "-u", str(main_path)]).returncode
            except Exception:
                rc = -1

            def done():
                if btn:
                    btn.state(['!disabled'])
                if rc == 0:
                    messagebox.showinfo("Gaze Tracker", "Gaze tracker closed.")
                else:
                    messagebox.showwarning("Gaze Tracker", "Gaze tracker ended with an error. Check console.")
            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _find_main_script(self) -> Path | None:
        """
        Try to locate main.py (your gaze tracker) in common places.
        Adjust as needed if you keep it elsewhere.
        """
        candidates = [
            Path.cwd() / "main.py",
            Path(__file__).resolve().parents[2] / "main.py",      # project root
            Path(__file__).resolve().parent / "main.py",          # same folder (unlikely)
        ]
        for p in candidates:
            if p.exists():
                return p
        return None


    def _find_calibration_script(self) -> Path | None:
        """Try to locate Calibration.py or calibration.py in a Calibration/ folder."""
        candidates = [
            Path.cwd() / "Calibration" / "Calibration.py",
            Path.cwd() / "Calibration" / "calibration.py",
            Path(__file__).resolve().parent / "Calibration" / "Calibration.py",
            Path(__file__).resolve().parent / "Calibration" / "calibration.py",
            Path(__file__).resolve().parents[1] / "Calibration" / "Calibration.py",
            Path(__file__).resolve().parents[1] / "Calibration" / "calibration.py",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def on_show(self):
        pass
