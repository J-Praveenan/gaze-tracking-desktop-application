import tkinter as tk
from UI.theme import Colors

class BasePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=Colors.bg)
        self.controller = controller
        # wallpaper holder (centered)
        self.bg_label = tk.Label(self, bd=0, bg=Colors.bg)
        self.bg_label.place(relx=0.5, rely=0.5, anchor="center")
        # translucent overlay for content
        self.overlay = tk.Frame(self, bg=Colors.bg_tint)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

    def set_bg(self, photo_img):
        if photo_img is None:
            self.bg_label.config(image="", bg=Colors.bg)
        else:
            self.bg_label.config(image=photo_img, bg=Colors.bg)
            self.bg_label.image = photo_img  # keep ref
        self.bg_label.lower()
        self.overlay.lift()

    def on_show(self):
        pass
