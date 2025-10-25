# UI/pages/settings.py
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage
from .sidebar import Sidebar
from utils.system_tray import SystemTrayIcon


def F(name, default):
    return getattr(Fonts, name, default)


# ---------------------------------------------------------------------
# 🔘 Modern Toggle Switch Widget (Pure Tkinter)
# ---------------------------------------------------------------------
class ModernToggle(tk.Canvas):
    def __init__(self, parent, width=50, height=26, on_toggle=None, initial=False, **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=Colors.glass_bg, **kwargs)
        self.on_toggle = on_toggle
        self.state = tk.BooleanVar(value=initial)
        self.width = width
        self.height = height
        self.radius = height // 2
        self._draw_toggle()
        self.bind("<Button-1>", self._toggle)

    def _draw_toggle(self):
        self.delete("all")
        color_on = "#2563eb"
        color_off = "#9ca3af"

        if self.state.get():
            self.create_oval(0, 0, self.height, self.height, fill=color_on, outline=color_on)
            self.create_oval(self.width - self.height, 0, self.width, self.height, fill=color_on, outline=color_on)
            self.create_rectangle(self.radius, 0, self.width - self.radius, self.height,
                                  fill=color_on, outline=color_on)
            self.create_oval(self.width - self.height + 2, 2, self.width - 2, self.height - 2,
                             fill="white", outline="")
        else:
            self.create_oval(0, 0, self.height, self.height, fill=color_off, outline=color_off)
            self.create_oval(self.width - self.height, 0, self.width, self.height, fill=color_off, outline=color_off)
            self.create_rectangle(self.radius, 0, self.width - self.radius, self.height,
                                  fill=color_off, outline=color_off)
            self.create_oval(2, 2, self.height - 2, self.height - 2, fill="white", outline="")

    def _toggle(self, _=None):
        self.state.set(not self.state.get())
        self._draw_toggle()
        if self.on_toggle:
            self.on_toggle(self.state.get())

    def get(self):
        return self.state.get()

    def set(self, value: bool):
        self.state.set(value)
        self._draw_toggle()


# ---------------------------------------------------------------------
# ⚙️ Settings Page
# ---------------------------------------------------------------------
class SettingsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)
        self.config = self._load_config()

        # === Ensure full height expansion ===
        root = self.winfo_toplevel()
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)

        # === Match InfoPage grid ===
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)

        # === Main column ===
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        self.main_col.grid_rowconfigure(0, weight=1)
        self.main_col.grid_columnconfigure(0, weight=1)

        # === Rounded scrollable container ===
        container = RoundedCard(
            self.main_col,
            radius=18,
            pad=0,
            bg=Colors.page_bg,
            border_color="#4b5563",
            border_width=0,
            tight=False
        )
        container.grid(row=0, column=0, sticky="nsew")
        container.body.grid_rowconfigure(0, weight=1)
        container.body.grid_columnconfigure(0, weight=1)

        # === Scrollable canvas ===
        self.canvas = tk.Canvas(container.body, bg=Colors.page_bg, highlightthickness=0, bd=0)
        vscroll = ttk.Scrollbar(container.body, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vscroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")

        # === Frame inside canvas ===
        self.scroll_frame = tk.Frame(self.canvas, bg=Colors.page_bg)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_frame, width=e.width))
        self.enable_scroll(self.canvas, self.scroll_frame)


        # === Inner content ===
        content = tk.Frame(self.scroll_frame, bg=Colors.page_bg)
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # Small invisible top spacer (prevents visual jump)
        tk.Frame(content, height=5, bg=Colors.page_bg).pack(fill="x")

        # === Page title ===
        tk.Label(
            content,
            text="Settings",
            fg=Colors.card_head,
            bg=Colors.page_bg,
            font=F("h2b", ("Segoe UI", 16, "bold"))
        ).pack(anchor="w", pady=(0, 10))

        # === Sections ===
        self._build_reminder_settings(content)
        self._build_voice_settings(content)
        self._build_tray_settings(content)
        self._build_camera_settings(content)

        # 🔹 Reset scroll to top once everything is rendered
        self.after(200, lambda: self.canvas.yview_moveto(0))
        
        # --- Ensure tray mode is disabled on very first launch ---
        if not self.config_path.exists():
            self.config["tray"]["enabled"] = False
            self._save_config()
            if hasattr(self, "tray_toggle"):
                self.tray_toggle.set(False)


    # Mousewheel handler
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")


    # -----------------------------------------------------------------
    # Unified config load/save
    # -----------------------------------------------------------------
    def _load_config(self):
        """Load configuration.json or create with defaults."""
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "Data"
        data_dir.mkdir(exist_ok=True)
        self.config_path = data_dir / "configuration.json"

        default = {
            "reminder": {"enabled": False, "duration": 10},
            "voice": {"tips_enabled": True, "action_confirmation": True},
            "tray": {"enabled": False},
            "camera": {"index": 0}
        }

        # --- Load existing file ---
        if self.config_path.exists():
            try:
                with open(self.config_path, "r+") as f:
                    data = json.load(f)

                    # Merge defaults if any key missing
                    for key, value in default.items():
                        if key not in data:
                            data[key] = value

                    # 🧠 Force disable tray every startup (safety)
                    if data.get("tray", {}).get("enabled", False):
                        print("[INFO] Tray mode reset to disabled on startup.")
                        data["tray"]["enabled"] = False

                    # Save back (in case we modified)
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                    return data
            except Exception as e:
                print(f"[WARN] Failed to load config properly: {e}")

        # --- If missing or invalid, recreate ---
        with open(self.config_path, "w") as f:
            json.dump(default, f, indent=4)
        return default

    def _save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)


    def _save_auto_open(self, value: bool):
        """Persist the auto-open instruction bar setting."""
        self.config["tray"]["auto_open_instruction"] = value
        self._save_config()
        print(f"[INFO] Auto-open instruction tray: {'enabled' if value else 'disabled'}")

    # -----------------------------------------------------------------
    # Reminder Section
    # -----------------------------------------------------------------
    def _build_reminder_settings(self, parent):
        data = self.config.get("reminder", {"enabled": False, "duration": 10})

        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(card.body, text="Rest Reminder Notification",
                 fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 13, "bold"))
                 ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        # Toggle
        tk.Label(card.body, text="Enable reminder notifications:",
                 bg=Colors.glass_bg, fg=Colors.card_text, font=("Segoe UI", 12)
                 ).grid(row=1, column=0, sticky="w", padx=10, pady=6)

        self.toggle = ModernToggle(
            card.body, initial=data["enabled"],
            on_toggle=lambda _: self._toggle_enable()
        )
        self.toggle.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        # Duration
        tk.Label(card.body, text="Duration (minutes):",
                 bg=Colors.glass_bg, fg=Colors.card_text,
                 font=("Segoe UI", 12)
                 ).grid(row=2, column=0, sticky="w", padx=8, pady=4)

        self.duration_var = tk.StringVar(value=str(data["duration"]))
        options = ["10", "20", "30", "40", "50", "60"]
        self.dropdown = ttk.Combobox(card.body, textvariable=self.duration_var, values=options, width=10)
        self.dropdown.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        tk.Button(card.body, text="Save", bg="#31A0EB", fg="white",
                  font=("Segoe UI", 12, "bold"),
                  command=self._save_reminder
                  ).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 6))

        self._toggle_enable()

    def _toggle_enable(self):
        state = "normal" if self.toggle.get() else "disabled"
        self.dropdown.configure(state=state)

    def _save_reminder(self):
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Duration must be a positive number.")
            return

        self.config["reminder"] = {"enabled": self.toggle.get(), "duration": duration}
        self._save_config()
        messagebox.showinfo("Saved", "Reminder settings saved successfully!")

    # -----------------------------------------------------------------
    # Voice Section
    # -----------------------------------------------------------------
    def _build_voice_settings(self, parent):
        from utils import common

        data = self.config.get("voice", {"tips_enabled": True, "action_confirmation": True})

        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(card.body, text="Voice Preferences",
                 fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 13, "bold"))
                 ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        tk.Label(card.body, text="Voice Tips:", bg=Colors.glass_bg,
                 fg=Colors.card_text, font=("Segoe UI", 12)
                 ).grid(row=1, column=0, sticky="w", padx=10, pady=6)

        ModernToggle(card.body, initial=data["tips_enabled"],
                     on_toggle=lambda val: self._on_voice_tips_toggle(val)
                     ).grid(row=1, column=1, sticky="w", padx=10, pady=6)

        tk.Label(card.body, text="Voice Action Confirmation:", bg=Colors.glass_bg,
                 fg=Colors.card_text, font=("Segoe UI", 12)
                 ).grid(row=2, column=0, sticky="w", padx=10, pady=6)

        ModernToggle(card.body, initial=data["action_confirmation"],
                     on_toggle=lambda val: self._on_voice_confirm_toggle(val)
                     ).grid(row=2, column=1, sticky="w", padx=10, pady=6)

    def _on_voice_tips_toggle(self, val):
        from utils import common
        common.set_voice_tips(val)
        self.config["voice"]["tips_enabled"] = val
        self._save_config()
        common.speak_if_allowed(f"Voice tips {'enabled' if val else 'disabled'}.")

    def _on_voice_confirm_toggle(self, val):
        from utils import common
        common.set_voice_action_confirmation(val)
        self.config["voice"]["action_confirmation"] = val
        self._save_config()
        common.speak_action_confirmation(f"Voice confirmations {'enabled' if val else 'disabled'}.")

    # -----------------------------------------------------------------
    # Tray Section
    # -----------------------------------------------------------------
    def _build_tray_settings(self, parent):
        from utils.common import speak, speak_action_confirmation
        from UI.pages.instruction_tray import InstructionTray

        # Load tray config
        data = self.config.get("tray", {"enabled": False, "auto_open_instruction": True})
        card = RoundedCard(parent, radius=12, pad=12,
                        bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(card.body, text="Hide to Tray",
                fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 13, "bold"))
                ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        # Shared variables
        tray_var = tk.BooleanVar(value=data.get("enabled", False))
        auto_open_var = tk.BooleanVar(value=data.get("auto_open_instruction", True))

        # Reference to toggle
        self.tray_toggle = None

        def toggle_tray():
            """Handles enabling/disabling tray mode."""
            root_window = self.winfo_toplevel()
            self.config["tray"]["enabled"] = tray_var.get()
            self.config["tray"]["auto_open_instruction"] = auto_open_var.get()
            self._save_config()

            if tray_var.get():
                # --- Minimize & create tray icon ---
                root_window.withdraw()

                # 🔹 Auto open instruction tray if setting enabled
                if auto_open_var.get():
                    try:
                        tray = InstructionTray(root_window)
                        tray.after(200, lambda: tray.deiconify())
                        print("[INFO] Instruction Tray auto-opened when minimized.")
                    except Exception as e:
                        print(f"[WARN] Failed to auto-open InstructionTray: {e}")

                def restore():
                    """Triggered when user clicks 'Restore' in tray menu."""
                    root_window.deiconify()
                    root_window.focus_force()

                    # Disable tray mode when restored
                    tray_var.set(False)
                    self.config["tray"]["enabled"] = False
                    self._save_config()

                    # Update toggle visually
                    if self.tray_toggle:
                        self.tray_toggle.set(False)

                    speak("Application restored from tray.")

                def exit_app():
                    root_window.destroy()

                tray_icon = SystemTrayIcon(on_restore=restore, on_exit=exit_app)
                tray_icon.show()
                speak_action_confirmation("Application minimized to tray.")
            else:
                root_window.deiconify()
                speak("Application restored.")

        # Enable tray mode toggle
        tk.Label(card.body, text="Enable tray mode:", bg=Colors.glass_bg,
                fg=Colors.card_text, font=("Segoe UI", 12)
                ).grid(row=1, column=0, sticky="w", padx=10, pady=6)

        self.tray_toggle = ModernToggle(
            card.body,
            initial=tray_var.get(),
            on_toggle=lambda val: (tray_var.set(val), toggle_tray())
        )
        self.tray_toggle.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        # ✅ New checkbox for auto-open instruction bar
        tk.Checkbutton(
            card.body,
            text="Auto-open Instruction Bar when minimized / hided to tray",
            variable=auto_open_var,
            bg=Colors.glass_bg,
            fg=Colors.card_text,
            activebackground=Colors.glass_bg,
            font=("Segoe UI", 11),
            anchor="w",
            onvalue=True,
            offvalue=False,
            command=lambda: self._save_auto_open(auto_open_var.get())
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 2))

    # -----------------------------------------------------------------
    # Camera Section
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # Camera Section (User-Friendly)
    # -----------------------------------------------------------------
    def _build_camera_settings(self, parent):
        """Display camera options in human-friendly terms instead of numeric indexes."""
        data = self.config.get("camera", {"index": 0})

        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(card.body, text="Camera Configuration",
                 fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 13, "bold"))
                 ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        tk.Label(card.body, text="Select active camera:",
                 bg=Colors.glass_bg, fg=Colors.card_text,
                 font=("Segoe UI", 12)
                 ).grid(row=1, column=0, sticky="w", padx=10, pady=6)

        # User-friendly options
        self.camera_options = {
            "Default / Built-in Camera": 0,
            "External USB Camera": 1,
            "Virtual / Software Camera": 2,
            "Other (Advanced User)": 3
        }

        # Find text label that matches current index
        current_text = next(
            (name for name, idx in self.camera_options.items() if idx == data.get("index", 0)),
            "Default / Built-in Camera"
        )

        # Dropdown with readable text
        self.camera_var = tk.StringVar(value=current_text)
        dropdown = ttk.Combobox(
            card.body,
            textvariable=self.camera_var,
            values=list(self.camera_options.keys()),
            width=30,
            state="readonly"
        )
        dropdown.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        # Save button
        tk.Button(card.body, text="Save", bg="#2563eb", fg="white",
                  font=("Segoe UI", 12, "bold"),
                  command=self._save_camera_config
                  ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 6))

    def _save_camera_config(self):
        """Save selected camera in numeric format, based on user-friendly name."""
        try:
            selected_name = self.camera_var.get()
            index = self.camera_options.get(selected_name, 0)
        except Exception:
            messagebox.showerror("Invalid Input", "Please select a valid camera option.")
            return

        self.config["camera"]["index"] = index
        self._save_config()
        messagebox.showinfo("Saved", f"Camera preference '{selected_name}' saved successfully!")
