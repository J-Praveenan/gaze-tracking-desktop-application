import tkinter as tk
from tkinter import messagebox
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage
from .sidebar import Sidebar


def F(name, default):
    return getattr(Fonts, name, default)


class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # Use grid for 2-column layout
        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)   # sidebar fixed
        self.overlay.grid_columnconfigure(1, weight=1)   # content expand

        # Sidebar (left)
        Sidebar(self.overlay, controller).grid(
            row=0, column=0, sticky="nsw", padx=(20, 10), pady=20
        )

        # Main content (right)
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        self._build_home_content(self.main_col)

    def _build_home_content(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        fr.pack(fill="both", expand=True)

        # === Hero ===
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

        # === Scrollable Area ===
        canvas = tk.Canvas(fr, bg=Colors.page_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(fr, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.page_bg)

        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))

        canvas.pack(fill="both", expand=True, side="left")
        scrollbar.pack(side="right", fill="y")

        # reuse your control cards, voice tips, tray, instructions, start btn...
        self._make_card(scroll_frame, "Control Mode",
                        "Select how you want to control apps using your gaze – automatic or manual.",
                        [("Auto Control", "auto"), ("Manual Control", "manual")])
        

        # === Voice Tips ===
        self._make_card(scroll_frame, "Voice Tips",
                        "Turn voice tips ON or OFF while using gaze control.",
                        [("Turn ON", "on"), ("Turn OFF", "off")],
                        radio_var=tk.StringVar(value="on"))

        # === Hide to Tray ===
        self._make_checkbox_card(scroll_frame)

        # === Instructions ===
        self._make_instruction_section(scroll_frame, "Eye & Blink Controls", [
            ("👀", "Eye Movement", "Pointer moves where you look"),
            ("🎯", "App Open", "Pointer starts at the center"),
            ("✨", "Both Eyes Blink", "Cycle pointer: Left → Top → Right → Bottom → Center"),
            ("👁️", "Left Eye Blink", "Left Click"),
            ("👁️", "Right Eye Blink", "Right Click"),
        ])
        self._make_instruction_section(scroll_frame, "Typing & Voice", [
            ("🎤", "Typing Field", "Voice prompt: 'Speak to type the text'"),
            ("⌨️", "Virtual Keyboard", "AI suggests words while typing"),
        ])
        self._make_instruction_section(scroll_frame, "Health & Rest", [
            ("⏱️", "Screen Time", "Tracks usage time"),
            ("⚠️", "Rest Reminder", "Popup: 'Please rest your eyes' after set time"),
            ("⚙️", "Custom Duration", "Choose when and where reminders appear"),
        ])
        self._make_instruction_section(scroll_frame, "Interface", [
            ("➡️", "Sidebar Arrow", "Right-center arrow → open instructions"),
        ])

        # === Start Button ===
        start_btn = PillButton(
            scroll_frame, text="START APPLICATION",
            command=lambda: messagebox.showinfo("Start", "Application started!")
        )
        start_btn.pack(anchor="e", pady=(16, 6), padx=8)

        # Spacer
        tk.Frame(scroll_frame, height=40, bg=Colors.page_bg).pack(fill="x")

    # ---------------- Reusable Helpers ----------------
    def _make_card(self, parent, title, desc, options, radio_var=None):
        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=6, padx=8)

        tk.Label(card.body, text=title,
                 fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))
        tk.Label(card.body, text=desc,
                 fg=Colors.card_text, bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 10))
                 ).grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        var = radio_var or tk.StringVar(value=options[0][1])
        for i, (label, value) in enumerate(options):
            tk.Radiobutton(card.body, text=label, variable=var, value=value,
                           bg=Colors.glass_bg, anchor="w").grid(row=2, column=i, sticky="w", padx=16, pady=(0, 10))

    def _make_checkbox_card(self, parent):
        card = RoundedCard(parent, radius=12, pad=12,
                           bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        card.pack(fill="x", pady=6, padx=8)

        tray_var = tk.BooleanVar(value=False)

        def toggle_tick():
            tray_toggle.config(text="✔" if tray_var.get() else "")

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
            tk.Label(card.body, text=icon + " " + label,
                     fg="white", bg=Colors.dark_card,
                     font=F("body", ("Segoe UI", 10, "bold"))
                     ).grid(row=i, column=0, sticky="w", padx=6, pady=2)
            tk.Label(card.body, text=desc,
                     fg="#d1d5db", bg=Colors.dark_card,
                     font=F("body", ("Segoe UI", 10))
                     ).grid(row=i, column=1, sticky="w", padx=(6, 0), pady=2)
