# UI/pages/settings.py
import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage
from .sidebar import Sidebar
import json
from pathlib import Path
from tkinter import ttk, messagebox


def F(name, default):
    return getattr(Fonts, name, default)


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
        self.enable_var = tk.BooleanVar(value=data.get("enabled", False))
        enable_chk = tk.Checkbutton(
            card.body,
            text="Enable reminder notifications",
            variable=self.enable_var,
            bg=Colors.glass_bg,
            fg=Colors.card_text,
            font=("Segoe UI", 12),
            activebackground=Colors.glass_bg,
            command=self._toggle_enable
        )
        enable_chk.grid(row=1, column=0, sticky="w", padx=10, pady=6, columnspan=3)

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

    # ----------------------------------------------------------------
    def _toggle_enable(self):
        """Enable or disable input fields based on toggle state."""
        state = "normal" if self.enable_var.get() else "disabled"
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
            "enabled": self.enable_var.get(),
            "duration": duration
        }

        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Saved", "Reminder settings saved successfully!")