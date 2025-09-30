import tkinter as tk
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard

def F(name, default):
    return getattr(Fonts, name, default)

class Sidebar(RoundedCard):
    def __init__(self, parent, controller):
        super().__init__(parent, radius=18, pad=10, bg=Colors.dark_card, tight=False)
        self.place(relx=0.045, rely=0.45, anchor="w", relwidth=0.23, relheight=0.86)
        self.controller = controller
        self._nav_rows, self._nav_btns = {}, {}
        self._build_sidebar(self.body)

    def _build_sidebar(self, parent):
        parent.configure(bg=Colors.sidebar_bg)
        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)
        wrap.grid_rowconfigure(8, weight=1)

        def _nav_row(row_index, key, text, target_page):
            cont = tk.Frame(wrap, bg=Colors.sidebar_bg)
            cont.grid(row=row_index, column=0, sticky="ew", pady=6)

            btn = tk.Button(
                cont, text=("  " + text), anchor="w",
                font=F("h3", ("Segoe UI", 12, "bold")),
                fg="white", bg=Colors.sidebar_bg, bd=0, relief="flat",
                activebackground="#1d4ed8", activeforeground="white",
                cursor="hand2", command=lambda: self.controller.show(target_page)
            )
            btn.configure(padx=12, pady=8)
            btn.bind("<Enter>", lambda e: btn.configure(bg="#2b3947"))
            btn.bind("<Leave>", lambda e: btn.configure(bg=Colors.sidebar_bg))
            btn.pack(fill="x", padx=6, pady=6)

            self._nav_rows[key] = cont
            self._nav_btns[key] = btn

        r = 1
        _nav_row(r, "home", "Home", "HomePage"); r += 1
        _nav_row(r, "setup", "Set Up Gaze Tracking", "SetupPage"); r += 1
        _nav_row(r, "gaze_test", "Gaze Test", "GazeTestPage"); r += 1
        _nav_row(r, "tips", "Tips", "TipsPage"); r += 1
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=r, column=0, sticky="nsew"); r += 1
        _nav_row(r, "info", "Information", "InfoPage"); r += 1
        
        # spacer row (row=99 expands to fill available space)
        tk.Frame(wrap, bg=Colors.sidebar_bg).grid(row=99, column=0, sticky="nsew")

        # settings pinned to bottom
        _nav_row(100, "settings", "Settings", "SettingsPage")
