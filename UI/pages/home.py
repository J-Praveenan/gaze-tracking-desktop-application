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
SIDEBAR_X, SIDEBAR_REL = 0.045, 0.55
MAIN_W = 0.70
MAIN_RELX = SIDEBAR_X + SIDEBAR_W + (1 - (SIDEBAR_X + SIDEBAR_W)) * 0.5
MAIN_RELH, MAIN_RELY = SIDEBAR_H, SIDEBAR_REL

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

        # sidebar / header icons
        self.logo_26 = load_img("CustomTkinter_logo_single.png", (26, 26))
        self.nav_home_20 = load_img("home_light.png", (20, 20))
        self.nav_chat_20 = load_img("chat_light.png", (20, 20))
        self.nav_user_20 = load_img("add_user_light.png", (20, 20))

        # main banner + button icon
        self.banner_500x150 = load_img("large_test_image.png", (500, 150))
        self.btn_icon_20 = load_img("image_icon_light.png", (20, 20))

        # ---------- SIDEBAR ----------
        self.sidebar = RoundedCard(self.overlay, radius=24, pad=0, bg=Colors.sidebar_bg, tight=False)
        self.sidebar.place(relx=SIDEBAR_X, rely=SIDEBAR_REL, anchor="w",
                           relwidth=SIDEBAR_W, relheight=SIDEBAR_H)
        self._build_sidebar(self.sidebar.body)

        # ---------- MAIN COLUMN (stack) ----------
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.place(relx=MAIN_RELX, rely=MAIN_RELY, anchor="center",
                            relwidth=MAIN_W, relheight=MAIN_RELH)

        # three frames like CTk example: home / set_up_gaze_tracking / frame_3
        self.frames = {
            "home": self._make_home_frame(self.main_col),
            "set_up_gaze_tracking": self._make_second_frame(self.main_col),
            "frame_3": self._make_third_frame(self.main_col),
        }
        for fr in self.frames.values():
            fr.place(relx=0, rely=0, relwidth=1, relheight=1)

        # default selection
        self.select_frame_by_name("home")

    # ======= Sidebar with icon buttons (CTk-like) =======
    def _build_sidebar(self, parent):
        parent.configure(bg=Colors.sidebar_bg)
        for w in parent.winfo_children():
            w.destroy()

        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)
        wrap.grid_rowconfigure(5, weight=1)

        # Header (logo + text)
        head = tk.Frame(wrap, bg=Colors.sidebar_bg)
        head.grid(row=0, column=0, sticky="ew", pady=(6, 12))
        if self.logo_26:
            tk.Label(head, image=self.logo_26, bg=Colors.sidebar_bg).pack(side="left", padx=(2, 8))
        tk.Label(head, text="Image Example", font=F("h2b", ("Segoe UI", 15, "bold")),
                 fg="#e6eef7", bg=Colors.sidebar_bg).pack(side="left")

        # Helper to create a "row" with border + the actual flat button inside
        def _nav_row(row_index, text, icon, cmd):
            # container with toggleable white border
            cont = tk.Frame(
                wrap, bg=Colors.sidebar_bg,
                highlightthickness=0,  # will be set to 2 on selection
                highlightbackground="#ffffff",
                highlightcolor="#ffffff",
                bd=0
            )
            cont.grid(row=row_index, column=0, sticky="ew", padx=2, pady=4)
            cont.grid_columnconfigure(0, weight=1)

            # the real button
            btn = tk.Button(
                cont, text=("  " + text), image=icon, compound="left", anchor="w",
                font=F("h3", ("Segoe UI", 12, "bold")),
                fg="#e6eef7", bg=Colors.sidebar_bg, bd=0, relief="flat",
                activebackground="#2b3947", activeforeground="#e6eef7",
                cursor="hand2"
            )
            # hover effect
            btn.bind("<Enter>", lambda e: btn.configure(bg="#2b3947"))
            btn.bind("<Leave>", lambda e: btn.configure(bg=Colors.sidebar_bg))
            btn.configure(command=cmd)
            btn.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
            return cont, btn

        # rows + buttons
        self._nav_rows = {}   # key -> container frame (so we can show border)
        self._nav_btns = {}   # key -> button (for bg highlight)

        r = 1
        row_home, self.btn_home = _nav_row(r, "Home", self.nav_home_20,
                                           lambda: self.select_frame_by_name("home"))
        self._nav_rows["home"] = row_home
        self._nav_btns["home"] = self.btn_home

        r += 1
        row_f2, self.btn_chat = _nav_row(r, "Set Up Gaze Tracking", self.nav_chat_20,
                                         lambda: self.select_frame_by_name("set_up_gaze_tracking"))
        self._nav_rows["set_up_gaze_tracking"] = row_f2
        self._nav_btns["set_up_gaze_tracking"] = self.btn_chat

        r += 1
        row_f3, self.btn_user = _nav_row(r, "Frame 3", self.nav_user_20,
                                         lambda: self.select_frame_by_name("frame_3"))
        self._nav_rows["frame_3"] = row_f3
        self._nav_btns["frame_3"] = self.btn_user

        # spacer
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=4, column=0, sticky="nsew")

        # Appearance dropdown (placeholder)
        dd_wrap = tk.Frame(wrap, bg=Colors.sidebar_bg)
        dd_wrap.grid(row=6, column=0, sticky="ew", pady=(12, 4))
        tk.Label(dd_wrap, text="Appearance", fg="#cfd8e3", bg=Colors.sidebar_bg,
                 font=F("body", ("Segoe UI", 10, "bold"))).pack(anchor="w", padx=2, pady=(0, 4))
        self.appearance = ttk.Combobox(dd_wrap, values=["Light", "Dark", "System"], state="readonly")
        self.appearance.current(2)
        self.appearance.pack(fill="x")
        self.appearance.bind("<<ComboboxSelected>>", self._on_appearance_change)

    # ======= Main frames (CTk-like content) =======
    def _make_home_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        # top banner card
        card = RoundedCard(fr, radius=18, pad=10, bg=Colors.glass_bg, tight=False)
        card.pack(fill="x", padx=8, pady=(0, 10))
        tk.Label(card.body, text="", image=self.banner_500x150 or "",
                 bg=Colors.glass_bg).pack(padx=10, pady=6)

        # button panel (like CTk example)
        panel = RoundedCard(fr, radius=18, pad=16, bg=Colors.glass_bg, tight=False)
        panel.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def _img_btn(text, compound="left", anchor="center"):
            return tk.Button(
                panel.body, text=text,
                image=self.btn_icon_20, compound=compound, anchor=anchor,
                font=F("h3", ("Segoe UI", 11, "bold")),
                fg=Colors.card_text, bg=Colors.dark_card, activebackground="#2f3e4c",
                activeforeground="#ffffff", bd=0, relief="flat", padx=12, pady=10, cursor="hand2"
            )

        b1 = _img_btn("", compound="left")
        b2 = _img_btn("CTkButton", compound="right")
        b3 = _img_btn("CTkButton", compound="top")
        b4 = _img_btn("CTkButton", compound="bottom", anchor="w")

        # grid like CTk example
        panel.body.grid_columnconfigure(0, weight=1)
        b1.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        b2.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        b3.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        b4.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        return fr

    def _make_second_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)
        card = RoundedCard(fr, radius=18, pad=18, bg=Colors.glass_bg, tight=False)
        card.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(card.body, text="Set Up Gaze Tracking", fg=Colors.card_head, bg=Colors.glass_bg,
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
        # border toggle
        for k, cont in self._nav_rows.items():
            cont.configure(highlightthickness=(2 if k == key else 0))
        # background toggle
        for k, btn in self._nav_btns.items():
            btn.configure(bg=("#3a4c60" if k == key else Colors.sidebar_bg))

    # ======= Frame switching like CTk example =======
    def select_frame_by_name(self, name: str):
        for key, fr in self.frames.items():
            if key == name:
                fr.lift()
            else:
                fr.lower()
        self._set_selected_nav(name)

    # ======= Appearance (placeholder hook) =======
    def _on_appearance_change(self, _evt=None):
        choice = self.appearance.get()
        # Hook your real theme switch here if you have one
        messagebox.showinfo("Appearance", f"Selected: {choice}")
