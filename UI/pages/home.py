# UI/pages/home.py (only the HomePage class replaced)
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from PIL import Image, ImageTk

from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage

def F(name, default):
    return getattr(Fonts, name, default)

SIDEBAR_W, SIDEBAR_H = 0.21, 0.86
SIDEBAR_X, SIDEBAR_REL = 0.045, 0.45
MAIN_W = 0.70
MAIN_RELX = SIDEBAR_X + SIDEBAR_W + (1 - (SIDEBAR_X + SIDEBAR_W)) * 0.5
MAIN_RELH, MAIN_RELY = 0.67, SIDEBAR_REL

ASSETS = Path(__file__).resolve().parents[2] / "Assets" / "test_images"

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # ---- image cache to avoid GC ----
        self._img = {}

        # ---- preload images (fallbacks if missing) ----
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

        # sidebar / header icons (replace names as needed)
        self.logo_26 = load_img("CustomTkinter_logo_single.png", (26, 26))
        self.nav_home_20 = load_img("home_light.png", (20, 20))
        self.nav_setup_20 = load_img("chat_light.png", (20, 20))       # placeholder
        self.nav_apps_20 = load_img("add_user_light.png", (20, 20))    # placeholder
        self.nav_system_20 = load_img("add_user_light.png", (20, 20))  # placeholder
        self.nav_tips_20 = load_img("add_user_light.png", (20, 20))    # placeholder
        self.nav_info_20 = load_img("add_user_light.png", (20, 20))    # placeholder
        self.nav_settings_20 = load_img("add_user_light.png", (20, 20))# placeholder

        # ---------- SIDEBAR ----------
        self.sidebar = RoundedCard(self.overlay, radius=18, pad=10, bg=Colors.dark_card, tight=False)
        # RoundedCard(self.overlay, radius=24, pad=0, bg=Colors.sidebar_bg, tight=False)
        self.sidebar.place(relx=SIDEBAR_X, rely=SIDEBAR_REL, anchor="w",
                           relwidth=SIDEBAR_W, relheight=SIDEBAR_H)
        self._nav_rows, self._nav_btns = {}, {}
        self._build_sidebar(self.sidebar.body)

        # ---------- MAIN COLUMN (stack) ----------
        # moved up slightly to reduce top spacing
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.place(relx=MAIN_RELX, rely=MAIN_RELY - 0.095, anchor="center",
                            relwidth=MAIN_W, relheight=MAIN_RELH)

        self.frames = {
            "home": self._make_home_frame(self.main_col),
            "frame_2": self._make_second_frame(self.main_col),
            "frame_3": self._make_third_frame(self.main_col),
        }
        for fr in self.frames.values():
            fr.place(relx=0, rely=0, relwidth=1, relheight=0.3)

        self._nav_to_frame = {
            "home": "home",
            "setup": "frame_2",
            "apps": "frame_3",
            "system": None,
            "tips": None,
            "info": None,
            "settings": None,
        }

        self.select_nav("home")

    # ======= Sidebar =======
    def _build_sidebar(self, parent):
        parent.configure(bg=Colors.sidebar_bg)
        for w in parent.winfo_children(): w.destroy()

        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)
        wrap.grid_rowconfigure(8, weight=1)

        head = tk.Frame(wrap, bg=Colors.sidebar_bg)
        head.grid(row=0, column=0, sticky="ew", pady=(6, 12))
        if self.logo_26:
            tk.Label(head, image=self.logo_26, bg=Colors.sidebar_bg).pack(side="left", padx=(2, 8))

        def _nav_row(row_index, key, text, icon, on_click):
            cont = tk.Frame(
                wrap, bg=Colors.sidebar_bg,
                highlightthickness=0,
                highlightbackground="#ffffff",
                highlightcolor="#ffffff",
                bd=0,
            )
            cont.grid(row=row_index, column=0, sticky="ew", padx=2, pady=6)

            btn = tk.Button(
                cont, text=("  " + text), image=icon, compound="left", anchor="w",
                font=F("h3", ("Segoe UI", 12, "bold")),
                fg="#e6eef7", bg=Colors.sidebar_bg, bd=0, relief="flat",
                activebackground="#2b3947", activeforeground="#e6eef7",
                cursor="hand2", command=on_click
            )
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

    # ======= Main: HOME =======
    def _make_home_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)

        # --- HERO (welcome) card like the screenshot ---
        hero = RoundedCard(fr, radius=18, pad=10, bg=Colors.dark_card, tight=False)
        hero.pack(fill="x", padx=8, pady=(2, 4))  # minimal top space

        title = tk.Label(
            hero.body,
            text="Welcome to LOOK TRACK VISION",
            fg="#ffffff", bg=Colors.dark_card,
            font=F("h1b", ("Segoe UI", 20, "bold"))
        )
        title.pack(pady=(2, 4))

        subtitle = tk.Label(
            hero.body,
            text=("A smart assistant that lets you control your computer with just your eyes and voice.\n"
                  "Whether you're browsing, chatting, or presenting, it's all hands-free, intuitive, and "
                  "empowering."),
            fg="#e8eef6", bg=Colors.dark_card,
            justify="center",
            font=F("body", ("Segoe UI", 10))
        )
        subtitle.pack(pady=(0, 0))

        # keep text nicely wrapped as card resizes
        def _wrap(e):
            # leave padding for rounded corners
            subtitle.configure(wraplength=max(150, int(e.width * 0.92)))
        hero.body.bind("<Configure>", _wrap)

        # --- MAIN PANEL (placeholder content below the hero) ---
        panel = RoundedCard(fr, radius=18, pad=16, bg=Colors.glass_bg, tight=False)
        panel.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # (you can replace these with your real controls; kept minimal)
        panel.body.grid_columnconfigure(0, weight=1)
        tk.Label(panel.body, text="Control Mode", fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))
        tk.Label(panel.body, text="(Auto / Manual controls go here)", fg=Colors.card_text,
                 bg=Colors.glass_bg, font=F("body", ("Segoe UI", 10))
                 ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 10))

        return fr

    def _make_second_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        card = RoundedCard(fr, radius=18, pad=18, bg=Colors.glass_bg, tight=False)
        card.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(card.body, text="Frame 2", fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 14, "bold"))).pack(anchor="w")
        tk.Label(card.body, text="(Your second frame content)",
                 fg=Colors.card_text, bg=Colors.glass_bg, font=F("body", ("Segoe UI", 11))
                 ).pack(anchor="w", pady=(6, 0))
        return fr

    def _make_third_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        card = RoundedCard(fr, radius=18, pad=18, bg=Colors.glass_bg, tight=False)
        card.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(card.body, text="Frame 3", fg=Colors.card_head, bg=Colors.glass_bg,
                 font=F("h2b", ("Segoe UI", 14, "bold"))).pack(anchor="w")
        tk.Label(card.body, text="(Your third frame content)",
                 fg=Colors.card_text, bg=Colors.glass_bg, font=F("body", ("Segoe UI", 11))
                 ).pack(anchor="w", pady=(6, 0))
        return fr

    # ======= selection visuals (bg + white border) =======
    def _set_selected_nav(self, key: str):
        for k, cont in self._nav_rows.items():
            cont.configure(highlightthickness=(2 if k == key else 0))
        for k, btn in self._nav_btns.items():
            btn.configure(bg=("#3a4c60" if k == key else Colors.sidebar_bg))

    # ======= Frame switching =======
    def _switch_frame(self, name: str):
        for k, fr in self.frames.items():
            fr.lift() if k == name else fr.lower()

    # ======= Unified selection from sidebar =======
    def select_nav(self, key: str):
        self._set_selected_nav(key)
        target = self._nav_to_frame.get(key)
        if target and target in self.frames:
            self._switch_frame(target)

    def select_frame_by_name(self, name: str):
        self._switch_frame(name)

    def _on_appearance_change(self, _evt=None):
        choice = self.appearance.get()
        messagebox.showinfo("Appearance", f"Selected: {choice}")
