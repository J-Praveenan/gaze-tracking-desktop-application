import tkinter as tk
from UI.theme import Colors, Fonts
from PIL import Image, ImageTk
import os


def F(name, default):
    return getattr(Fonts, name, default)


class InstructionTray(tk.Toplevel):
    def __init__(self, master=None, controller=None):
        super().__init__(master)
        self.controller = controller
        self.title("Look Track Vision - Eye Controls")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=Colors.dark_card)

        # === Tray size & position ===
        width, height = 1280, 150
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(sw - width)//2}+{sh - height - 40}")

        tray = tk.Frame(self, bg=Colors.dark_card, padx=14, pady=10)
        tray.pack(fill="both", expand=True)

        content = tk.Frame(tray, bg=Colors.dark_card)
        content.pack(side="left", fill="both", expand=True)

        # === Load icons ===
        assets = os.path.join(os.path.dirname(__file__), "../../assets")

        def load_icon(name, size=(56, 56)):
            p = os.path.join(assets, name)
            try:
                return ImageTk.PhotoImage(Image.open(p).resize(size, Image.LANCZOS))
            except Exception:
                print(f"[WARN] Could not load {name}")
                return None

        icons = {
            "up": load_icon("up.png"),
            "down": load_icon("down.png"),
            "left": load_icon("left.png"),
            "right": load_icon("right.png"),
            "left_blink": load_icon("left_eye_blink.png"),
            "right_blink": load_icon("right_eye_blink.png"),
            "closed_short": load_icon("closed_less_than_2mins.png"),
            "closed_long": load_icon("closed_greater_than_2mins.png"),
            "cycle_blink": load_icon("cycle_blink.png", size=(350, 350)),
            "info": load_icon("info.png", size=(18, 18)),
            "start": load_icon("power_on.png", size=(40, 40)),
            "stop": load_icon("power_off.png", size=(40, 40)),
        }

        # === Instruction Controls ===
        controls = [
            (icons["up"], "Look Up", "Move Pointer Up"),
            (icons["down"], "Look Down", "Move Pointer Down"),
            (icons["left"], "Look Left", "Move Pointer Left"),
            (icons["right"], "Look Right", "Move Pointer Right"),
            (icons["left_blink"], "Left Blink", "Left Click"),
            (icons["right_blink"], "Right Blink", "Right Click"),
            (icons["closed_long"], "Long Blink", "Scroll Mode"),
            (icons["closed_short"], "Short Blink", "Cycle Pointer"),
        ]

        controls_frame = tk.Frame(content, bg=Colors.dark_card)
        controls_frame.pack(fill="x", pady=(10, 0))

        for icon, title, desc in controls:
            block = tk.Frame(controls_frame, bg=Colors.dark_card, padx=14, pady=2)
            block.pack(side="left", expand=True, anchor="n")

            if icon:
                lbl = tk.Label(block, image=icon, bg=Colors.dark_card)
                lbl.pack(anchor="center", pady=(0, 5))
                block.icon_ref = icon

            title_frame = tk.Frame(block, bg=Colors.dark_card)
            title_frame.pack()

            tk.Label(
                title_frame,
                text=title,
                fg="white",
                bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10, "bold"))
            ).pack(side="left")

            # Info icon for Short Blink
            if title == "Short Blink":
                info_icon = tk.Label(
                    title_frame, image=icons["info"], bg=Colors.dark_card, cursor="hand2"
                )
                info_icon.image_ref = icons["info"]
                info_icon.pack(side="left", padx=(4, 0))
                self.add_cycle_popup_behavior(info_icon, icons["cycle_blink"])

            tk.Label(
                block,
                text=desc,
                fg="#9ca3af",
                bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 9))
            ).pack(anchor="center")

        # === START / STOP APPLICATION BUTTON ===
        start_frame = tk.Frame(controls_frame, bg=Colors.dark_card, padx=14, pady=0)
        start_frame.pack(side="left", expand=True, anchor="center", pady=(10, 0))

        self.app_running = False
        self.start_icon = icons["start"]
        self.stop_icon = icons["stop"]

        # Center contents inside start_frame
        inner = tk.Frame(start_frame, bg=Colors.dark_card)
        inner.pack(expand=True)

        self.start_button = tk.Label(
            inner,
            image=self.start_icon,
            bg=Colors.dark_card,
            cursor="hand2"
        )
        self.start_button.pack(anchor="center", pady=(0, 2))
        self.start_button.bind("<Button-1>", self.toggle_app)

        tk.Label(
            inner,
            text="Start Application",
            fg="white",
            bg=Colors.dark_card,
            font=F("body", ("Segoe UI", 10, "bold"))
        ).pack(anchor="center", pady=(0, 0))


        # === Close Tray Button (small, top-right corner) ===
        base_dir = os.path.dirname(os.path.abspath(__file__))
        close_icon_path = os.path.abspath(os.path.join(base_dir, "../../assets/close_icon.png"))

        # fallback to new file name if not found
        if not os.path.exists(close_icon_path):
            alt_path = os.path.abspath(os.path.join(base_dir, "../../assets/6ba7585a-a971-4836-be42-811be238a80b.png"))
            if os.path.exists(alt_path):
                close_icon_path = alt_path
            else:
                print(f"[WARN] Close icon not found at: {close_icon_path}")
                close_icon_path = None

        close_img = None
        if close_icon_path:
            try:
                close_img = ImageTk.PhotoImage(Image.open(close_icon_path).resize((24, 24), Image.LANCZOS))
                print(f"[INFO] Loaded close icon from: {close_icon_path}")
            except Exception as e:
                print(f"[WARN] Could not load close icon: {e}")

        if close_img:
            close_btn = tk.Label(self, image=close_img, bg=Colors.dark_card, cursor="hand2")
            close_btn.image = close_img
            close_btn.place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")
            close_btn.bind("<Button-1>", lambda e: self.destroy())
        else:
            tk.Button(
                self,
                text="×",
                command=self.destroy,
                bg="#ef4444",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                width=2,
                height=1,
                cursor="hand2"
            ).place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")

        # === Enable tray drag ===
        tray.bind("<ButtonPress-1>", self.start_move)
        tray.bind("<B1-Motion>", self.on_move)

        self.cycle_popup = None

    # === Cycle Blink Popup ===
    def add_cycle_popup_behavior(self, widget, image):
        def show_popup(event=None):
            if self.cycle_popup and self.cycle_popup.winfo_exists():
                self.close_cycle_popup()
                return
            popup = tk.Toplevel(self)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(bg=Colors.dark_card, padx=8, pady=8, bd=2, relief="solid")
            tk.Label(popup, image=image, bg=Colors.dark_card).pack()
            popup.image_ref = image
            x = widget.winfo_rootx() - 150
            y = widget.winfo_rooty() - 370
            popup.geometry(f"+{x}+{y}")
            self.cycle_popup = popup
            self.bind_all("<Button-1>", self._handle_outside_click, add="+")
            widget.bind("<Leave>", lambda e: self.close_cycle_popup())

        widget.bind("<Enter>", show_popup)
        widget.bind("<Button-1>", show_popup)

    def _handle_outside_click(self, event):
        if not self.cycle_popup or not self.cycle_popup.winfo_exists():
            return
        try:
            px, py = self.cycle_popup.winfo_rootx(), self.cycle_popup.winfo_rooty()
            pw, ph = self.cycle_popup.winfo_width(), self.cycle_popup.winfo_height()
            if not (px <= event.x_root <= px + pw and py <= event.y_root <= py + ph):
                self.close_cycle_popup()
        except tk.TclError:
            pass

    def close_cycle_popup(self):
        if self.cycle_popup:
            try:
                self.cycle_popup.destroy()
            except tk.TclError:
                pass
            self.cycle_popup = None
        self.unbind_all("<Button-1>")

    # === Start/Stop Gaze App Toggle ===
    def toggle_app(self, event=None):
        """Start or stop the gaze control dynamically (lazy import to avoid circular import)."""
        try:
            from UI.pages.home import launch_gaze_app  # local import fixes circular import
        except ImportError:
            print("[WARN] Could not import launch_gaze_app dynamically.")
            return

        if not self.app_running:
            launch_gaze_app(enable_mouse_control=True)
            self.app_running = True
            self.start_button.configure(image=self.stop_icon)
        else:
            launch_gaze_app(enable_mouse_control=False)
            self.app_running = False
            self.start_button.configure(image=self.start_icon)


    # === Moveable Tray ===
    def start_move(self, e):
        self.x, self.y = e.x, e.y

    def on_move(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self.x}+{self.winfo_y() + e.y - self.y}")
