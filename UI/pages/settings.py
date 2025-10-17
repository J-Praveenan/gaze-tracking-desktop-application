# UI/pages/settings.py
import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage
from .sidebar import Sidebar
import json
from pathlib import Path
from tkinter import ttk, messagebox
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
        self.circle_pos = self.width - self.height if self.state.get() else 2
        self._draw_toggle()
        self.bind("<Button-1>", self._toggle)

    def _draw_toggle(self):
        self.delete("all")
        if self.state.get():
            # Blue ON state
            self.create_oval(0, 0, self.height, self.height, fill="#2563eb", outline="#2563eb")
            self.create_oval(self.width - self.height, 0, self.width, self.height, fill="#2563eb", outline="#2563eb")
            self.create_rectangle(self.radius, 0, self.width - self.radius, self.height,
                                  fill="#2563eb", outline="#2563eb")
            # Circle (white)
            self.create_oval(self.width - self.height + 2, 2, self.width - 2, self.height - 2,
                             fill="white", outline="")
        else:
            # Gray OFF state
            self.create_oval(0, 0, self.height, self.height, fill="#9ca3af", outline="#9ca3af")
            self.create_oval(self.width - self.height, 0, self.width, self.height, fill="#9ca3af", outline="#9ca3af")
            self.create_rectangle(self.radius, 0, self.width - self.radius, self.height,
                                  fill="#9ca3af", outline="#9ca3af")
            self.create_oval(2, 2, self.height - 2, self.height - 2, fill="white", outline="")

    def _toggle(self, event=None):
        self.state.set(not self.state.get())
        self._draw_toggle()
        if self.on_toggle:
            self.on_toggle(self.state.get())

    def get(self):
        return self.state.get()

    def set(self, value: bool):
        self.state.set(value)
        self._draw_toggle()


class SettingsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Layout: sidebar left, content right
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)  # sidebar
        self.overlay.grid_columnconfigure(1, weight=1)  # content


        # Main content card
        self.main_col = RoundedCard(
            self.overlay,
            radius=18,
            pad=20,
            bg=Colors.glass_bg,
            border_color="#4b5563",
            border_width=2
        )
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 20))

        # Title
        tk.Label(
            self.main_col.body,
            text="Settings",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 16, "bold"))
        ).pack(anchor="w", pady=(0, 8))


        # Call new section
        self._build_reminder_settings(self.main_col.body)
        
    # ----------------------------------------------------------------
    def _build_reminder_settings(self, parent):
        # === File path ===
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "Data"
        data_dir.mkdir(exist_ok=True)
        self.data_path = data_dir / "notification_remainder_time.json"

        # === Load existing settings if file exists ===
        if self.data_path.exists():
            try:
                with open(self.data_path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {"enabled": False, "duration": 10}
        else:
            data = {"enabled": False, "duration": 10}

        # --- Section card ---
        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(
            card.body,
            text="Rest Reminder Notification",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 13, "bold"))
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        # === Toggle ===
        # === Toggle Switch ===
        tk.Label(
            card.body,
            text="Enable reminder notifications:",
            bg=Colors.glass_bg,
            fg=Colors.card_text,
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, sticky="w", padx=10, pady=6)

        self.toggle = ModernToggle(
            card.body,
            initial=data.get("enabled", False),
            on_toggle=lambda val: self._toggle_enable()
        )
        self.toggle.grid(row=1, column=1, sticky="w", padx=10, pady=6)
        self._build_voice_settings(self.main_col.body)
        self._build_tray_settings(self.main_col.body)


        # === Duration entry + dropdown ===
        tk.Label(card.body, text="Duration (minutes):", bg=Colors.glass_bg,font=("Segoe UI", 12),
                 fg=Colors.card_text).grid(row=2, column=0, sticky="w", padx=8, pady=4)

        self.duration_var = tk.StringVar(value=str(data.get("duration", 10)))

        # Dropdown (predefined durations)
        options = ["10", "20", "30", "40", "50", "60"]
        self.dropdown = ttk.Combobox(card.body, textvariable=self.duration_var, values=options, width=10)
        self.dropdown.grid(row=2, column=1, sticky="w", padx=8, pady=4)


        # === Save button ===
        save_btn = tk.Button(
            card.body,
            text="Save",
            bg="#2563eb", fg="white",
            font=("Segoe UI", 12, "bold"),
            command=self._save_settings
        )
        save_btn.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 6))

        # Initial toggle state
        self._toggle_enable()


    def _build_voice_settings(self, parent):
        from utils import common

        card = RoundedCard(parent, radius=12, pad=12,
                        bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(
            card.body,
            text="Voice Preferences",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 13, "bold"))
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        # --- Voice Tips Toggle ---
        tk.Label(card.body, text="Voice Tips:", bg=Colors.glass_bg,
                fg=Colors.card_text, font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=6)
        voice_tips_toggle = ModernToggle(
            card.body,
            initial=common.voice_tips_enabled,
            on_toggle=lambda val: self._on_voice_tips_toggle(val)
        )
        voice_tips_toggle.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        # --- Voice Action Confirmation Toggle ---
        tk.Label(card.body, text="Voice Action Confirmation:", bg=Colors.glass_bg,
                fg=Colors.card_text, font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=6)
        voice_confirm_toggle = ModernToggle(
            card.body,
            initial=common.voice_action_confirmation,
            on_toggle=lambda val: self._on_voice_confirm_toggle(val)
        )
        voice_confirm_toggle.grid(row=2, column=1, sticky="w", padx=10, pady=6)


    def _on_voice_tips_toggle(self, val):
        from utils import common
        common.set_voice_tips(val)
        state = "enabled" if val else "disabled"
        common.speak_if_allowed(f"Voice tips {state}.")

    def _on_voice_confirm_toggle(self, val):
        from utils import common
        common.set_voice_action_confirmation(val)
        state = "enabled" if val else "disabled"
        common.speak_action_confirmation(f"Voice action confirmations {state}.")


    def _build_tray_settings(self, parent):
        from utils.common import speak, speak_action_confirmation

        card = RoundedCard(parent, radius=12, pad=12,
                        bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=8)

        tk.Label(
            card.body,
            text="Hide to Tray",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 13, "bold"))
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        tray_var = tk.BooleanVar(value=False)

        def toggle_tick():
            root_window = self.winfo_toplevel()

            if tray_var.get():
                # Minimize & create tray icon
                root_window.withdraw()  # hide completely from taskbar

                def restore():
                    root_window.deiconify()
                    root_window.focus_force()

                def exit_app():
                    root_window.destroy()

                tray = SystemTrayIcon(on_restore=restore, on_exit=exit_app)
                tray.show()
                speak_action_confirmation("Application minimized to tray.")
            else:
                root_window.deiconify()
                speak("Application restored.")


        tk.Label(card.body, text="Enable tray mode:", bg=Colors.glass_bg,
                fg=Colors.card_text, font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=6)
        ModernToggle(card.body, initial=False, on_toggle=lambda val: (tray_var.set(val), toggle_tick())
                    ).grid(row=1, column=1, sticky="w", padx=10, pady=6)

    # ----------------------------------------------------------------
    def _toggle_enable(self):
        """Enable or disable input fields based on toggle state."""
        state = "normal" if self.toggle.get() else "disabled"
        self.dropdown.configure(state=state)

    # ----------------------------------------------------------------
    def _save_settings(self):
        """Save reminder settings to JSON file."""
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                messagebox.showerror("Invalid Input", "Duration must be a positive number.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for duration.")
            return

        data = {
            "enabled":  self.toggle.get(),
            "duration": duration
        }

        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Saved", "Reminder settings saved successfully!")