import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from .base import BasePage
from .sidebar import Sidebar


def F(name, default):
    return getattr(Fonts, name, default)


class InfoPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # === Grid layout for sidebar + main content ===
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)


        # === Main content frame (fills remaining width) ===
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 20))
        self.main_col.grid_rowconfigure(0, weight=1)
        self.main_col.grid_columnconfigure(0, weight=1)

        # === Rounded Card (fills entire space) ===
        self.card = RoundedCard(
            self.main_col,
            radius=18,
            pad=20,
            bg=Colors.glass_bg,
            border_color="#4b5563",
            border_width=2,
            tight=False   # ensures card fills height
        )
        self.card.grid(row=0, column=0, sticky="nsew")

        # === Configure card body grid ===
        self.card.body.grid_rowconfigure(1, weight=1)
        self.card.body.grid_columnconfigure(0, weight=1)

        # === Title ===
        tk.Label(
            self.card.body,
            text="Information & Features",
            fg=Colors.card_head,
            bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 16, "bold"))
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # === Scrollable Area ===
        canvas = tk.Canvas(self.card.body, bg=Colors.glass_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.card.body, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.glass_bg)

        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # --- Dynamic scroll area resizing ---
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        scroll_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        # --- Mouse wheel scroll support ---
        def _on_mousewheel(event):
            # Smoother scrolling speed (120 = standard delta unit)
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Bind when mouse enters scroll area
        def _bind_scroll(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # For Linux
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Unbind when mouse leaves
        def _unbind_scroll(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        scroll_frame.bind("<Enter>", _bind_scroll)
        scroll_frame.bind("<Leave>", _unbind_scroll)

        # === Content sections ===
        self._make_instruction_section(scroll_frame, "Typing & Voice", [
            ("🎤", "Typing Field", "Voice prompt: 'Speak to type the text'"),
            ("⌨️", "Virtual Keyboard", "AI suggests words while typing"),
            ("🗣️", "Voice Dictation", "Type with speech-to-text using your microphone"),
            ("🔊", "Voice Feedback", "Get spoken tips and alerts while using gaze control"),
        ])

        self._make_instruction_section(scroll_frame, "Health & Rest", [
            ("⏱️", "Screen Time", "Tracks your eye usage duration automatically"),
            ("⚠️", "Rest Reminder", "Popup reminder to rest your eyes after long sessions"),
            ("⚙️", "Custom Duration", "Choose your preferred rest interval in settings"),
            ("🧘", "Relax Mode", "Temporarily disable gaze tracking to relax your eyes"),
        ])

        self._make_instruction_section(scroll_frame, "Interface", [
            ("➡️", "Sidebar Navigation", "Switch between pages using the left sidebar"),
            ("🪟", "Hide to Tray", "Minimize the app while keeping it running in background"),
            ("💡", "Dark / Light Mode", "Adaptive theme based on system settings"),
            ("📘", "Help & Tips", "Access quick guidance and troubleshooting info"),
        ])

        # Spacer at bottom
        tk.Frame(scroll_frame, height=40, bg=Colors.glass_bg).pack(fill="x")

    # ---------------- Helper ----------------
    def _make_instruction_section(self, parent, title, entries):
        card = RoundedCard(
            parent,
            radius=12,
            pad=12,
            bg=Colors.dark_card,
            border_color=Colors.dark_card,
            border_width=0
        )
        card.pack(fill="x", pady=8, padx=8)

        tk.Label(
            card.body,
            text=title,
            fg="white",
            bg=Colors.dark_card,
            font=F("h2b", ("Segoe UI", 12, "bold"))
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

        for i, (icon, label, desc) in enumerate(entries, start=1):
            tk.Label(
                card.body,
                text=f"{icon} {label}",
                fg="white",
                bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10, "bold"))
            ).grid(row=i, column=0, sticky="w", padx=6, pady=2)
            tk.Label(
                card.body,
                text=desc,
                fg="#d1d5db",
                bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10))
            ).grid(row=i, column=1, sticky="w", padx=(6, 0), pady=2)
