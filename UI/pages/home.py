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

SIDEBAR_W, SIDEBAR_H = 0.23, 0.86
SIDEBAR_X, SIDEBAR_REL = 0.045, 0.45
MAIN_W = 0.70
MAIN_RELX = SIDEBAR_X + SIDEBAR_W + (1 - (SIDEBAR_X + SIDEBAR_W)) * 0.5
MAIN_RELH = 1.0
MAIN_RELY = 0.63

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
        self.sidebar.place(relx=SIDEBAR_X, rely=SIDEBAR_REL, anchor="w",
                           relwidth=SIDEBAR_W, relheight=SIDEBAR_H)
        self._nav_rows, self._nav_btns = {}, {}
        self._build_sidebar(self.sidebar.body)

        # ---------- MAIN COLUMN (fixed area that hosts pages) ----------
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.place(relx=MAIN_RELX, rely=MAIN_RELY - 0.095, anchor="center",
                            relwidth=MAIN_W, relheight=MAIN_RELH)

        # container where all pages are stacked
        self.content = tk.Frame(self.main_col, bg=Colors.page_bg)
        self.content.place(relx=0, rely=0, relwidth=1, relheight=1)

        # create all pages ONCE and stack them in the same spot
        self.frames = {
            "home":   self._make_home_frame(self.content),
            "setup":  self._make_second_frame(self.content),
            "apps":   self._make_third_frame(self.content),
            "system":   self._make_third_frame(self.content),
            "tips":   self._make_third_frame(self.content),
            "info":   self._make_third_frame(self.content),
            "settings":   self._make_third_frame(self.content),
            # you can add real pages later: "system": SystemPage(self.content, controller), etc.
        }
        for fr in self.frames.values():
            fr.place(relx=0, rely=0, relwidth=1, relheight=1)  # full size & same position

        # map sidebar keys -> frame keys
        self._nav_to_frame = {
            "home": "home",
            "setup": "setup",
            "apps": "apps",
            "system": "system",    # placeholder until you build a System page
            "tips": "tips",
            "info": "info",
            "settings": "settings",
        }

        self.select_nav("home")

    # ======= Frame switching =======
    def _switch_frame(self, name: str):
        # tkraise shows one frame and keeps others underneath
        self.frames[name].tkraise()

    # ======= Unified selection from sidebar =======
    def select_nav(self, key: str):
        self._set_selected_nav(key)
        target = self._nav_to_frame.get(key)
        if target in self.frames:
            self._switch_frame(target)

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

    # ======= Main: HOME =======
        # ======= Main: HOME =======
    def _make_home_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)

        # --- HERO (welcome) card ---
        hero = RoundedCard(fr, radius=18, pad=20, bg=Colors.dark_card, tight=True)
        hero.pack(fill="x", padx=8, pady=(2, 4))

        title = tk.Label(
            hero.body,
            text="Welcome to LOOK TRACK VISION",
            fg="#ffffff", bg=Colors.dark_card,
            font=F("h1b", ("Segoe UI", 20, "bold"))
        )
        title.pack(pady=(2, 0))

        subtitle = tk.Label(
            hero.body,
            text=("A smart assistant that lets you control your computer with just your eyes and voice.\n"
                  "Whether you're browsing, chatting, or presenting, it's all hands-free, intuitive, and empowering."),
            fg="#e8eef6", bg=Colors.dark_card,
            justify="center",
            font=F("body", ("Segoe UI", 10))
        )
        subtitle.pack(pady=(0,4))
        subtitle.configure(wraplength=400)
        def _wrap(e):
            subtitle.configure(wraplength=max(150, int(e.width * 0.92)))
        hero.body.bind("<Configure>", _wrap)

        # --- MAIN PANEL ---
        panel = RoundedCard(fr, radius=18, pad=16, bg=Colors.glass_bg, tight=False)
        panel.pack(fill="both", expand=True, padx=8, pady=(8, 8))
        panel.body.grid_columnconfigure(0, weight=1)

        # ---- Control Mode ----
        control_card = RoundedCard(panel.body, radius=12, pad=12,
                        bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        control_card.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        control_card.body.grid_columnconfigure(0, weight=1)

        tk.Label(control_card.body, text="Control Mode", fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))

        tk.Label(control_card.body, text="Select how you want to control apps using your gaze – automatic or manual.",
                fg=Colors.card_text, bg=Colors.glass_bg, font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 8))

        auto_var = tk.StringVar(value="auto")
        tk.Radiobutton(control_card.body, text="Auto Control", variable=auto_var, value="auto",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=0, sticky="w", padx=16)
        tk.Radiobutton(control_card.body, text="Manual Control", variable=auto_var, value="manual",
                    bg=Colors.glass_bg, anchor="w").grid(row=3, column=0, sticky="w", padx=16, pady=(0, 10))

        # ---- Voice Tips ----
        voice_card = RoundedCard(panel.body, radius=12, pad=12,
                 bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        voice_card.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        voice_card.body.grid_columnconfigure(0, weight=1)

        tk.Label(voice_card.body, text="Voice Tips", fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(6, 6))

        tk.Label(voice_card.body, text="Turn voice tips ON or OFF while using gaze control.",
                fg=Colors.card_text, bg=Colors.glass_bg, font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 8))

        voice_var = tk.StringVar(value="on")
        tk.Radiobutton(voice_card.body, text="Turn ON", variable=voice_var, value="on",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=0, sticky="w", padx=16)
        tk.Radiobutton(voice_card.body, text="Turn OFF", variable=voice_var, value="off",
                    bg=Colors.glass_bg, anchor="w").grid(row=3, column=0, sticky="w", padx=16, pady=(0, 10))

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

SIDEBAR_W, SIDEBAR_H = 0.23, 0.86
SIDEBAR_X, SIDEBAR_REL = 0.045, 0.45
MAIN_W = 0.70
MAIN_RELX = SIDEBAR_X + SIDEBAR_W + (1 - (SIDEBAR_X + SIDEBAR_W)) * 0.5
MAIN_RELH = 1.0
MAIN_RELY = 0.62

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
        self.sidebar.place(relx=SIDEBAR_X, rely=SIDEBAR_REL, anchor="w",
                           relwidth=SIDEBAR_W, relheight=SIDEBAR_H)
        self._nav_rows, self._nav_btns = {}, {}
        self._build_sidebar(self.sidebar.body)

        # ---------- MAIN COLUMN (fixed area that hosts pages) ----------
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.place(relx=MAIN_RELX, rely=MAIN_RELY - 0.095, anchor="center",
                            relwidth=MAIN_W, relheight=MAIN_RELH)

        # container where all pages are stacked
        self.content = tk.Frame(self.main_col, bg=Colors.page_bg)
        self.content.place(relx=0, rely=0, relwidth=1, relheight=1)

        # create all pages ONCE and stack them in the same spot
        self.frames = {
            "home":   self._make_home_frame(self.content),
            "setup":  self._make_second_frame(self.content),
            "apps":   self._make_third_frame(self.content),
            "system":   self._make_third_frame(self.content),
            "tips":   self._make_third_frame(self.content),
            "info":   self._make_third_frame(self.content),
            "settings":   self._make_third_frame(self.content),
            # you can add real pages later: "system": SystemPage(self.content, controller), etc.
        }
        for fr in self.frames.values():
            fr.place(relx=0, rely=0, relwidth=1, relheight=1)  # full size & same position

        # map sidebar keys -> frame keys
        self._nav_to_frame = {
            "home": "home",
            "setup": "setup",
            "apps": "apps",
            "system": "system",    # placeholder until you build a System page
            "tips": "tips",
            "info": "info",
            "settings": "settings",
        }

        self.select_nav("home")

    # ======= Frame switching =======
    def _switch_frame(self, name: str):
        # tkraise shows one frame and keeps others underneath
        self.frames[name].tkraise()

    # ======= Unified selection from sidebar =======
    def select_nav(self, key: str):
        self._set_selected_nav(key)
        target = self._nav_to_frame.get(key)
        if target in self.frames:
            self._switch_frame(target)

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

    # ======= Main: HOME =======
    def _make_home_frame(self, parent):
        fr = tk.Frame(parent, bg=Colors.page_bg)

        # --- HERO (fixed, not scrollable) ---
        hero = RoundedCard(fr, radius=18, pad=20, bg=Colors.dark_card, tight=True)
        hero.pack(fill="x", padx=8, pady=(8, 4))

        title = tk.Label(
            hero.body,
            text="Welcome to LOOK TRACK VISION",
            fg="#ffffff", bg=Colors.dark_card,
            font=F("h1b", ("Segoe UI", 20, "bold"))
        )
        title.pack(pady=(2, 0))

        subtitle = tk.Label(
            hero.body,
            text=("A smart assistant that lets you control your computer with just your eyes and voice.\n"
                "Whether you're browsing, chatting, or presenting, it's all hands-free, intuitive, and empowering."),
            fg="#e8eef6", bg=Colors.dark_card,
            justify="center",
            font=F("body", ("Segoe UI", 10))
        )
        subtitle.pack(pady=(0, 4))
        subtitle.configure(wraplength=400)
        hero.body.bind("<Configure>", lambda e: subtitle.configure(wraplength=max(150, int(e.width * 0.92))))

        # === SCROLLABLE AREA (everything else) ===
        canvas = tk.Canvas(fr, bg=Colors.page_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(fr, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.page_bg)

        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_frame_resize(event):
            canvas.itemconfig(window_id, width=event.width)
            # Toggle scrollbar only if needed
            content_h = scroll_frame.winfo_reqheight()
            if content_h > canvas.winfo_height():
                canvas.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side="right", fill="y")
            else:
                canvas.configure(yscrollcommand=None)
                scrollbar.pack_forget()

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", _on_frame_resize)

        canvas.pack(fill="both", expand=True, side="left")
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # === CONTENT INSIDE scroll_frame ===

        # ---- Control Mode ----
        control_card = RoundedCard(scroll_frame, radius=12, pad=12,
                                bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        control_card.pack(fill="x", pady=6, padx=8)

        tk.Label(control_card.body, text="Control Mode", fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))
        tk.Label(control_card.body, text="Select how you want to control apps using your gaze – automatic or manual.",
                fg=Colors.card_text, bg=Colors.glass_bg, font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 8))

        auto_var = tk.StringVar(value="auto")
        tk.Radiobutton(control_card.body, text="Auto Control", variable=auto_var, value="auto",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=0, sticky="w", padx=16)
        tk.Radiobutton(control_card.body, text="Manual Control", variable=auto_var, value="manual",
                    bg=Colors.glass_bg, anchor="w").grid(row=3, column=0, sticky="w", padx=16, pady=(0, 10))

        # ---- Voice Tips ----
        voice_card = RoundedCard(scroll_frame, radius=12, pad=12,
                                bg=Colors.glass_bg, border_color="#4b5563", border_width=2)
        voice_card.pack(fill="x", pady=6, padx=8)

        tk.Label(voice_card.body, text="Voice Tips", fg=Colors.card_head, bg=Colors.glass_bg,
                font=F("h2b", ("Segoe UI", 12, "bold"))).grid(row=0, column=0, sticky="w", padx=6, pady=(6, 6))
        tk.Label(voice_card.body, text="Turn voice tips ON or OFF while using gaze control.",
                fg=Colors.card_text, bg=Colors.glass_bg, font=F("body", ("Segoe UI", 10))
                ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 8))

        voice_var = tk.StringVar(value="on")
        tk.Radiobutton(voice_card.body, text="Turn ON", variable=voice_var, value="on",
                    bg=Colors.glass_bg, anchor="w").grid(row=2, column=0, sticky="w", padx=16)
        tk.Radiobutton(voice_card.body, text="Turn OFF", variable=voice_var, value="off",
                    bg=Colors.glass_bg, anchor="w").grid(row=3, column=0, sticky="w", padx=16, pady=(0, 10))

        # ---- Hide to tray ----
        tray_card = RoundedCard(scroll_frame, radius=12, pad=12,
                                bg=Colors.dark_card, border_color=Colors.dark_card, border_width=0)
        tray_card.pack(fill="x", pady=6, padx=8)

        tray_card.body.grid_columnconfigure(0, weight=1)  # push label to left
        tray_card.body.grid_columnconfigure(1, weight=0)  # keep checkbox tight to right

        tray_var = tk.BooleanVar(value=False)
        def toggle_tick():
            tray_toggle.config(text="✔" if tray_var.get() else "")

        tk.Label(tray_card.body, text="Hide to tray",
                fg="white", bg=Colors.dark_card,
                font=F("h2b", ("Segoe UI", 12, "bold"))
                ).grid(row=0, column=0, sticky="w")

        tray_toggle = tk.Checkbutton(
            tray_card.body,
            variable=tray_var,
            onvalue=True,
            offvalue=False,
            indicatoron=False,
            text="",
            font=("Segoe UI", 10, "bold"),
            width=2, height=1,
            bg="white", fg=Colors.dark_card,
            activebackground="white",
            highlightthickness=1,
            highlightbackground="white",
            command=toggle_tick
        )
        tray_toggle.grid(row=0, column=1, sticky="e", padx=(8, 0))

        tk.Label(tray_card.body,
                text="When enabled, the app will minimize and continue running in the background.",
                fg="#d1d5db", bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 9)),
                wraplength=400, justify="left"
                ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        toggle_tick()


        # ---- Shortcuts Legend ----
        legend = tk.Frame(scroll_frame, bg=Colors.glass_bg)
        legend.pack(fill="x", pady=10, padx=8)

        entries = [
            ("Look Up  :", "Move to the option above", "red"),
            ("Look Down  :", "Move to the option below", "red"),
            ("Look Left  :", "Go to the previous section or tab", "orange"),
            ("Look Right :", "Go to the next section or tab", "orange"),
            ("Blink :", "Select / Toggle the highlighted option", "purple"),
        ]
        for i, (label, text, color) in enumerate(entries):
            tk.Label(legend, text=label, fg=color, bg=Colors.glass_bg,
                    font=F("body", ("Segoe UI", 9, "bold"))).grid(row=i, column=0, sticky="w")
            tk.Label(legend, text=text, fg=Colors.card_text, bg=Colors.glass_bg,
                    font=F("body", ("Segoe UI", 9))).grid(row=i, column=1, sticky="w", padx=(6, 0))

        # ---- Start Button ----
        start_btn = PillButton(scroll_frame, text="START APPLICATION",
                           command=lambda: messagebox.showinfo("Start", "Application started!"))
        start_btn.pack(anchor="e", pady=(16, 6), padx=8)

    # ---- Bottom Spacer (extra padding) ----
        tk.Frame(scroll_frame, height=40, bg=Colors.page_bg).pack(fill="x")

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
        # Spacer to add bottom padding in scroll area

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
    # def select_nav(self, key: str):
    #     self._set_selected_nav(key)
    #     target = self._nav_to_frame.get(key)
    #     if target and target in self.frames:
    #         self._switch_frame(target)

    def select_frame_by_name(self, name: str):
        self._switch_frame(name)

    def _on_appearance_change(self, _evt=None):
        choice = self.appearance.get()
        messagebox.showinfo("Appearance", f"Selected: {choice}")

        # ---- Shortcuts Legend ----
        legend = tk.Frame(panel.body, bg=Colors.glass_bg)
        legend.grid(row=10, column=0, sticky="ew", padx=6, pady=(12, 6))

        tk.Label(legend, text="Look Up  :", fg="red", bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 9, "bold"))).grid(row=0, column=0, sticky="w")
        tk.Label(legend, text="Move to the option above", fg=Colors.card_text,
                 bg=Colors.glass_bg, font=F("body", ("Segoe UI", 9))).grid(row=0, column=1, sticky="w", padx=(6, 0))

        tk.Label(legend, text="Look Down  :", fg="red", bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 9, "bold"))).grid(row=1, column=0, sticky="w")
        tk.Label(legend, text="Move to the option below", fg=Colors.card_text,
                 bg=Colors.glass_bg, font=F("body", ("Segoe UI", 9))).grid(row=1, column=1, sticky="w", padx=(6, 0))

        tk.Label(legend, text="Look Left  :", fg="orange", bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 9, "bold"))).grid(row=2, column=0, sticky="w")
        tk.Label(legend, text="Go to the previous section or tab", fg=Colors.card_text,
                 bg=Colors.glass_bg, font=F("body", ("Segoe UI", 9))).grid(row=2, column=1, sticky="w", padx=(6, 0))

        tk.Label(legend, text="Look Right :", fg="orange", bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 9, "bold"))).grid(row=3, column=0, sticky="w")
        tk.Label(legend, text="Go to the next section or tab", fg=Colors.card_text,
                 bg=Colors.glass_bg, font=F("body", ("Segoe UI", 9))).grid(row=3, column=1, sticky="w", padx=(6, 0))

        tk.Label(legend, text="Blink :", fg="purple", bg=Colors.glass_bg,
                 font=F("body", ("Segoe UI", 9, "bold"))).grid(row=4, column=0, sticky="w")
        tk.Label(legend, text="Select / Toggle the highlighted option", fg=Colors.card_text,
                 bg=Colors.glass_bg, font=F("body", ("Segoe UI", 9))).grid(row=4, column=1, sticky="w", padx=(6, 0))


        # ---- Start Button ----
        start_btn = PillButton(panel.body, text="START APPLICATION", command=lambda: messagebox.showinfo("Start", "Application started!"))
        start_btn.grid(row=9, column=0, pady=(16, 6), sticky="e")

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
    # def select_nav(self, key: str):
    #     self._set_selected_nav(key)
    #     target = self._nav_to_frame.get(key)
    #     if target and target in self.frames:
    #         self._switch_frame(target)

    def select_frame_by_name(self, name: str):
        self._switch_frame(name)

    def _on_appearance_change(self, _evt=None):
        choice = self.appearance.get()
        messagebox.showinfo("Appearance", f"Selected: {choice}")
