import tkinter as tk
from tkinter import messagebox
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage
from utils.common import speak, voice_tips_enabled
from .sidebar import Sidebar
import threading
from UI.pages import gaze_runner
import winsound
from win10toast import ToastNotifier
from winotify import Notification, audio
import time
import pyttsx3
from PIL import Image, ImageTk
import os
from pathlib import Path
import json
from UI.widgets import RoundedButton  # 👈 add import


gaze_thread = None  # global reference
stop_reminder_event = threading.Event()


def F(name, default):
    return getattr(Fonts, name, default)


def launch_gaze_app(enable_mouse_control=False):
    global gaze_thread, stop_reminder_event
    try:
        
        # 🟢 Start gaze control in background
        if enable_mouse_control:
            # Reset stop flag for both gaze and reminder
            stop_reminder_event.clear()
            # 🟢 Start gaze control only if not already running
            if gaze_thread and gaze_thread.is_alive():
                print("[INFO] Gaze already running.")
                return

            from UI.pages import gaze_runner
            gaze_thread = threading.Thread(
                target=lambda: gaze_runner.main(enable_mouse_control=True, show_video=False),
                daemon=True
            )
            gaze_thread.start()
        else:
            # 🟥 Stop gaze control
            from UI.pages import gaze_runner
            gaze_runner.stop_gaze()
            print("[INFO] Stop request sent to gaze thread.")
        
        
        # 🕒 Load reminder settings
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "Data"
        data_dir.mkdir(exist_ok=True)
        settings_path = data_dir / "notification_remainder_time.json"
        reminder_enabled = False
        reminder_minutes = 10
        
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    data = json.load(f)
                    reminder_enabled = data.get("enabled", False)
                    reminder_minutes = data.get("duration", 10)
            except Exception:
                pass

        # 🕒 Start reminder if enabled
        if enable_mouse_control and reminder_enabled:
            def rest_reminder_timer():
                start_time = time.time()
                while not stop_reminder_event.is_set():
                    elapsed = time.time() - start_time
                    if elapsed >= reminder_minutes * 60:
                        # 🔔 Time’s up → show notification only once
                        winsound.Beep(800, 400)

                        base_dir = Path(__file__).resolve().parents[2]
                        assets_dir = base_dir / "assets"
                        icon_path = assets_dir / "eyelogo.ico"

                        toast = Notification(
                            app_id="Look Track Vision",
                            title="Eye Care Reminder",
                            msg=f"You've been using Look Track Vision for {reminder_minutes} minutes.\nTake a short rest!",
                            icon=str(icon_path),
                            duration="long"
                        )
                        toast.set_audio(audio.Reminder, loop=False)
                        toast.show()
                        speak(f"You have been using Look Track Vision for {reminder_minutes} minutes. Take a short rest!")

                        break  # exit loop after first notification
                    time.sleep(1)

            threading.Thread(target=rest_reminder_timer, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to start gaze system:\n{e}")


class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # === Layout: Sidebar + Main Column ===
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)


        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 20))
        self.main_col.grid_rowconfigure(0, weight=1)
        self.main_col.grid_columnconfigure(0, weight=1)

        self._build_home_content(self.main_col)

    # ----------------------------------------------------------------
    def _build_home_content(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        fr.pack(fill="both", expand=True)

        # === Hero Card ===
        hero = RoundedCard(fr, radius=18, pad=20, bg=Colors.dark_card, tight=True)
        hero.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(hero.body, text="Welcome to LOOK TRACK VISION",
                 fg="white", bg=Colors.dark_card,
                 font=F("h1b", ("Segoe UI", 20, "bold"))).pack(pady=(2, 0))

        subtitle = tk.Label(
            hero.body,
            text=("A smart assistant that lets you control your computer with just your eyes and voice.\n"
                  "Whether you're browsing, chatting, or presenting, it's all hands-free, intuitive, and empowering."),
            fg="#e8eef6", bg=Colors.dark_card, justify="center",
            font=F("body", ("Segoe UI", 10))
        )
        subtitle.pack(pady=(0, 4))
        subtitle.configure(wraplength=400)
        hero.body.bind("<Configure>", lambda e: subtitle.configure(
            wraplength=max(150, int(e.width * 0.92))
        ))

        # === Scrollable Canvas ===
        canvas = tk.Canvas(fr, bg=Colors.page_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(fr, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.page_bg)
        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # Adjust scrollable area dynamically
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(fill="both", expand=True, side="left")
        scrollbar.pack(side="right", fill="y")

        # === Mouse wheel scroll support (same as InfoPage) ===
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _unbind_scroll(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        scroll_frame.bind("<Enter>", _bind_scroll)
        scroll_frame.bind("<Leave>", _unbind_scroll)

        # === Row frame for Control Mode & Voice Tips ===
        row_frame = tk.Frame(scroll_frame, bg=Colors.page_bg)
        row_frame.pack(fill="x", padx=8, pady=(8, 4))
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=1)

        # Create cards
        control_card = self._make_card(
            row_frame, "Control Mode",
            "Select how you want to control apps using your gaze – automatic or manual.",
            [("Auto Control", "auto"), ("Manual Control", "manual")]
        )
        voice_var = tk.StringVar(value="on")

        def on_voice_change(*_):
            import utils.common as common
            common.voice_tips_enabled = (voice_var.get() == "on")
            state = "enabled" if common.voice_tips_enabled else "disabled"
            common.speak(f"Voice tips {state}.")



        voice_var.trace_add("write", on_voice_change)

        voice_card = self._make_card(
            row_frame, "Voice Tips",
            "Turn voice tips ON or OFF while using gaze control.",
            [("Turn ON", "on"), ("Turn OFF", "off")],
            radio_var=voice_var
        )


        # Initially position them side-by-side
        control_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        voice_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        # Adjust layout on resize
        def adjust_layout(event):
            if event.width < 600:
                # Stack vertically on small screens
                control_card.grid_configure(row=0, column=0, columnspan=2, padx=0)
                voice_card.grid_configure(row=1, column=0, columnspan=2, padx=0)
            else:
                # Side by side on large screens
                control_card.grid_configure(row=0, column=0, columnspan=1, padx=(0, 8))
                voice_card.grid_configure(row=0, column=1, columnspan=1, padx=(8, 0))

        row_frame.bind("<Configure>", adjust_layout)



        # === Hide to Tray ===
        self._make_checkbox_card(scroll_frame)

        # === Instructions ===
        self._make_instruction_section(scroll_frame, "Eye & Blink Controls", [
    ("👀", "Eye Movement", "Pointer moves in the direction you look (Left, Right, Up, Down, Center)"),
    ("🎯", "App Open", "Pointer starts at the center of the screen when the application launches"),
    ("✨", "Both Eyes Blink", "Cycles pointer position in order — Left → Top → Right → Bottom → Center"),
    ("👁️", "Left Eye Blink", "Performs a Left Click"),
    ("👁️", "Right Eye Blink", "Performs a Right Click"),
("😴", "Long Blink ( > 2s )", 
 "Activates Scroll Mode — after activation, looking up scrolls up and looking down scrolls down until another long blink disables it."),
])


        self._make_instruction_section(scroll_frame, "Interface", [
            ("➡️", "Sidebar Arrow", "Right-center arrow → open instructions"),
        ])

        # === Start / Stop Application Button with Icon ==

        ASSETS_DIR = os.path.join(os.path.dirname(__file__), "../../assets")
        power_on_path = os.path.join(ASSETS_DIR, "power_on.png")
        power_off_path = os.path.join(ASSETS_DIR, "power_off.png")

        # Load icons safely
        def load_icon(path, size=(22, 22)):
            try:
                img = Image.open(path).resize(size, Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        power_on_icon = load_icon(power_on_path)
        power_off_icon = load_icon(power_off_path)
        
        self.power_on_icon = power_on_icon
        self.power_off_icon = power_off_icon


        # --- Button state ---
        self.app_running = False

        def toggle_app():
            app = self.controller  # ✅ reference to App
            app._handle_global_gaze_toggle(not self.app_running)



        # --- Right-aligned START button ---
        btn_frame = tk.Frame(scroll_frame, bg=Colors.page_bg)
        btn_frame.pack(fill="x", pady=(20, 10))

        self.start_btn = RoundedButton(
            btn_frame,
            text="START APPLICATION",
            radius=25,
            padding_x=22,
            padding_y=10,
            bg="#31A0EB",
            activebg="#31A0EB",
            icon=self.power_on_icon,
            command=toggle_app
        )
        self.start_btn.pack(side="right", padx=(0, 20))



        # Spacer
        tk.Frame(scroll_frame, height=40, bg=Colors.page_bg).pack(fill="x")

    # ----------------------------------------------------------------
    # Reusable UI helpers
    def _make_card(self, parent, title, desc, options, radio_var=None):
        card = RoundedCard(parent, radius=12, pad=12,
                       bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        # Remove .pack() here
        tk.Label(card.body, text=title,
                fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))
                ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))
        tk.Label(card.body, text=desc,
                fg=Colors.card_text, bg=Colors.glass_bg,
                font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        var = radio_var or tk.StringVar(value=options[0][1])
        for i, (label, value) in enumerate(options):
            tk.Radiobutton(card.body, text=label, variable=var, value=value,
                        bg=Colors.glass_bg, anchor="w").grid(row=2, column=i, sticky="w", padx=16, pady=(0, 10))

        return card


    def _make_checkbox_card(self, parent):
        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=6, padx=8)

        tray_var = tk.BooleanVar(value=False)

        def toggle_tick():
            # tray_toggle.config(text="✔" if tray_var.get() else "")
            root_window = self.winfo_toplevel()

            if tray_var.get():
                # ✅ Instantly show tick before minimizing
                tray_toggle.config(text="✔")
                root_window.update_idletasks()  # force UI refresh before minimize

                # ✅ Minimize app window to taskbar (hide to tray)
                root_window.after(100, root_window.iconify)
                speak("Application minimized to tray.")
            else:
                # ✅ Optional: restore app window when unchecked
                root_window.deiconify()
                tray_toggle.config(text="")
                speak("Application restored.")
                
        # When the window is restored manually (e.g., from taskbar)
        def on_restore(event):
            tray_var.set(False)
            tray_toggle.config(text="")

        # Bind to window deiconify event
        self.bind_all("<Map>", on_restore)

        tk.Label(card.body, text="Hide to tray",
                 fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w")

        tray_toggle = tk.Checkbutton(
            card.body, variable=tray_var, indicatoron=False,
            text="", width=2, height=1, command=toggle_tick,
            bg="white", fg=Colors.glass_bg, font=("Segoe UI", 10, "bold")
        )
        tray_toggle.grid(row=0, column=1, sticky="e", padx=(8, 0))

        tk.Label(card.body,
                 text="When enabled, the app will minimize and continue running in the background.",
                 fg=Colors.card_text, bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 9)),
                 wraplength=400, justify="left"
                 ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        toggle_tick()

    def _make_instruction_section(self, parent, title, entries):
        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.dark_card, border_color=Colors.dark_card, border_width=0)
        card.pack(fill="x", pady=8, padx=8)

        tk.Label(card.body, text=title,
                 fg="white", bg=Colors.dark_card,
                 font=F("h2b", ("Segoe UI", 12, "bold"))
                 ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        for i, (icon, label, desc) in enumerate(entries, start=1):
            # Add fixed-width container for uniform alignment
            label_text = f"{icon:<3} {label}"  # 👈 Ensures consistent spacing for emojis
            tk.Label(card.body, text=label_text,
                    fg="white", bg=Colors.dark_card,
                    font=F("body", ("Segoe UI", 10, "bold")),
                    anchor="w", justify="left", width=22  # 👈 fixed width for uniform column
                    ).grid(row=i, column=0, sticky="w", padx=(6, 0), pady=2)

            tk.Label(card.body, text=desc,
                     fg="#d1d5db", bg=Colors.dark_card,
                     font=F("body", ("Segoe UI", 10))
                     ).grid(row=i, column=1, sticky="w", padx=(6, 0), pady=2)
            
    def update_gaze_button(self, running: bool):
        """Update the HomePage START/STOP button to match global state."""
        self.app_running = running
        if running:
            self.start_btn.bg = "#F65353"
            self.start_btn.activebg = "#F65353"
            self.start_btn.text = "STOP APPLICATION"
            self.start_btn.icon = self.power_off_icon
        else:
            self.start_btn.bg = "#31A0EB"
            self.start_btn.activebg = "#31A0EB"
            self.start_btn.text = "START APPLICATION"
            self.start_btn.icon = self.power_on_icon

        self.start_btn.delete("all")
        self.start_btn._draw_button()


