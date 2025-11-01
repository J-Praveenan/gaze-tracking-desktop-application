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

        # === Base screen size ===
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        height = 110

        # === Dynamically calculated width ===
        if sw >= 1920:
            width = 1300
        elif sw >= 1600:
            width = 1150
        elif sw >= 1366:
            width = 1000
        else:
            width = int(sw * 0.9)

        # === Center horizontally, position near bottom ===
        x = (sw - width) // 2
        y = sh - height - 40
        self.geometry(f"{width}x{height}+{x}+{y}")

        tray = tk.Frame(self, bg=Colors.dark_card, padx=10, pady=6)
        tray.pack(fill="both", expand=True)

        content = tk.Frame(tray, bg=Colors.dark_card)
        content.pack(fill="both", expand=True)
        content.pack_propagate(False)

        # === Load icons ===
        assets = os.path.join(os.path.dirname(__file__), "../../assets")

        def load_icon(name, size=(42, 42)):
            p = os.path.join(assets, name)
            try:
                return ImageTk.PhotoImage(Image.open(p).resize(size, Image.LANCZOS))
            except Exception:
                print(f"[WARN] Could not load {name}")
                return None

        icons = {
            "up": load_icon("up.ico"),
            "down": load_icon("down.ico"),
            "left": load_icon("left.ico"),
            "right": load_icon("right.ico"),
            "left_blink": load_icon("left_eye_blink.ico"),
            "right_blink": load_icon("right_eye_blink.ico"),
            "closed_short": load_icon("closed_less_than_2mins.ico"),
            "closed_long": load_icon("closed_greater_than_2mins.ico"),
            "cycle_blink": load_icon("cycle_blink.ico", size=(300, 300)),
            "info": load_icon("info.ico", size=(16, 16)),
            "start": load_icon("power_on.ico", size=(34, 34)),
            "stop": load_icon("power_off.ico", size=(34, 34)),
        }

        # === Controls ===
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
        controls_frame.pack(anchor="center", expand=True)

        for icon, title, desc in controls:
            block = tk.Frame(controls_frame, bg=Colors.dark_card, padx=8, pady=0)
            block.pack(side="left", expand=True, anchor="center")

            if icon:
                lbl = tk.Label(block, image=icon, bg=Colors.dark_card)
                lbl.pack(anchor="center", pady=(0, 2))
                block.icon_ref = icon

            title_frame = tk.Frame(block, bg=Colors.dark_card)
            title_frame.pack()

            tk.Label(
                title_frame,
                text=title,
                fg="white",
                bg=Colors.dark_card,
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")

            if title == "Short Blink":
                info_icon = tk.Label(
                    title_frame, image=icons["info"], bg=Colors.dark_card, cursor="hand2"
                )
                info_icon.image_ref = icons["info"]
                info_icon.pack(side="left", padx=(3, 0))
                self.add_cycle_popup_behavior(info_icon, icons["cycle_blink"])

            tk.Label(
                block,
                text=desc,
                fg="#9ca3af",
                bg=Colors.dark_card,
                font=("Segoe UI", 10)
            ).pack(anchor="center")

        # === Start/Stop Application Button ===
        start_frame = tk.Frame(controls_frame, bg=Colors.dark_card, padx=8, pady=0)
        start_frame.pack(side="left", expand=True, anchor="center")

        self.app_running = False
        self.start_icon = icons["start"]
        self.stop_icon = icons["stop"]

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

        self.start_label = tk.Label(
            inner,
            text="Start Application",
            fg="white",
            bg=Colors.dark_card,
            font=("Segoe UI", 11, "bold")
        )
        self.start_label.pack(anchor="center")


        # === Close Button (Always Visible, Fixed to Right Corner) ===
        close_path = os.path.abspath(os.path.join(assets, "close_icon.ico"))
        if not os.path.exists(close_path):
            close_path = os.path.abspath(os.path.join(assets, "6ba7585a-a971-4836-be42-811be238a80b.ico"))

        close_img = None
        if os.path.exists(close_path):
            try:
                close_img = ImageTk.PhotoImage(Image.open(close_path).resize((20, 20), Image.LANCZOS))
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

        # === Make tray movable ===
        tray.bind("<ButtonPress-1>", self.start_move)
        tray.bind("<B1-Motion>", self.on_move)

        self.cycle_popup = None

    # === Popup, Click, Move Methods ===
    def add_cycle_popup_behavior(self, widget, image):
        def show_popup(event=None):
            if self.cycle_popup and self.cycle_popup.winfo_exists():
                self.close_cycle_popup()
                return
            popup = tk.Toplevel(self)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(bg=Colors.dark_card, padx=6, pady=6, bd=1, relief="solid")
            tk.Label(popup, image=image, bg=Colors.dark_card).pack()
            popup.image_ref = image
            x = widget.winfo_rootx() - 120
            y = widget.winfo_rooty() - 320
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

    def toggle_app(self, event=None):
        """Toggle gaze control and sync with main HomePage button."""
        try:
            from UI.pages.home import launch_gaze_app
        except ImportError:
            print("[WARN] Could not import launch_gaze_app dynamically.")
            return

        # Get main window (for syncing with HomePage)
        main_window = self.controller
        home_page = getattr(main_window, "home_page", None)
        if not home_page and hasattr(main_window, "get_page"):
            try:
                home_page = main_window.get_page("HomePage")
            except Exception:
                home_page = None

        if not self.app_running:
            print("[INFO] Tray Start clicked → Starting gaze control.")
            launch_gaze_app(enable_mouse_control=True)
            self.app_running = True
            self.start_button.configure(image=self.stop_icon)
            self.start_label.configure(text="Stop Application")   # ✅ change text

            if home_page:
                home_page.update_gaze_button(True)
        else:
            print("[INFO] Tray Stop clicked → Stopping gaze control.")
            launch_gaze_app(enable_mouse_control=False)
            self.app_running = False
            self.start_button.configure(image=self.start_icon)
            self.start_label.configure(text="Start Application")  # ✅ change text back

            if home_page:
                home_page.update_gaze_button(False)

    def start_move(self, e):
        self.x, self.y = e.x, e.y

    def on_move(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self.x}+{self.winfo_y() + e.y - self.y}")
