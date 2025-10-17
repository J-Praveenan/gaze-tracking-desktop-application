import tkinter as tk
from UI.theme import Colors, Fonts

def F(name, default):
    return getattr(Fonts, name, default)


class InstructionTray(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Look Track Vision - Instructions")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=Colors.dark_card)

        # === Base dimensions ===
        width = 600
        height = 260  # increased to show all items clearly

        # === Calculate bottom-right position ===
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = screen_w - width - 30
        y = screen_h - height - 60
        self.geometry(f"{width}x{height}+{x}+{y}")

        # === Tray Header ===
        header = tk.Frame(self, bg=Colors.dark_card)
        header.pack(fill="x", pady=(6, 4))
        tk.Label(
            header, text="👁 Eye & Blink Controls",
            fg="white", bg=Colors.dark_card,
            font=F("h2b", ("Segoe UI", 11, "bold"))
        ).pack(side="left", padx=(12, 0))

        # === Scrollable content (if screen smaller) ===
        canvas = tk.Canvas(self, bg=Colors.dark_card, highlightthickness=0)
        scroll_y = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=Colors.dark_card)

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_frame_configure)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=(0, 10))
        scroll_y.pack(side="right", fill="y")

        # === Instructions ===
        instructions = [
            ("👀", "Eye Movement", "Pointer moves in the direction you look."),
            ("🎯", "App Open", "Pointer starts at the center when the app launches."),
            ("✨", "Both Eyes Blink", "Cycles pointer position."),
            ("👁️", "Left Eye Blink", "Performs a Left Click."),
            ("👁️", "Right Eye Blink", "Performs a Right Click."),
            ("😴", "Long Blink (>2s)", "Activates Scroll Mode — look up/down to scroll."),
        ]

        for i, (icon, label, desc) in enumerate(instructions):
            row = tk.Frame(frame, bg=Colors.dark_card)
            row.pack(fill="x", pady=2)
            tk.Label(
                row, text=f"{icon} {label}", width=22,
                anchor="w", fg="white", bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10, "bold"))
            ).pack(side="left", padx=(4, 4))
            tk.Label(
                row, text=desc,
                anchor="w", fg="#d1d5db", bg=Colors.dark_card,
                font=F("body", ("Segoe UI", 10)), wraplength=340, justify="left"
            ).pack(side="left", padx=(0, 10))

        # === Close Button ===
        close_btn = tk.Button(
            self, text="×", command=self.destroy,
            bg="#ef4444", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", width=3
        )
        close_btn.place(relx=0.97, rely=0.05, anchor="ne")

        # === Make draggable ===
        header.bind("<ButtonPress-1>", self.start_move)
        header.bind("<B1-Motion>", self.on_move)

    # === Drag support ===
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")
