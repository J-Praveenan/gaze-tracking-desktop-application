import tkinter as tk
from tkinter import messagebox
from frontend.theme import Colors, Fonts
from frontend.widgets import RoundedCard, RoundedButton
from .base import BasePage
import threading
import winsound
from winotify import Notification, audio
import time
import pyttsx3
from PIL import Image, ImageTk
import os
from pathlib import Path
import json
from frontend.pages.instruction_tray import InstructionTray

from frontend.pages import gaze_runner

main_gaze_session = None  # global session variable

# Global control thread state
gaze_thread = None
stop_reminder_event = threading.Event()


def F(name, default):
    """Font helper"""
    return getattr(Fonts, name, default)


def speak(message):
    """Speak helper using pyttsx3"""
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()



# =====================================================================
# Launch / Stop Gaze Control + Reminder Timer
# =====================================================================
# =====================================================================
# Launch / Stop Gaze Control + Reminder Timer
# =====================================================================
def launch_gaze_app(enable_mouse_control=False):
    global gaze_thread, stop_reminder_event, main_gaze_session
    try:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "Data"
        data_dir.mkdir(exist_ok=True)
        config_path = data_dir / "configuration.json"

        # Load unified configuration
        reminder_enabled = False
        reminder_minutes = 10
        control_mode = "auto"

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    reminder_enabled = config.get("reminder", {}).get("enabled", False)
                    reminder_minutes = config.get("reminder", {}).get("duration", 10)
                    control_mode = config.get("control", {}).get("mode", "auto")
            except Exception as e:
                print(f"[WARN] Could not parse configuration.json: {e}")

        # ==============================================================
        # ✅ FINAL SAFEGUARD — Prevent unwanted gaze start in manual mode
        # ==============================================================
        if control_mode == "manual":
            if not enable_mouse_control:
                print("[INFO] Manual Control Mode: standby — system loaded but gaze tracking is OFF until voice command.")
                return
            else:
                print("[INFO] Manual Control Mode: 'Start gaze control' voice command received — enabling gaze tracking.")
        else:
            print("[INFO] Auto Control Mode: starting gaze control automatically.")

        # ==============================================================
        # === Main Gaze Logic ===
        # ==============================================================
        if enable_mouse_control:
            stop_reminder_event.clear() 
            if main_gaze_session and main_gaze_session.thread and main_gaze_session.thread.is_alive():
                print("[INFO] Main gaze control already running.")
                return

            print("[INFO] Starting main gaze tracking session...")
            main_gaze_session = gaze_runner.GazeSession(enable_mouse_control=True, show_video=False)
            main_gaze_session.start()
            print("[INFO] Gaze session started successfully.")

        else:
            # 🛑 Stop gaze and reminder threads
            stop_reminder_event.set()
            print("[INFO] Stopping gaze control and reminder thread...")
            
            if main_gaze_session:
                print("[INFO] Stopping active gaze session...")
                main_gaze_session.stop()
                main_gaze_session = None
                print("[INFO] Gaze session stopped.")

        # ==============================================================
        # === Rest Reminder Logic ===
        # ==============================================================
        if enable_mouse_control and reminder_enabled:
            def rest_reminder_timer():
                start_time = time.time()
                while not stop_reminder_event.is_set():
                    elapsed = time.time() - start_time
                    if elapsed >= reminder_minutes * 60:
                        print(f"[INFO] Eye rest reminder triggered after {reminder_minutes} minutes.")
                        winsound.Beep(800, 400)
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

                        speak(
                            f"You have been using Look Track Vision for {reminder_minutes} minutes. "
                            f"Please take a short rest."
                        )
                        break
                    time.sleep(1)

            threading.Thread(target=rest_reminder_timer, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to start gaze system:\n{e}")
        print(f"[ERROR] Failed to start gaze system: {e}")

# =====================================================================
# Home Page frontend
# =====================================================================
class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)
        
        

        # Layout setup
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)

        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 20))
        self.main_col.grid_rowconfigure(0, weight=1)
        self.main_col.grid_columnconfigure(0, weight=1)

        self.app_running = False
        self._build_home_content(self.main_col)


        

    # -----------------------------------------------------------------
    def _build_home_content(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        fr.pack(fill="both", expand=True)

        # === Hero Section ===
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
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(fill="both", expand=True, side="left")
        scrollbar.pack(side="right", fill="y")


        # Enable smooth independent scrolling
        self.enable_scroll(canvas, scroll_frame)


        # === CONTROL MODE + SYSTEM STATUS ===
        row_frame = tk.Frame(scroll_frame, bg=Colors.page_bg)
        row_frame.pack(fill="x", padx=8, pady=(8, 4))
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=1)

        control_card = self._make_card(
            row_frame, "Control Mode",
            "Select how you want to control apps using your gaze – automatic or manual.",
            [("Auto Control", "auto"), ("Manual Control", "manual")]
        )

        # --- System Status ---
        from utils import common
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "Data"
        reminder_path = data_dir / "notification_remainder_time.json"

        reminder_enabled, reminder_duration = False, 0
        if reminder_path.exists():
            try:
                with open(reminder_path, "r") as f:
                    data = json.load(f)
                    reminder_enabled = data.get("enabled", False)
                    reminder_duration = data.get("duration", 10)
            except Exception:
                pass

        # Create the card
        self.status_card = RoundedCard(
    row_frame, radius=12, pad=12,
    bg=Colors.glass_bg, border_color="#4b5563", border_width=2
)


        # --- Title ---
        tk.Label(
            self.status_card.body,
            text="System Status",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 12, "bold"))
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 6))

        # --- Helper to make neat aligned rows ---
        def add_status_row(r, c, icon, label, value, color_icon="#1e293b", color_value="#111827"):
            frame = tk.Frame(self.status_card.body, bg=Colors.glass_bg)
            frame.grid(row=r, column=c, sticky="nsew", padx=10, pady=5)

            tk.Label(frame, text=icon, fg=color_icon, bg=Colors.glass_bg, font=("Segoe UI Emoji", 11)).pack(side="left", padx=(0, 4))
            tk.Label(frame, text=f"{label}:", fg=Colors.card_text, bg=Colors.glass_bg,
                    font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
            tk.Label(frame, text=value, fg=color_value, bg=Colors.glass_bg,
                    font=("Segoe UI", 10)).pack(side="left")


        # --- Add neatly aligned rows ---
        # Row 1
        add_status_row(1, 0, "🎯", "Gaze Control", "Enabled" if self.app_running else "Disabled")
        add_status_row(1, 1, "🔊", "Voice Tips", "Enabled" if common.voice_tips_enabled else "Disabled")

        # Row 2
        add_status_row(2, 0, "🔔", "Voice Confirmation", "Enabled" if common.voice_action_confirmation else "Disabled")
        add_status_row(2, 1, "⏰", "Rest Reminder", f"ON ({reminder_duration} min)" if reminder_enabled else "OFF")

        for i in range(2):
            self.status_card.body.grid_columnconfigure(i, weight=1)


        self.status_card.body.grid_columnconfigure(2, weight=1)

        # --- Place both cards ---
        control_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.status_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))


        # ✅ Force equal height for both cards
        def sync_card_heights():
            self.status_card.update_idletasks()
            control_card.update_idletasks()

            # Get both total card heights (outer frames)
            h1 = self.status_card.winfo_height()
            h2 = control_card.winfo_height()
            max_h = max(h1, h2)

            # Apply the same height to both outer cards and inner bodies
            self.status_card.configure(height=max_h)
            control_card.configure(height=max_h)
            self.status_card.body.configure(height=max_h - 30)
            control_card.body.configure(height=max_h - 30)

        # Run once and bind for resizing
        row_frame.after(200, sync_card_heights)
        row_frame.bind("<Configure>", lambda e: sync_card_heights())


        # Run once and bind for resizing
        row_frame.after(100, sync_card_heights)
        row_frame.bind("<Configure>", lambda e: sync_card_heights())


        # control_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        # self.status_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        # Responsive stacking
        def adjust_layout(event):
            if event.width < 950:
                control_card.grid_configure(row=0, column=0, columnspan=2, padx=0)
                self.status_card.grid_configure(row=1, column=0, columnspan=2, padx=0)
            else:
                control_card.grid_configure(row=0, column=0, columnspan=1, padx=(0, 8))
                self.status_card.grid_configure(row=0, column=1, columnspan=1, padx=(8, 0))

        row_frame.bind("<Configure>", adjust_layout)

        # === Eye & Blink Controls ===
        self._make_instruction_section(scroll_frame, "Eye & Blink Controls", [
            ("👀", "Eye Movement", "Pointer moves in the direction you look."),
            ("🎯", "App Open", "Pointer starts at the center when the app launches."),
            ("✨", "Both Eyes Blink", "Cycles pointer position."),
            ("👁️", "Left Eye Blink", "Performs a Left Click."),
            ("👁️", "Right Eye Blink", "Performs a Right Click."),
            ("😴", "Long Blink (>2s)", "Activates Scroll Mode — look up/down to scroll."),
        ])

        # === Start / Stop Button ===
        ASSETS_DIR = os.path.join(os.path.dirname(__file__), "../../assets")
        power_on_path = os.path.join(ASSETS_DIR, "power_on.ico")
        power_off_path = os.path.join(ASSETS_DIR, "power_off.ico")

        def load_icon(path, size=(22, 22)):
            try:
                img = Image.open(path).resize(size, Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        self.power_on_icon = load_icon(power_on_path)
        self.power_off_icon = load_icon(power_off_path)

        def toggle_app():
            app = self.controller
            app._handle_global_gaze_toggle(not self.app_running)

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

       

    # -----------------------------------------------------------------
    def refresh_status(self):
        """Rebuilds the aligned System Status section dynamically in 2×2 grid layout."""
        from utils import common
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "Data"
        config_path = data_dir / "configuration.json"

        reminder_enabled, reminder_duration = False, 0
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    reminder_enabled = config.get("reminder", {}).get("enabled", False)
                    reminder_duration = config.get("reminder", {}).get("duration", 10)
            except Exception:
                pass

        # Clear previous rows before redrawing
        for widget in self.status_card.body.winfo_children():
            widget.destroy()

        # Title
        tk.Label(
            self.status_card.body,
            text="System Status",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 12, "bold"))
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 6))

        # Helper for neat grid layout
        def add_status_row(r, c, icon, label, value, color_icon="#1e293b", color_value="#111827"):
            frame = tk.Frame(self.status_card.body, bg=Colors.glass_bg)
            frame.grid(row=r, column=c, sticky="nsew", padx=10, pady=9)
            tk.Label(frame, text=icon, fg=color_icon, bg=Colors.glass_bg, font=("Segoe UI Emoji", 11)).pack(side="left", padx=(0, 4))
            tk.Label(frame, text=f"{label}:", fg=Colors.card_text, bg=Colors.glass_bg,
                    font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
            tk.Label(frame, text=value, fg=color_value, bg=Colors.glass_bg,
                    font=("Segoe UI", 10)).pack(side="left")

        # Row 1
        add_status_row(1, 0, "🎯", "Gaze Control", "Enabled" if self.app_running else "Disabled")
        add_status_row(1, 1, "🔊", "Voice Tips", "Enabled" if common.voice_tips_enabled else "Disabled")

        # Row 2
        add_status_row(2, 0, "🔔", "Voice Confirmation", "Enabled" if common.voice_action_confirmation else "Disabled")
        add_status_row(2, 1, "⏰", "Rest Reminder", f"ON ({reminder_duration} min)" if reminder_enabled else "OFF")

        for i in range(2):
            self.status_card.body.grid_columnconfigure(i, weight=1)


    def on_show(self):
        """Called when HomePage is shown again."""
        self.refresh_status()

    # -----------------------------------------------------------------
    def _make_card(self, parent, title, desc, options, radio_var=None):
        """Reusable card for control settings with persistent Auto/Manual Control mode."""
        card = RoundedCard(
            parent, radius=12, pad=12,
            bg=Colors.glass_bg, border_color="#4b5563", border_width=2
        )

        tk.Label(
            card.body, text=title,
            fg=Colors.card_head, bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 12, "bold"))
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))

        tk.Label(
            card.body, text=desc,
            fg=Colors.card_text, bg=Colors.glass_bg,
            font=F("body", ("Segoe UI", 10))
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        # === Load info icon ===
        base_dir = Path(__file__).resolve().parents[2]
        assets_dir = base_dir / "assets"
        info_icon_path = assets_dir / "info_icon.ico"

        info_img = None
        if info_icon_path.exists():
            img = Image.open(info_icon_path).resize((14, 14), Image.LANCZOS)
            info_img = ImageTk.PhotoImage(img)

        # === Persistent config handling ===
        def _load_control_mode():
            """Read saved control mode ('auto' or 'manual') from configuration.json."""
            try:
                config_path = base_dir / "Data" / "configuration.json"
                if config_path.exists():
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        return config.get("control", {}).get("mode", "auto")
            except Exception:
                pass
            return "auto"  # default fallback

        def _save_control_mode(new_mode):
            """Save selected control mode ('auto' or 'manual') to configuration.json."""
            try:
                data_dir = base_dir / "Data"
                data_dir.mkdir(exist_ok=True)
                config_path = data_dir / "configuration.json"

                config = {}
                if config_path.exists():
                    with open(config_path, "r") as f:
                        config = json.load(f)

                config.setdefault("control", {})
                config["control"]["mode"] = new_mode

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)

                print(f"[INFO] Saved control mode: {new_mode}")
            except Exception as e:
                print(f"[WARN] Failed to save control mode: {e}")

        # === Tooltip helper ===
        def create_tooltip(widget, text):
            tooltip = tk.Toplevel(widget)
            tooltip.withdraw()
            tooltip.overrideredirect(True)
            tooltip.attributes("-topmost", True)
            tooltip.attributes("-alpha", 0.95)

            canvas = tk.Canvas(
                tooltip, bg="#1f2937", highlightthickness=0, bd=0, width=300, height=0
            )
            canvas.pack(fill="both", expand=True)

            def draw_rounded_rect(x1, y1, x2, y2, radius=12, color="#1f2937"):
                canvas.create_rectangle(x1 + radius, y1, x2 - radius, y1 + radius, fill=color, outline=color)
                canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=color, outline=color)
                canvas.create_rectangle(x1 + radius, y2 - radius, x2 - radius, y2, fill=color, outline=color)
                canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, start=90, extent=90, fill=color, outline=color)
                canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, start=0, extent=90, fill=color, outline=color)
                canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, start=180, extent=90, fill=color, outline=color)
                canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, start=270, extent=90, fill=color, outline=color)

            text_item = canvas.create_text(
                20, 20, text=text, anchor="nw", fill="white",
                font=("Segoe UI", 9), width=260
            )
            bbox = canvas.bbox(text_item)
            padding = 20
            new_h = (bbox[3] - bbox[1]) + padding * 2
            new_w = 300
            canvas.config(height=new_h)
            draw_rounded_rect(5, 5, new_w - 5, new_h - 5, radius=12)
            canvas.tag_raise(text_item)

            def on_enter(_):
                x = widget.winfo_rootx() + 25
                y = widget.winfo_rooty() + 25
                tooltip.geometry(f"+{x}+{y}")
                tooltip.deiconify()
                tooltip.lift()

            def on_leave(_):
                tooltip.withdraw()

            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        # === Build radio buttons ===
        var = radio_var or tk.StringVar(value=_load_control_mode())

        def on_mode_change():
            _save_control_mode(var.get())

        for i, (label, value) in enumerate(options):
            option_frame = tk.Frame(card.body, bg=Colors.glass_bg)
            option_frame.grid(row=2, column=i, sticky="w", padx=20, pady=(5, 10))

            rb = tk.Radiobutton(
                option_frame,
                text=label,
                variable=var,
                value=value,
                command=on_mode_change,  # 💾 Save mode on select
                bg=Colors.glass_bg,
                anchor="w",
                font=("Segoe UI", 11),
                padx=6,
                pady=5,
                indicatoron=True,
                relief="flat",
                highlightthickness=0
            )
            rb.pack(side="left")

            # === Info Icon ===
            if info_img:
                icon_label = tk.Label(option_frame, image=info_img, bg=Colors.glass_bg, cursor="hand2")
                icon_label.image = info_img
                icon_label.pack(side="left", padx=(6, 0))
            else:
                icon_label = tk.Label(option_frame, text="ℹ️", bg=Colors.glass_bg, fg="#0078D7", cursor="hand2")
                icon_label.pack(side="left", padx=(6, 0))

            # Tooltip text for each mode
            tip_text = (
                "Auto Control:\n"
                "Automatically starts gaze tracking once the app launches.\n"
                "Your eyes and blinks directly control the system — no manual activation needed."
            ) if "auto" in value.lower() else (
                "Manual Control:\n"
                "System is ready but waits for you to enable gaze tracking manually.\n"
                "Useful to avoid accidental gaze actions.\n\n"
                "🗣️ Say 'Start gaze control' — the mouse pointer will follow your gaze.\n"
                "🗣️ Say 'Stop gaze control' — gaze tracking stops without closing the app."
            )
            create_tooltip(icon_label, tip_text)

        card.body.update_idletasks()
        return card

    # -----------------------------------------------------------------
    def _make_instruction_section(self, parent, title, entries=None):
        """Builds Eye & Blink Controls section (aligned layout, stable popup, scroll-safe)."""
        card = RoundedCard(parent, radius=12, pad=12,
                        bg=Colors.dark_card, border_color=Colors.dark_card, border_width=0)
        card.pack(fill="x", pady=8, padx=8)

        tk.Label(
            card.body,
            text=title,
            fg="white",
            bg=Colors.dark_card,
            font=F("h2b", ("Segoe UI", 12, "bold"))
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=3)

        # === Load icons ===
        base_dir = Path(__file__).resolve().parents[2]
        assets = os.path.join(base_dir, "assets")

        def load_icon(name, size=(28, 28)):
            try:
                return ImageTk.PhotoImage(Image.open(os.path.join(assets, name)).resize(size, Image.LANCZOS))
            except Exception:
                print(f"[WARN] Could not load {name}")
                return None

        icons = {
            "up": load_icon("up.ico"),
            "down": load_icon("down.ico"),
            "left": load_icon("left.ico"),
            "right": load_icon("right.ico"),
            "left_blink": load_icon("left_eye_blink.ico"),
            "right_blink": load_icon("right_eye_blink.ico"),
            "closed_short": load_icon("closed_less_than_2mins.ico"),
            "closed_long": load_icon("closed_greater_than_2mins.ico"),
            "info": load_icon("info.ico", size=(14, 14)),
        }

        controls = [
            (icons["up"], "Look Up", "Move Pointer Up"),
            (icons["down"], "Look Down", "Move Pointer Down"),
            (icons["left"], "Look Left", "Move Pointer Left"),
            (icons["right"], "Look Right", "Move Pointer Right"),
            (icons["left_blink"], "Left Blink", "Left Click"),
            (icons["right_blink"], "Right Blink", "Right Click"),
            (icons["closed_long"], "Long Blink", "Scroll Mode Enable/Disable (Look Up/Down to scroll)"),
            (icons["closed_short"], "Short Blink", "Cycle Pointer Position"),
        ]

        # === Track popup state ===
        self.cycle_popup = None
        self.popup_visible = False

        def close_cycle_popup():
            """Safely close the popup and restore normal scrolling."""
            if self.cycle_popup and self.cycle_popup.winfo_exists():
                try:
                    self.cycle_popup.destroy()
                except tk.TclError:
                    pass
            self.cycle_popup = None
            self.popup_visible = False
            # Unbind outside click detection — restores scroll usability
            if hasattr(self, "_popup_click_binding"):
                self.unbind_all("<Button-1>")
                self._popup_click_binding = None

        def show_cycle_popup(widget):
            """Toggle popup visibility near info icon."""
            if self.popup_visible:
                close_cycle_popup()
                return

            popup = tk.Toplevel(card)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(bg=Colors.dark_card, padx=6, pady=6, bd=1, relief="solid")

            try:
                cycle_img = ImageTk.PhotoImage(
                    Image.open(os.path.join(assets, "cycle_blink.ico")).resize((280, 280), Image.LANCZOS)
                )
                lbl = tk.Label(popup, image=cycle_img, bg=Colors.dark_card)
                lbl.image = cycle_img
                lbl.pack()
            except Exception:
                tk.Label(
                    popup, text="Cycle Blink Pattern", fg="white", bg=Colors.dark_card
                ).pack(padx=10, pady=10)

            # Position popup near icon
            x = widget.winfo_rootx() - 110
            y = widget.winfo_rooty() - 300
            popup.geometry(f"+{x}+{y}")

            self.cycle_popup = popup
            self.popup_visible = True

            # --- Outside click detection (limited only to popup area) ---
            def handle_outside_click(event):
                if not self.cycle_popup or not self.cycle_popup.winfo_exists():
                    return
                px, py = popup.winfo_rootx(), popup.winfo_rooty()
                pw, ph = popup.winfo_width(), popup.winfo_height()
                # If click outside popup, close it
                if not (px <= event.x_root <= px + pw and py <= event.y_root <= py + ph):
                    close_cycle_popup()

            # Store the binding ID so we can unbind precisely
            self._popup_click_binding = self.bind_all("<Button-1>", handle_outside_click, add="+")

            # Close when mouse leaves the popup
            popup.bind("<Leave>", lambda e: close_cycle_popup())

        # === Build aligned grid ===
        for i, (icon, label, desc) in enumerate(controls, start=1):
            if icon:
                lbl_icon = tk.Label(card.body, image=icon, bg=Colors.dark_card)
                lbl_icon.image = icon
                lbl_icon.grid(row=i, column=0, sticky="w", padx=(6, 12), pady=3)

            label_frame = tk.Frame(card.body, bg=Colors.dark_card)
            label_frame.grid(row=i, column=1, sticky="w", padx=(0, 10), pady=3)

            tk.Label(
                label_frame,
                text=label,
                fg="white",
                bg=Colors.dark_card,
                font=("Segoe UI", 10, "bold")
            ).pack(side="left")

            if label == "Short Blink" and icons["info"]:
                info_icon = tk.Label(label_frame, image=icons["info"], bg=Colors.dark_card, cursor="hand2")
                info_icon.image = icons["info"]
                info_icon.pack(side="left", padx=(4, 0))

                # Hover or click both trigger popup
                info_icon.bind("<Enter>", lambda e, w=info_icon: show_cycle_popup(w))
                info_icon.bind("<Button-1>", lambda e, w=info_icon: show_cycle_popup(w))
                info_icon.bind("<Leave>", lambda e: close_cycle_popup())

            tk.Label(
                card.body,
                text=desc,
                fg="#d1d5db",
                bg=Colors.dark_card,
                font=("Segoe UI", 10),
                anchor="w",
                justify="left",
                wraplength=420
            ).grid(row=i, column=2, sticky="w", padx=(0, 10), pady=3)

        # Perfect alignment
        card.body.grid_columnconfigure(0, minsize=40)
        card.body.grid_columnconfigure(1, minsize=140)
        card.body.grid_columnconfigure(2, weight=1)

    # -----------------------------------------------------------------
    def update_gaze_button(self, running: bool):
        """Update START/STOP button state, sync with InstructionTray, and handle tray visibility."""
        self.app_running = running

        try:
            base_dir = Path(__file__).resolve().parents[2]
            config_path = base_dir / "Data" / "configuration.json"
            auto_open_instruction = False
            control_mode = "auto"

            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    auto_open_instruction = config.get("tray", {}).get("auto_open_instruction", False)
                    control_mode = config.get("control", {}).get("mode", "auto")

        except Exception as e:
            print(f"[WARN] Could not read configuration: {e}")
            auto_open_instruction = False
            control_mode = "auto"

        # === Update Main Button ===
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

        # Redraw button
        self.start_btn.delete("all")
        self.start_btn._draw_button()

        # === Start or Stop Gaze System based on control mode ===
        if running:
            print(f"[INFO] Application started. Control mode = {control_mode}")
            from frontend.pages.home import launch_gaze_app

            if control_mode == "auto":
                # Auto mode → Start gaze + mouse immediately
                launch_gaze_app(enable_mouse_control=True)
            else:
                # Manual mode → Do NOT start gaze at all, wait for voice command
                print("[INFO] Manual Control Mode active — system loaded, awaiting 'Start gaze control' voice command.")
                # Ensure any previous gaze session is stopped
                launch_gaze_app(enable_mouse_control=False)

        else:
            # Stop the system
            from frontend.pages.home import launch_gaze_app
            launch_gaze_app(enable_mouse_control=False)
            print("[INFO] Application stopped.")

        # === Sync Instruction Tray ===
        try:
            if not hasattr(self, "instruction_tray") or not self.instruction_tray.winfo_exists():
                self.instruction_tray = InstructionTray(self.controller)
                self.instruction_tray.withdraw()
                print("[INFO] Instruction Tray created.")

            tray = self.instruction_tray

            if running:
                tray.app_running = True
                tray.start_button.configure(image=tray.stop_icon)
                tray.start_label.configure(text="Stop Application")

                if auto_open_instruction:
                    tray.deiconify()
            else:
                tray.app_running = False
                tray.start_button.configure(image=tray.start_icon)
                tray.start_label.configure(text="Start Application")
                tray.withdraw()

        except Exception as e:
            print(f"[WARN] Could not sync Instruction Tray: {e}")
