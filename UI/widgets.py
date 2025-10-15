import tkinter as tk
from tkinter import ttk
from UI.theme import Colors, Fonts
from PIL import Image, ImageTk
from pathlib import Path
import os
from tkinter import font as tkfont
import threading



class RoundedCard(tk.Frame):
    def __init__(self, parent, border_color="#222", border_width=0,
                 radius=16, pad=12, bg=None, tight=True, **kwargs):
        self.radius = radius
        self._bg = bg or Colors.card_bg
        self._tight = tight
        self.border_color = border_color
        self.border_width = border_width
        self.pad = pad

        # prevent tkinter from seeing these
        kwargs.pop("border_color", None)
        kwargs.pop("border_width", None)

        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=0, **kwargs)

        self.canvas = tk.Canvas(self, bg=self["bg"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=self._bg)

        self.bind("<Configure>", self._draw)
        # self.body.bind("<Configure>", lambda e: self._draw())

    def _draw(self, _evt=None):
        w = max(10, self.winfo_width())

        if self._tight:
            reqh = max(10, self.body.winfo_reqheight())
            h = reqh + 2*self.pad
        else:
            h = max(10, self.winfo_height())

        self.canvas.config(width=w, height=h)
        self.canvas.delete("all")

        r = min(self.radius, h // 2, w // 2)

        # --- Background fill ---
        self.canvas.create_rectangle(r, 0, w-r, h, fill=self._bg, outline="")
        self.canvas.create_rectangle(0, r, w, h-r, fill=self._bg, outline="")
        for x, y in [(0,0), (w-2*r,0), (0,h-2*r), (w-2*r,h-2*r)]:
            self.canvas.create_oval(x, y, x+2*r, y+2*r, fill=self._bg, outline="")

        # --- Border stroke (only if border_width > 0) ---
        if self.border_width > 0:
            # top line
            self.canvas.create_line(r, 0, w-r, 0,
                                    fill=self.border_color, width=self.border_width)
            # bottom line
            self.canvas.create_line(r, h, w-r, h,
                                    fill=self.border_color, width=self.border_width)
            # left line
            self.canvas.create_line(0, r, 0, h-r,
                                    fill=self.border_color, width=self.border_width)
            # right line
            self.canvas.create_line(w, r, w, h-r,
                                    fill=self.border_color, width=self.border_width)
            # 4 arcs for corners
            self.canvas.create_arc(0, 0, 2*r, 2*r, start=90, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)
            self.canvas.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)
            self.canvas.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)
            self.canvas.create_arc(0, h-2*r, 2*r, h, start=180, extent=90,
                                   style="arc", outline=self.border_color, width=self.border_width)

        # place inner body
        self.canvas.create_window(
            self.pad, self.pad, window=self.body, anchor="nw",
            width=max(1, w-2*self.pad), height=max(1, h-2*self.pad)
        )

class TitleBar(tk.Frame):
    """Header with logo + title and a thin bottom border, plus Start/Stop button."""
    def __init__(self, parent, logo_img=None, title_text="", on_toggle_gaze=None):
        super().__init__(parent, bg="#dbeafe", height=48, highlightthickness=0)
        self.pack_propagate(False)

        self.on_toggle_gaze = on_toggle_gaze  # ✅ callback from parent
        self.app_running = False

        # Left side logo + title
        self.logo = tk.Label(self, image=logo_img, bg=self["bg"])
        self.logo.image = logo_img
        self.logo.pack(side="left", padx=(10, 8), pady=6)

        self.title = tk.Label(
            self, text=title_text,
            font=("Segoe UI", 14, "bold"), bg=self["bg"], fg="#111827"
        )
        self.title.pack(side="left")

        # Load icons
        ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
        self.power_on_icon = ImageTk.PhotoImage(Image.open(ASSETS_DIR / "power_on.png").resize((20, 20)))
        self.power_off_icon = ImageTk.PhotoImage(Image.open(ASSETS_DIR / "power_off.png").resize((20, 20)))

        # Button
        self.square_btn = tk.Button(
            self,
            text=" START", image=self.power_on_icon,
            compound="left", font=("Segoe UI", 10, "bold"),
            fg="white", bg="#2563eb", activebackground="#1e40af",
            activeforeground="white", bd=0, relief="flat",
            padx=10, pady=4, cursor="hand2",
            command=self._toggle_gaze
        )
        self.square_btn.pack(side="right", padx=(0, 50), pady=6)

        self.border = tk.Frame(parent, bg="#1d4ed8", height=2)
        self.border.pack(fill="x", side="top")

    def _toggle_gaze(self):
        """Toggle start/stop state and delegate action to parent."""
        self.app_running = not self.app_running
        if self.on_toggle_gaze:
            self.on_toggle_gaze(self.app_running)  # ✅ call parent callback

        if self.app_running:
            self.square_btn.config(
                text=" STOP",
                image=self.power_off_icon,
                bg="#dc2626",
                activebackground="#b91c1c"
            )
        else:
            self.square_btn.config(
                text=" START",
                image=self.power_on_icon,
                bg="#2563eb",
                activebackground="#1e40af"
            )

    def set_logo(self, img):
        if img:
            self.logo.configure(image=img)
            self.logo.image = img
        
    def update_gaze_button(self, running: bool):
        """Update the TitleBar button appearance."""
        if running:
            self.square_btn.config(
                text=" STOP",
                image=self.power_off_icon,
                bg="#dc2626",
                activebackground="#b91c1c"
            )
            self.app_running = True
        else:
            self.square_btn.config(
                text=" START",
                image=self.power_on_icon,
                bg="#2563eb",
                activebackground="#1e40af"
            )
            self.app_running = False




class PillButton(tk.Button):
    """Rounded style button (visual)."""
    def __init__(self, parent, text, command=None):
        super().__init__(parent, text=text, command=command,
                         font=("Segoe UI", 10, "bold"),
                         fg=Colors.pill_fg, bg=Colors.pill_bg, activebackground="#2563eb",
                         bd=0, padx=18, pady=8, cursor="hand2")




class RoundedButton(tk.Canvas):
    def __init__(self, parent, text="", radius=16,
                 padding_x=18, padding_y=8,
                 bg="#2563eb", fg="white",
                 command=None, activebg="#1e40af",
                 font=None, icon=None):
        super().__init__(parent, highlightthickness=0, bg=parent["bg"], bd=0)
        self.command = command
        self.bg = bg
        self.fg = fg
        self.activebg = activebg
        self.text = text
        self.icon = icon
        self.radius = radius
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.font = font or ("Segoe UI Semibold", 11)

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self._set_color(self.activebg))
        self.bind("<Leave>", lambda e: self._set_color(self.bg))

        self._draw_button()

    def _set_color(self, color):
        self.itemconfig("button", fill=color)
        self.itemconfig("side", fill=color)

    def _draw_button(self):
        fnt = tkfont.Font(font=self.font)
        text_w = fnt.measure(self.text)
        text_h = fnt.metrics("linespace")

        # button size
        height = text_h + 2 * self.padding_y
        width = text_w + 2 * self.padding_x

        # Add icon space if present
        icon_space = height * 0.8 if self.icon else 0
        width += icon_space

        self.config(width=width, height=height)
        r = min(self.radius, height // 2)

        # --- shape ---
        self.create_oval(0, 0, height, height, fill=self.bg, outline="", tags=("button", "side"))
        self.create_oval(width - height, 0, width, height, fill=self.bg, outline="", tags=("button", "side"))
        self.create_rectangle(height / 2, 0, width - height / 2, height,
                            fill=self.bg, outline="", tags=("button", "side"))

        # --- compute total centered content width ---
        icon_gap = height * 0.35 if self.icon else 0  # 👈 adjustable spacing between icon & text
        total_content_width = text_w + (icon_space if self.icon else 0) + icon_gap
        start_x = (width - total_content_width) / 2

        # --- draw icon ---
        if self.icon:
            icon_x = start_x + height * 0.4
            self.create_image(icon_x, height / 2, image=self.icon)
            start_x += icon_space + icon_gap  # move text start after icon + gap

        # --- draw text ---
        text_x = start_x + text_w / 2
        self.create_text(
            text_x, height / 2,
            text=self.text, fill=self.fg,
            font=self.font, tags="text"
        )

    def _on_click(self, event):
        if self.command:
            self.command()
