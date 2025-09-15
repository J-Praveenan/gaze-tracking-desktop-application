# UI/pages/home.py
import tkinter as tk
from tkinter import ttk, messagebox
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from .base import BasePage


def F(name, default):
    """Safe font getter, e.g. F('h3', ('Segoe UI', 12, 'bold'))"""
    return getattr(Fonts, name, default)


# ---- layout knobs ----
SIDEBAR_W, SIDEBAR_H = 0.21, 0.86
SIDEBAR_X, SIDEBAR_REL = 0.045, 0.55

MAIN_W = 0.70
MAIN_RELX = SIDEBAR_X + SIDEBAR_W + (1 - (SIDEBAR_X + SIDEBAR_W)) * 0.5
MAIN_RELH, MAIN_RELY = SIDEBAR_H, SIDEBAR_REL


def DLabel(parent, **kw):
    """Label that sits on a dark card (no halos)."""
    base = dict(bg=Colors.dark_card, fg="#ffffff", bd=0, highlightthickness=0)
    base.update(kw)
    return tk.Label(parent, **base)


# -------------------- Right-side sections (simple placeholders) --------------------

class _SectionBase(tk.Frame):
    def __init__(self, parent, title: str, subtitle: str = ""):
        super().__init__(parent, bg=Colors.page_bg)
        # banner
        banner = RoundedCard(self, radius=18, pad=6, bg=Colors.dark_card, tight=False)
        banner.pack(fill="x", pady=(0, 8))
        DLabel(
            banner.body,
            text=title,
            font=F("h2b", ("Segoe UI", 14, "bold")),
            justify="center"
        ).pack(fill="x", padx=6, pady=(2, 6))
        if subtitle:
            tk.Label(
                banner.body, text=subtitle, fg="#cfd8e3", bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10)), justify="center", wraplength=1100
            ).pack(fill="x", padx=6, pady=(0, 6))

        # glass body area to put content in
        self.glass = RoundedCard(self, radius=18, pad=14, bg=Colors.glass_bg, tight=False)
        self.glass.pack(fill="both", expand=True, pady=(0, 8))
        self.body = tk.Frame(self.glass.body, bg=self.glass.cget("bg"))
        self.body.pack(fill="both", expand=True)


class HomeSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(
            parent,
            "Welcome to LOOK TRACK VISION",
            "Control your computer with your eyes and voice — hands-free, intuitive, empowering."
        )
        # ---- Control Mode ----
        self._section(parent=self.body, title="Control Mode",
                      desc="Select how you want to control apps using your gaze — automatic or manual.")

    def _section(self, parent, title, desc):
        box = tk.Frame(parent, bg=self.glass.cget("bg"),
                       highlightbackground="#4a637d", highlightcolor="#4a637d",
                       highlightthickness=2, bd=0)
        box.pack(fill="x", pady=(6, 10))
        tk.Label(box, text=title, font=F("h2b", ("Segoe UI", 14, "bold")),
                 fg=Colors.card_head, bg=self.glass.cget("bg")).pack(anchor="w", padx=18, pady=(10, 0))
        tk.Label(box, text=desc, font=F("body", ("Segoe UI", 11)),
                 fg=Colors.muted, bg=self.glass.cget("bg"), wraplength=1000
                 ).pack(anchor="w", padx=18, pady=(2, 8))

        mode_var = tk.StringVar(value="auto")
        r = tk.Frame(box, bg=self.glass.cget("bg")); r.pack(anchor="w", padx=18, pady=(2, 12))
        ttk.Radiobutton(r, text="Auto Control", value="auto", variable=mode_var).pack(side="left", padx=(0, 18))
        ttk.Radiobutton(r, text="Manual Control", value="manual", variable=mode_var).pack(side="left")

        # tips + start
        tips = tk.Label(self.body,
                        text="These gaze and blink actions work across the entire application.",
                        font=F("body", ("Segoe UI", 11)), fg=Colors.tips, bg=self.glass.cget("bg"))
        tips.pack(anchor="w", pady=(6, 0), padx=12)

        right = tk.Frame(self.body, bg=self.glass.cget("bg"))
        right.pack(anchor="e", fill="x", pady=(8, 4))
        PillButton(right, text="START APPLICATION   ⏻",
                   command=lambda: messagebox.showinfo("LOOK TRACK VISION", "Start your backend here.")
                   ).pack(side="right", padx=6, pady=4)


class SetupSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(parent, "Set Up Gaze Tracking",
                         "Calibrate camera, eye model, and environment.")
        tk.Label(self.body, text="(Your setup UI goes here)", bg=self.glass.cget("bg"),
                 fg=Colors.card_text, font=F("body", ("Segoe UI", 11))).pack(padx=16, pady=12, anchor="w")


class AppsSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(parent, "Apps Control", "Bind gaze gestures to your favorite apps.")
        tk.Label(self.body, text="(Your apps mapping UI goes here)", bg=self.glass.cget("bg"),
                 fg=Colors.card_text, font=F("body", ("Segoe UI", 11))).pack(padx=16, pady=12, anchor="w")


class SystemSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(parent, "System Control", "Volume, brightness, mouse, and more.")
        tk.Label(self.body, text="(Your system controls go here)", bg=self.glass.cget("bg"),
                 fg=Colors.card_text, font=F("body", ("Segoe UI", 11))).pack(padx=16, pady=12, anchor="w")


class TipsSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(parent, "Tips", "Helpful hints for smooth gaze navigation.")
        tk.Label(self.body, text="(Your tips content goes here)", bg=self.glass.cget("bg"),
                 fg=Colors.card_text, font=F("body", ("Segoe UI", 11))).pack(padx=16, pady=12, anchor="w")


class InfoSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(parent, "Information", "Version, authors, credits, links.")
        tk.Label(self.body, text="(Your info content goes here)", bg=self.glass.cget("bg"),
                 fg=Colors.card_text, font=F("body", ("Segoe UI", 11))).pack(padx=16, pady=12, anchor="w")


class SettingsSection(_SectionBase):
    def __init__(self, parent):
        super().__init__(parent, "Settings", "Theme, audio, accessibility, preferences.")
        tk.Label(self.body, text="(Your settings UI goes here)", bg=self.glass.cget("bg"),
                 fg=Colors.card_text, font=F("body", ("Segoe UI", 11))).pack(padx=16, pady=12, anchor="w")


# -------------------- Home page with persistent sidebar --------------------

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        # ---------- SIDEBAR ----------
        self.sidebar = RoundedCard(self.overlay, radius=24, pad=10,
                                   bg=Colors.sidebar_bg, tight=False)
        self.sidebar.place(relx=SIDEBAR_X, rely=SIDEBAR_REL, anchor="w",
                           relwidth=SIDEBAR_W, relheight=SIDEBAR_H)
        self._build_sidebar(self.sidebar.body)

        # ---------- MAIN COLUMN (holds swappable sections) ----------
        self.main_col = tk.Frame(self.overlay, bg=Colors.page_bg)
        self.main_col.place(relx=MAIN_RELX, rely=MAIN_RELY, anchor="center",
                            relwidth=MAIN_W, relheight=MAIN_RELH)

        # section host (stack); we create all once and raise the one we need
        self.sections = {
            "Home":       HomeSection(self.main_col),
            "Setup":      SetupSection(self.main_col),
            "Apps":       AppsSection(self.main_col),
            "System":     SystemSection(self.main_col),
            "Tips":       TipsSection(self.main_col),
            "Info":       InfoSection(self.main_col),
            "Settings":   SettingsSection(self.main_col),
        }
        for s in self.sections.values():
            s.place(relx=0, rely=0, relwidth=1, relheight=1)

        # default
        self.show_section("Home")

    # =================== SIDEBAR WITH MOVING ROUNDED OUTLINE ===================

    def _build_sidebar(self, parent):
        """
        Sidebar with clickable rows and a rounded white outline that glides
        to the clicked row. We do NOT navigate to other top-level pages; instead
        we call show_section(...) to swap the RIGHT content only.
        """
        parent.configure(bg=Colors.sidebar_bg)
        for w in parent.winfo_children():
            w.destroy()

        wrap = tk.Frame(parent, bg=Colors.sidebar_bg)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        # Canvas for the moving rounded outline; sits BEHIND the rows.
        self._hilite = tk.Canvas(wrap, bg=Colors.sidebar_bg, highlightthickness=0, bd=0)
        self._hilite.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Rows on top
        self._rows = tk.Frame(wrap, bg=Colors.sidebar_bg)
        self._rows.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Offscreen outline at start (nothing selected)
        self._outline_ids = self._draw_round_outline(self._hilite, -100, -100, -50, -50,
                                                     r=14, width=3, color="#e6eef7")
        self._current_row = None
        self._rows.lift()

        # Home (label only)
        home = tk.Frame(self._rows, bg=Colors.sidebar_bg, takefocus=0, cursor="hand2")
        home.pack(anchor="w")
        lbl_home = tk.Label(home, text="  🏠  Home",
                            font=F("h2b", ("Segoe UI", 14, "bold")),
                            fg="#e6eef7", bg=Colors.sidebar_bg, bd=0)
        lbl_home.pack(padx=14, pady=8)

        tk.Frame(self._rows, height=12, bg=Colors.sidebar_bg).pack(fill="x")

        # Sidebar items -> section keys
        items = [
            ("Set Up Gaze Tracking", "Setup",    "⚙️"),
            ("Apps Control",         "Apps",     "🧩"),
            ("System Control",       "System",   "🖥️"),
            ("Tips",                 "Tips",     "💡"),
            ("Information",          "Info",     "ℹ️"),
            ("Settings",             "Settings", "⚙️"),
        ]

        self._row_widgets = []

        def _bind_click(widget, section_key, row_widget):
            def on_click(_evt=None, key=section_key, rw=row_widget):
                first_time = self._current_row is None
                self._current_row = rw
                self._move_outline_to_row(rw, instant=first_time)
                self.after(80, lambda: self.show_section(key))   # swap right side only
                try:
                    self.overlay.focus_set()
                except Exception:
                    pass
            widget.bind("<Button-1>", on_click)

        # Make Home clickable too
        _bind_click(home, "Home", home)
        _bind_click(lbl_home, "Home", home)
        self._row_widgets.append(home)

        for text, key, icon in items:
            row = tk.Frame(self._rows, bg=Colors.sidebar_bg, cursor="hand2", takefocus=0)
            row.pack(fill="x", pady=10)

            tk.Label(row, text=icon, takefocus=0,
                     font=F("h3", ("Segoe UI", 12, "bold")),
                     fg="#e6eef7", bg=Colors.sidebar_bg).pack(side="left", padx=(2, 10))

            lbl = tk.Label(row, text=text, takefocus=0,
                           font=F("h3", ("Segoe UI", 12, "bold")),
                           fg="#e6eef7", bg=Colors.sidebar_bg, bd=0)
            lbl.pack(side="left")

            _bind_click(row, key, row)
            _bind_click(lbl, key, row)
            self._row_widgets.append(row)

    # ---- rounded outline helpers (canvas: 4 arcs + 4 lines) ----
    def _draw_round_outline(self, canvas, x1, y1, x2, y2, r=12, width=2, color="#fff"):
        r = max(0, min(r, int(min(x2 - x1, y2 - y1) / 2)))
        ids = {}
        ids["a_tl"] = canvas.create_arc(x1, y1, x1 + 2*r, y1 + 2*r,
                                        start=90, extent=90, style="arc",
                                        outline=color, width=width)
        ids["a_tr"] = canvas.create_arc(x2 - 2*r, y1, x2, y1 + 2*r,
                                        start=0, extent=90, style="arc",
                                        outline=color, width=width)
        ids["a_br"] = canvas.create_arc(x2 - 2*r, y2 - 2*r, x2, y2,
                                        start=270, extent=90, style="arc",
                                        outline=color, width=width)
        ids["a_bl"] = canvas.create_arc(x1, y2 - 2*r, x1 + 2*r, y2,
                                        start=180, extent=90, style="arc",
                                        outline=color, width=width)
        ids["l_top"]   = canvas.create_line(x1 + r, y1, x2 - r, y1, fill=color, width=width)
        ids["l_right"] = canvas.create_line(x2, y1 + r, x2, y2 - r, fill=color, width=width)
        ids["l_bot"]   = canvas.create_line(x1 + r, y2, x2 - r, y2, fill=color, width=width)
        ids["l_left"]  = canvas.create_line(x1, y1 + r, x1, y2 - r, fill=color, width=width)
        ids["_bbox"] = [x1, y1, x2, y2, r, width]
        return ids

    def _set_round_outline(self, ids, x1, y1, x2, y2):
        c = self._hilite
        _, _, _, _, r, _ = ids["_bbox"]
        c.coords(ids["a_tl"], x1, y1, x1 + 2*r, y1 + 2*r)
        c.coords(ids["a_tr"], x2 - 2*r, y1, x2, y1 + 2*r)
        c.coords(ids["a_br"], x2 - 2*r, y2 - 2*r, x2, y2)
        c.coords(ids["a_bl"], x1, y2 - 2*r, x1 + 2*r, y2)
        c.coords(ids["l_top"],   x1 + r, y1, x2 - r, y1)
        c.coords(ids["l_right"], x2, y1 + r, x2, y2 - r)
        c.coords(ids["l_bot"],   x1 + r, y2, x2 - r, y2)
        c.coords(ids["l_left"],  x1, y1 + r, x1, y2 - r)
        ids["_bbox"][:4] = [x1, y1, x2, y2]

    def _move_outline_to_row(self, row, instant=False):
        """Animate the rounded outline to wrap the given row."""
        try:
            y = row.winfo_y()
            h = row.winfo_height() or 40
            pad_x, pad_y = 12, 6
            x1 = pad_x
            y1 = max(0, y - pad_y)
            x2 = self._rows.winfo_width() - pad_x
            y2 = y + h + pad_y
        except Exception:
            return

        cx1, cy1, cx2, cy2, *_ = self._outline_ids["_bbox"]

        if instant or cx1 == cx2 == 0:
            self._set_round_outline(self._outline_ids, x1, y1, x2, y2)
            self._rows.lift()   # keep rows above the canvas
            return

        steps = 12
        dx1 = (x1 - cx1) / steps
        dy1 = (y1 - cy1) / steps
        dx2 = (x2 - cx2) / steps
        dy2 = (y2 - cy2) / steps

        def step(i=0, a=cx1, b=cy1, c=cx2, d=cy2):
            na, nb, nc, nd = a + dx1, b + dy1, c + dx2, d + dy2
            self._set_round_outline(self._outline_ids, na, nb, nc, nd)
            self._rows.lift()
            if i < steps - 1:
                self.after(12, lambda: step(i + 1, na, nb, nc, nd))
            else:
                self._set_round_outline(self._outline_ids, x1, y1, x2, y2)
                self._rows.lift()
        step()

    # ---------- section swap ----------
    def show_section(self, key: str):
        """Raise only the right-side section; sidebar remains."""
        sect = self.sections.get(key)
        if not sect:
            return
        sect.tkraise()

    # ---------- actions ----------
    def _start_app(self):
        messagebox.showinfo(
            "LOOK TRACK VISION",
            "Start Application clicked.\nHook this to start your backend."
        )

    def _run_calibration(self):
        """Launch Calibration/Calibration.py in a separate process so Tk stays responsive."""
        calib_path = self._find_calibration_script()
        if not calib_path:
            messagebox.showerror("Calibration", "Could not find Calibration.py (looked under ./Calibration/).")
            return

        btn = self.sidebar_buttons.get("Set Up Gaze Tracking")
        if btn:
            btn.state(['disabled'])

        def work():
            rc = -1
            try:
                rc = subprocess.run([sys.executable, "-u", str(calib_path)]).returncode
            except Exception:
                rc = -1

            def done():
                if btn:
                    btn.state(['!disabled'])
                if rc == 0:
                    messagebox.showinfo("Calibration", "Calibration complete. Thresholds saved.")
                else:
                    messagebox.showwarning("Calibration", "Calibration cancelled or failed. Check console output.")
            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()
        
        
        
    def _run_gaze_tracker(self):
        """
        Launch main.py in a separate process so the Tk UI stays responsive.
        """
        main_path = self._find_main_script()
        if not main_path:
            messagebox.showerror("Gaze Tracker", "Could not find main.py.")
            return

        btn = self.sidebar_buttons.get("Gaze Tracker")
        if btn:
            btn.state(['disabled'])

        def work():
            rc = -1
            try:
                # -u for unbuffered prints; run with same interpreter
                rc = subprocess.run([sys.executable, "-u", str(main_path)]).returncode
            except Exception:
                rc = -1

            def done():
                if btn:
                    btn.state(['!disabled'])
                if rc == 0:
                    messagebox.showinfo("Gaze Tracker", "Gaze tracker closed.")
                else:
                    messagebox.showwarning("Gaze Tracker", "Gaze tracker ended with an error. Check console.")
            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _find_main_script(self) -> Path | None:
        """
        Try to locate main.py (your gaze tracker) in common places.
        Adjust as needed if you keep it elsewhere.
        """
        candidates = [
            Path.cwd() / "main.py",
            Path(__file__).resolve().parents[2] / "main.py",      # project root
            Path(__file__).resolve().parent / "main.py",          # same folder (unlikely)
        ]
        for p in candidates:
            if p.exists():
                return p
        return None


    def _find_calibration_script(self) -> Path | None:
        """Try to locate Calibration.py or calibration.py in a Calibration/ folder."""
        candidates = [
            Path.cwd() / "Calibration" / "Calibration.py",
            Path.cwd() / "Calibration" / "calibration.py",
            Path(__file__).resolve().parent / "Calibration" / "Calibration.py",
            Path(__file__).resolve().parent / "Calibration" / "calibration.py",
            Path(__file__).resolve().parents[1] / "Calibration" / "Calibration.py",
            Path(__file__).resolve().parents[1] / "Calibration" / "calibration.py",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def on_show(self):
        # Optional: clear the outline when the page is re-shown
        if hasattr(self, "_outline_ids"):
            self._set_round_outline(self._outline_ids, -100, -100, -50, -50)
            self._current_row = None
        # ensure current section visible
        self.show_section("Home")
