import tkinter as tk
import threading
from PIL import Image, ImageTk, ImageSequence
import os


class RecordingIndicator:
    _instance = None

    def __init__(self):
        self.window = None
        self.frames = []
        self.label = None
        self.frame_index = 0
        self.animating = False


    def load_gif(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gif_path = os.path.join(script_dir, "..", "assets", "mic.gif")
        gif_path = os.path.abspath(gif_path)


        print("Loading GIF:", gif_path)

        gif = Image.open(gif_path)

        # Load frames
        self.frames = [
            ImageTk.PhotoImage(frame.copy().resize((35, 35)))
            for frame in ImageSequence.Iterator(gif)
        ]

        print("Actual frames in GIF:", len(self.frames))


    def animate(self):
        if not self.animating or not self.window:
            return

        frame = self.frames[self.frame_index]
        self.label.config(image=frame)
        self.frame_index = (self.frame_index + 1) % len(self.frames)

        self.window.after(70, self.animate)  # change speed here

    def show(self):
        if self.window:
            return  # already visible

        self.window = tk.Toplevel()
        self.window.withdraw()   # <-- Prevent flash
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#31A0EB")

        # load GIF frames
        self.load_gif()

        self.label = tk.Label(
            self.window,
            text=" Recording…",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#31A0EB",
            compound="left"
        )
        self.label.pack(padx=10, pady=5)

        # Right middle position
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        win_width = 180
        win_height = 50

        x = screen_width - win_width - 20
        y = (screen_height // 2) - (win_height // 2)

        self.window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        self.window.deiconify()  # <-- Now show

        # Start GIF animation
        self.animating = True
        self.animate()

    def hide(self):
        self.animating = False
        if self.window:
            try:
                # Destroy window IN the Tkinter thread
                self.window.after(0, self.window.destroy)
            except Exception as e:
                print("Error destroying window:", e)
            self.window = None



# Singleton instance
RecordingIndicator._instance = RecordingIndicator()

def show_indicator():
    threading.Thread(target=RecordingIndicator._instance.show, daemon=True).start()

def hide_indicator():
    # No thread needed – hide schedules destroy properly
    RecordingIndicator._instance.hide()


