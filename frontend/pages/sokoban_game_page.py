import tkinter as tk
from tkinter import ttk
from frontend.theme import Colors
import os, sys, subprocess
from itertools import count
from PIL import Image, ImageTk

class SokobanGamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=Colors.bg)
        self.controller = controller

        # Title
        tk.Label(
            self,
            text="Sokoban Game",
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg=Colors.bg
        ).pack(pady=20)

        tk.Label(
            self,
            text="Select a Level to Start Playing",
            font=("Segoe UI", 12),
            fg="#cccccc",
            bg=Colors.bg
        ).pack(pady=5)

        # Container for grid
        grid_frame = tk.Frame(self, bg=Colors.bg)
        grid_frame.pack(pady=20)

        self.create_level_grid(grid_frame)
        
        # --- Add Sokoban animated GIF below levels ---
        gif_path = os.path.join(os.path.dirname(__file__), "../../assets/sokoban.gif")

        if os.path.exists(gif_path):
            try:
                frames = []
                with Image.open(gif_path) as im:
                    for frame in range(im.n_frames):
                        im.seek(frame)
                        frame_image = ImageTk.PhotoImage(im.copy().resize((500, 250)))  # Resize if needed
                        frames.append(frame_image)

                gif_label = tk.Label(self, bg=Colors.bg)
                gif_label.pack(pady=15)

                def update_gif(index=0):
                    frame = frames[index]
                    gif_label.configure(image=frame)
                    gif_label.image = frame
                    self.after(300, update_gif, (index + 1) % len(frames))  # 100 ms per frame

                update_gif()  # Start animation
            except Exception as e:
                print("⚠️ Could not load Sokoban GIF:", e)
        else:
            print("⚠️ Sokoban GIF not found at:", gif_path)


    def create_level_grid(self, frame):
        """Creates a clickable grid of level buttons (1–52)."""
        num_levels = 15
        cols = 5  # 8 columns per row
        btn_width = 10
        btn_height = 4
        font_size = 10  # increased font size

        for i in range(1, num_levels + 1):
            
            btn = tk.Button(
                frame,
                text=f"Level {i}",
                width=btn_width,
                height=btn_height,
                font=("Segoe UI", font_size, "bold"),
                bg="#2b3947",
                fg="white",
                activebackground="#FFFFFF",
                cursor="hand2",
                relief="solid",
                bd=0,
                highlightthickness=0,           # border thickness
                highlightbackground="#FFFFFF",    # border color (normal)
                highlightcolor="#FFFFFF",         # border color (when focused)
                command=lambda lvl=i: self.launch_level(lvl)
            )

            # Bind hover events (change background color)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#31A0EB", bd=2, relief="solid", highlightbackground="#31A0EB"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#2b3947", bd=2, relief="solid", highlightbackground="#FFFFFF"))


            r, c = divmod(i - 1, cols)
            btn.grid(row=r, column=c, padx=10, pady=10)


    def launch_level(self, level):
        """Launch the selected Sokoban level in a new Pygame window."""
        try:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
            sokoban_path = os.path.join(root_dir, "frontend", "sokoban", "sokoban.py")

            print(f"🎮 Launching Sokoban Level {level}...")

            # Pass the level number as a command-line argument
            subprocess.Popen([sys.executable, sokoban_path, str(level)], shell=True)
        except Exception as e:
            print("Error launching Sokoban:", e)

    def on_show(self):
        """Called when the page is displayed."""
        pass
