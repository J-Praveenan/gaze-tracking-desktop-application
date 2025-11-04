import tkinter as tk
from frontend.theme import Colors

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


    def enable_scroll(self, canvas, scroll_frame):
        """Enable scroll only while mouse is over this page's canvas."""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll(_):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_scroll(_):
            canvas.unbind_all("<MouseWheel>")

        # Bind when mouse enters/leaves the page
        for widget in (canvas, scroll_frame, self):
            widget.bind("<Enter>", _bind_scroll)
            widget.bind("<Leave>", _unbind_scroll)

        # Linux scroll events
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
