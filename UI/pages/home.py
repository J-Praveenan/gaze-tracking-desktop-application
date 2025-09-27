import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageTk

from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage


def F(name, default):
    return getattr(Fonts, name, default)


# Layout ratios
SIDEBAR_W, SIDEBAR_H = 0.23, 0.86
SIDEBAR_X, SIDEBAR_REL = 0.045, 0.45
MAIN_W, MAIN_RELH = 0.70, 1.0
MAIN_RELX = SIDEBAR_X + SIDEBAR_W + (1 - (SIDEBAR_X + SIDEBAR_W)) * 0.5
MAIN_RELY = 0.62

ASSETS = Path(__file__).resolve().parents[2] / "Assets" / "test_images"


class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)
        self._img = {}  # cache for images

        # preload images
        def load_img(name, size=None):
            p = ASSETS / name
            if not p.exists():
                return None
            im = Image.open(p)
            if size:
                im = im.resize(size, Image.LANCZOS)
            ph = ImageTk.PhotoImage(im)
            self._img[name] = ph
            return ph

        self.logo_26 = load_img("CustomTkinter_logo_single.png", (26, 26))
        self.nav_home_20 = load_img("home_light.png", (20, 20))
        self.nav_setup_20 = load_img("chat_light.png", (20, 20))
        self.nav_apps_20 = load_img("add_user_light.png", (20, 20))
        self.nav_system_20 = load_img("add_user_light.png", (20, 20))
        self.nav_tips_20 = load_img("add_user_light.png", (20, 20))
        self.nav_info_20 = load_img("add_user_light.png", (20, 20))
        self.nav_settings_20 = load_img("add_user_light.png", (20, 20))

        # Sidebar
        self.sidebar = RoundedCard(
            self.overlay, radius=18, pad=10, bg=Colors.dark_card, tight=False
        )
        self.sidebar.place(
            relx=SIDEBAR_X, rely=SIDEBAR_REL,
            anchor="w", relwidth=SIDEBAR_W, relheight=SIDEBAR_H
        )
        self._nav_rows, self._nav_btns = {}, {}
        self._build_sidebar(self.sidebar.body)

        # Main column
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.place(
            relx=MAIN_RELX, rely=MAIN_RELY - 0.095,
            anchor="center", relwidth=MAIN_W, relheight=MAIN_RELH
        )

        # Pages container
        self.content = tk.Frame(self.main_col, bg=Colors.page_bg)
        self.content.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.frames = {
            "home": self._make_home_frame(self.content),
            "setup": self._make_second_frame(self.content),
            "apps": self._make_third_frame(self.content),
            "system": self._make_third_frame(self.content),
            "tips": self._make_third_frame(self.content),
            "info": self._make_third_frame(self.content),
            "settings": self._make_third_frame(self.content),
        }
        for fr in self.frames.values():
            fr.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._nav_to_frame = {
            "home": "home",
            "setup": "setup",
            "apps": "apps",
            "system": "system",
            "tips": "tips",
            "info": "info",
            "settings": "settings",
        }

        self.select_nav("home")

    # ===== Sidebar =====
    def _build_sidebar(self, parent):
        parent.configure(bg=Colors.sidebar_bg)
        for w in parent.winfo_children():
            w.destroy()

        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)
        wrap.grid_rowconfigure(8, weight=1)

        head = tk.Frame(wrap, bg=Colors.sidebar_bg)
        head.grid(row=0, column=0, sticky="ew", pady=(6, 12))
        if self.logo_26:
            tk.Label(head, image=self.logo_26, bg=Colors.sidebar_bg).pack(side="left", padx=(2, 8))

        def _nav_row(row_index, key, text, icon, on_click):
            cont = tk.Frame(wrap, bg=Colors.sidebar_bg, highlightthickness=0, bd=0)
            cont.grid(row=row_index, column=0, sticky="ew", padx=2, pady=6)

            btn = tk.Button(
                cont, text=("  " + text), image=icon, compound="left", anchor="w",
                font=F("h3", ("Segoe UI", 12, "bold")),
                fg="white", bg=Colors.sidebar_bg, bd=0, relief="flat",
                activebackground="#1d4ed8", activeforeground="white",
                cursor="hand2", command=on_click
            )
            btn.configure(padx=12, pady=8)
            btn.bind("<Enter>", lambda e: btn.configure(bg="#2b3947"))
            btn.bind("<Leave>", lambda e: btn.configure(bg=Colors.sidebar_bg))
            btn.pack(fill="x", padx=6, pady=6)

            self._nav_rows[key] = cont
            self._nav_btns[key] = btn

        r = 1
        _nav_row(r, "home", "Home", self.nav_home_20, lambda: self.select_nav("home")); r += 1
        _nav_row(r, "setup", "Set Up Gaze Tracking", self.nav_setup_20, lambda: self.select_nav("setup")); r += 1
        _nav_row(r, "apps", "Apps Control", self.nav_apps_20, lambda: self.select_nav("apps")); r += 1
        _nav_row(r, "system", "System Control", self.nav_system_20, lambda: self.select_nav("system")); r += 1
        _nav_row(r, "tips", "Tips", self.nav_tips_20, lambda: self.select_nav("tips")); r += 1
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=r, column=0, sticky="nsew"); r += 1
        _nav_row(r, "info", "Information", self.nav_info_20, lambda: self.select_nav("info")); r += 1
        _nav_row(r, "settings", "Settings", self.nav_settings_20, lambda: self.select_nav("settings")); r += 1

    # ===== Frames =====
    def _make_home_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)

        # === FIXED HERO (not scrollable) ===
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
        hero.body.bind("<Configure>", lambda e: subtitle.configure(wraplength=max(150, int(e.width * 0.92))))

        # === SCROLLABLE AREA (everything below Hero) ===
        canvas = tk.Canvas(fr, bg=Colors.page_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(fr, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.page_bg)

        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_frame_resize(event):
            canvas.itemconfig(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", _on_frame_resize)

        canvas.pack(fill="both", expand=True, side="left")
        scrollbar.pack(side="right", fill="y")

        # === CONTROL MODE CARD ===
        control_card = RoundedCard(scroll_frame, radius=12, pad=12,
                                bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        control_card.pack(fill="x", pady=6, padx=8)

        tk.Label(control_card.body, text="Control Mode",
                fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))
        tk.Label(control_card.body, text="Select how you want to control apps using your gaze – automatic or manual.",
                fg=Colors.card_text, bg=Colors.glass_bg,
                font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        auto_var = tk.StringVar(value="auto")
        tk.Radiobutton(control_card.body, text="Auto Control", variable=auto_var, value="auto",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))
        tk.Radiobutton(control_card.body, text="Manual Control", variable=auto_var, value="manual",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=1, sticky="w", padx=16, pady=(0, 10))

        # === VOICE TIPS CARD ===
        voice_card = RoundedCard(scroll_frame, radius=12, pad=12,
                                bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        voice_card.pack(fill="x", pady=6, padx=8)

        tk.Label(voice_card.body, text="Voice Tips",
                fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        tk.Label(voice_card.body, text="Turn voice tips ON or OFF while using gaze control.",
                fg=Colors.card_text, bg=Colors.glass_bg,
                font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        voice_var = tk.StringVar(value="on")
        tk.Radiobutton(voice_card.body, text="Turn ON", variable=voice_var, value="on",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))
        tk.Radiobutton(voice_card.body, text="Turn OFF", variable=voice_var, value="off",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=1, sticky="w", padx=16, pady=(0, 10))

        # === HIDE TO TRAY CARD ===
        tray_card = RoundedCard(
            scroll_frame, radius=12, pad=12,
            bg=Colors.glass_bg, border_color="#4b5563", border_width=2
        )
        tray_card.pack(fill="x", pady=6, padx=8)

        tray_var = tk.BooleanVar(value=False)

        def toggle_tick():
            tray_toggle.config(text="✔" if tray_var.get() else "")

        tk.Label(
            tray_card.body, text="Hide to tray",
            fg=Colors.card_head, bg=Colors.glass_bg,
            font=F("h2b", ("Segoe UI", 12, "bold"))
        ).grid(row=0, column=0, sticky="w")

        tray_toggle = tk.Checkbutton(
            tray_card.body, variable=tray_var, indicatoron=False,
            text="", width=2, height=1, command=toggle_tick,
            bg="white", fg=Colors.glass_bg, font=("Segoe UI", 10, "bold")
        )
        tray_toggle.grid(row=0, column=1, sticky="e", padx=(8, 0))

        tk.Label(
            tray_card.body,
            text="When enabled, the app will minimize and continue running in the background.",
            fg=Colors.card_text, bg=Colors.glass_bg,
            font=F("body", ("Segoe UI", 9)),
            wraplength=400, justify="left"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        toggle_tick()


        # === SHORTCUTS LEGEND ===
        def make_instruction_section(parent, title, entries):
            card = RoundedCard(
            parent, radius=12, pad=12,
            bg=Colors.dark_card, border_color=Colors.dark_card, border_width=0
        )
            card.pack(fill="x", pady=8, padx=8)

            # Section Title
            tk.Label(
                card.body, text=title,
                fg="white", bg=Colors.dark_card,
                font=F("h2b", ("Segoe UI", 12, "bold"))
            ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8), columnspan=2)

            # Entries (with emoji icons)
            for i, (icon, label, desc) in enumerate(entries, start=1):
                tk.Label(
                    card.body, text=icon + " " + label,
                    fg="white", bg=Colors.dark_card,
                    font=F("body", ("Segoe UI", 10, "bold"))
                ).grid(row=i, column=0, sticky="w", padx=6, pady=2)

                tk.Label(
                    card.body, text=desc,
                    fg="#d1d5db", bg=Colors.dark_card,
                    font=F("body", ("Segoe UI", 10))
                ).grid(row=i, column=1, sticky="w", padx=(6, 0), pady=2)



        # === Eye & Blink Controls ===
        make_instruction_section(scroll_frame, "Eye & Blink Controls", [
            ("👀", "Eye Movement", "Pointer moves where you look"),
            ("🎯", "App Open", "Pointer starts at the center"),
            ("✨", "Both Eyes Blink", "Cycle pointer: Left → Top → Right → Bottom → Center"),
            ("👁️", "Left Eye Blink", "Left Click"),
            ("👁️", "Right Eye Blink", "Right Click"),
        ])

        # === Typing & Voice ===
        make_instruction_section(scroll_frame, "Typing & Voice", [
            ("🎤", "Typing Field", "Voice prompt: 'Speak to type the text'"),
            ("⌨️", "Virtual Keyboard", "AI suggests words while typing"),
        ])

        # === Health & Rest ===
        make_instruction_section(scroll_frame, "Health & Rest", [
            ("⏱️", "Screen Time", "Tracks usage time"),
            ("⚠️", "Rest Reminder", "Popup: 'Please rest your eyes' after set time"),
            ("⚙️", "Custom Duration", "Choose when and where reminders appear"),
        ])

        # === Interface ===
        make_instruction_section(scroll_frame, "Interface", [
            ("➡️", "Sidebar Arrow", "Right-center arrow → open instructions"),
        ])


        # === START BUTTON ===
        start_btn = PillButton(
            scroll_frame, text="START APPLICATION",
            command=lambda: messagebox.showinfo("Start", "Application started!")
        )
        start_btn.pack(anchor="e", pady=(16, 6), padx=8)

        # Spacer
        tk.Frame(scroll_frame, height=40, bg=Colors.page_bg).pack(fill="x")


        return fr

    def _make_second_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        card = RoundedCard(fr, radius=18, pad=18, bg=Colors.glass_bg)
        card.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(card.body, text="Frame 2", fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 14, "bold"))).pack(anchor="w")
        tk.Label(card.body, text="(Your second frame content)",
                 fg=Colors.card_text, bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 11))).pack(anchor="w", pady=(6, 0))
        return fr

    def _make_third_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        card = RoundedCard(fr, radius=18, pad=18, bg=Colors.glass_bg)
        card.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(card.body, text="Frame 3", fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 14, "bold"))).pack(anchor="w")
        tk.Label(card.body, text="(Your third frame content)",
                 fg=Colors.card_text, bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 11))).pack(anchor="w", pady=(6, 0))
        return fr

    # ===== Navigation =====
    def _set_selected_nav(self, key: str):
        for k, cont in self._nav_rows.items():
            cont.configure(highlightthickness=(2 if k == key else 0))
        for k, btn in self._nav_btns.items():
            btn.configure(bg=("#3a4c60" if k == key else Colors.sidebar_bg))

    def _switch_frame(self, name: str):
        for k, fr in self.frames.items():
            fr.lift() if k == name else fr.lower()

    def select_nav(self, key: str):
        self._set_selected_nav(key)
        target = self._nav_to_frame.get(key)
        if target in self.frames:
            self._switch_frame(target)

    def select_frame_by_name(self, name: str):
        self._switch_frame(name)
