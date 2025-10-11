import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard
from PIL import Image, ImageTk
import os

# Get the absolute project root (two levels up from this file)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

# Build paths dynamically
home_icon_path = os.path.join(ASSETS_DIR, "home.png")
setting_icon_path = os.path.join(ASSETS_DIR, "setting.png")
tips_icon_path = os.path.join(ASSETS_DIR, "tips.png")
info_icon_path = os.path.join(ASSETS_DIR, "info.png")
gaze_set_up_icon_path = os.path.join(ASSETS_DIR, "gaze_set_up.png")
gaze_test_icon_path = os.path.join(ASSETS_DIR, "gaze_test.png")

def F(name, default):
    return getattr(Fonts, name, default)

class Sidebar(RoundedCard):
    def __init__(self, parent, controller):
        super().__init__(parent, radius=18, pad=10, bg=Colors.dark_card, tight=False)
        self.place(relx=0.045, rely=0.45, anchor="w", relwidth=0.23, relheight=0.86)
        self.controller = controller
        self._nav_rows, self._nav_btns = {}, {}
        self._icons = {}
        self.selected_key = None
        self._build_sidebar(self.body)
        self.after(100, lambda: self.highlight_selected("home"))

    def _build_sidebar(self, parent):
        parent.configure(bg=Colors.sidebar_bg)
        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)
        wrap.grid_rowconfigure(8, weight=1)

        def _nav_row(row_index, key, text, target_page, icon_path=None):
            cont = tk.Frame(wrap, bg=Colors.sidebar_bg)
            cont.grid(row=row_index, column=0, sticky="ew", pady=6)
            
            if icon_path and os.path.exists(icon_path):
                img = Image.open(icon_path).resize((20, 20), Image.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                self._icons[key] = icon  # ✅ keep reference
            else:
                icon = None
                
            
            def on_click():
                self.highlight_selected(key)

                # Proper delayed navigation (no tuple auto-execution)
                def do_switch():
                    self.controller.show(target_page)
                    self.highlight_selected(key)  # reapply highlight after page load

                self.controller.after(1,do_switch)

            btn = tk.Button(
                cont, text=("  " + text),image=icon,
                compound="left", anchor="w",
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
        _nav_row(r, "home", "Home", "HomePage", icon_path=home_icon_path); r += 1
        _nav_row(r, "setup", "Set Up Gaze Tracking", "SetupPage", icon_path=gaze_set_up_icon_path); r += 1
        _nav_row(r, "gaze_test", "Gaze Test", "GazeTestPage", icon_path=gaze_test_icon_path); r += 1
        _nav_row(r, "tips", "Tips", "TipsPage", icon_path=tips_icon_path); r += 1
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=r, column=0, sticky="nsew"); r += 1
        _nav_row(r, "info", "Information", "InfoPage", icon_path=info_icon_path); r += 1
        
        # spacer row (row=99 expands to fill available space)
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=99, column=0, sticky="nsew")

        # settings pinned to bottom
        _nav_row(100, "settings", "Settings", "SettingsPage", icon_path=setting_icon_path)
        
        
    # 🔹 Highlight selected sidebar item
    def highlight_selected(self, key):
        for k, cont in self._nav_rows.items():
            if k == key:
                cont.configure(
                    bg=Colors.sidebar_bg,
                    highlightbackground="white",
                    highlightthickness=2,
                    bd=0
                )
                self._nav_btns[k].configure(bg="#2b3947")  # active bg
                self.selected_key = key
            else:
                cont.configure(
                    bg=Colors.sidebar_bg,
                    highlightthickness=0,
                    bd=0
                )
                self._nav_btns[k].configure(bg=Colors.sidebar_bg)
