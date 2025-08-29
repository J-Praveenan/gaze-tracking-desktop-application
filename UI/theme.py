from tkinter import ttk

class Colors:
    bg          = "#0b2e3b"
    bg_tint     = "#0b2e3b"   # changed, no alpha
    banner_bg   = "#98b6e6"
    banner_text = "#111827"
    sidebar_bg  = "#1f2a37"
    card_bg     = "#e0edff"
    dark_card   = "#1f2937"
    card_head   = "#0f172a"
    card_text   = "#0f172a"
    muted       = "#475569"
    tips        = "#b42318"
    pill_bg     = "#3b82f6"
    pill_fg     = "#ffffff"


class Fonts:
    banner = ("Segoe UI", 20, "bold")
    h1     = ("Segoe UI", 18, "bold")
    h2b    = ("Segoe UI", 14, "bold")
    h3     = ("Segoe UI", 12, "bold")
    body   = ("Segoe UI", 10)

def apply_base_style(root):
    s = ttk.Style(root)
    try:
        s.theme_use("vista")
    except Exception:
        pass
    s.configure("TFrame", background=Colors.card_bg)
    s.configure("TLabel", background=Colors.card_bg, foreground=Colors.card_text, font=Fonts.body)
    s.configure("TButton", font=Fonts.body)
    s.configure("Nav.TButton", anchor="w", padding=(12, 10), relief="flat")
    s.map("Nav.TButton",
          background=[("!active", Colors.sidebar_bg), ("active", "#243143")],
          foreground=[("!active", "#e5e7eb"), ("active", "#ffffff")])
    s.configure("NavActive.TButton", background="#2b3a4d", foreground="#ffffff")
