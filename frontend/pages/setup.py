import os, platform, ctypes, threading
from pathlib import Path
import tkinter as tk

from frontend.theme import Colors, Fonts
from frontend.widgets import RoundedCard, PillButton
from frontend.pages.base import BasePage
from Calibration.Calibration import calibrate_gaze

# -------- VLC bootstrap (auto-load from third_party/vlc) --------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VLC_DIR = PROJECT_ROOT / "third_party" / "vlc"
LIBVLC = VLC_DIR / "libvlc.dll"
LIBVLCCORE = VLC_DIR / "libvlccore.dll"
PLUGINS = VLC_DIR / "plugins"

if platform.system() == "Windows":
    if LIBVLC.exists() and LIBVLCCORE.exists():
        try:
            os.add_dll_directory(str(VLC_DIR))
            ctypes.CDLL(os.path.abspath(str(LIBVLCCORE)))
            ctypes.CDLL(os.path.abspath(str(LIBVLC)))
            os.environ["PATH"] = str(VLC_DIR) + os.pathsep + os.environ.get("PATH", "")
            os.environ["PYTHON_VLC_LIB_PATH"] = str(LIBVLC)
            os.environ["VLC_PLUGIN_PATH"] = str(PLUGINS)
            print(f"✅ Loaded VLC runtime from: {VLC_DIR}")
        except OSError as e:
            print("❌ Could not preload VLC DLLs:", e)
    else:
        print("⚠️ VLC DLLs not found in:", VLC_DIR)
else:
    print("⚠️ Non-Windows system: skipping VLC bootstrap")

# ✅ Import VLC only after bootstrapping
import vlc
# ---------------------------------------------------------------



# -------- SetupPage --------
class SetupPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.overlay.configure(bg=Colors.page_bg)

        self.overlay.grid_rowconfigure(0, weight=1)
        self.overlay.grid_columnconfigure(0, weight=0)
        self.overlay.grid_columnconfigure(1, weight=1)

        # Card container for video player
        card = RoundedCard(self.overlay, radius=18, bg=Colors.dark_card, tight=False)
        card.grid(row=0, column=1, sticky="nsew", padx=(0, 20))

        # --- Video canvas ---
        self.video_canvas = tk.Canvas(
            card.body, bg=Colors.dark_card, highlightthickness=0, bd=0
        )
        self.video_canvas.pack(fill="both", expand=True)
        
        
        # --- Placeholder image before video plays ---
        thumb_path = PROJECT_ROOT / "assets" / "thumbnail.ico"
        if thumb_path.exists():
            self.thumb_image = tk.PhotoImage(file=str(thumb_path))
            self.preview_label = tk.Label(
    self.video_canvas,
    image=self.thumb_image,
    bg=Colors.dark_card,
    borderwidth=0
)
            self.preview_label.image = self.thumb_image  # keep a reference
            # Center thumbnail, smaller size, not full fill
            self.preview_label.place(relx=0.5, rely=0.45, anchor="center")


        else:
            # fallback text if image missing
            self.preview_label = tk.Label(
                self.video_canvas,
                text="Calibration Guide Ready",
                font=F("h3", ("Segoe UI", 14, "bold")),
                fg="#ffffff",
                bg=Colors.dark_card
            )
            self.preview_label.pack(expand=True)


        # --- Controls row ---
        # --- Controls row (responsive layout) ---
        ctrl_frame = tk.Frame(card.body, bg=Colors.dark_card)
        ctrl_frame.pack(fill="x", pady=(5, 0))

        # Configure adaptive grid
        ctrl_frame.columnconfigure(0, weight=0)  # play button
        ctrl_frame.columnconfigure(1, weight=1)  # progress bar expands
        ctrl_frame.columnconfigure(2, weight=0)  # right control buttons

        # ▶ Playback button
        self.btn_play = tk.Button(
            ctrl_frame,
            text="▶",
            font=("Segoe UI Symbol", 12, "bold"),
            fg="#ffffff",
            bg=Colors.dark_card,
            bd=0,
            cursor="hand2",
            command=self._toggle_play,
        )
        self.btn_play.grid(row=0, column=0, sticky="w", padx=8, pady=4)

        # Progress bar expands dynamically
        self.progress = tk.Canvas(
            ctrl_frame, height=10, bg=Colors.dark_card, highlightthickness=0
        )
        self.progress.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.progress.bind("<Button-1>", self._progress_click)
        self.progress.bind("<B1-Motion>", self._progress_click)
        self.progress.bind("<Configure>", lambda e: self._draw_progress())

        # Right control section (also grid-based)
        right_ctrl = tk.Frame(ctrl_frame, bg=Colors.dark_card)
        right_ctrl.grid(row=0, column=2, sticky="e", padx=8, pady=4)
        right_ctrl.columnconfigure(0, weight=0)
        right_ctrl.columnconfigure(1, weight=0)
        right_ctrl.columnconfigure(2, weight=1)

        # 🔇 Volume + Fullscreen + Start Calibration buttons
        self.btn_vol = tk.Button(
            right_ctrl,
            text="🔊",
            font=("Segoe UI Symbol", 11),
            fg="#ffffff",
            bg=Colors.dark_card,
            bd=0,
            cursor="hand2",
            command=self._toggle_mute,
        )
        self.btn_vol.grid(row=0, column=0, padx=4)

        self.btn_full = tk.Button(
            right_ctrl,
            text="⤢",
            font=("Segoe UI Symbol", 11),
            fg="#ffffff",
            bg=Colors.dark_card,
            bd=0,
            cursor="hand2",
            command=self._toggle_fullscreen,
        )
        self.btn_full.grid(row=0, column=1, padx=4)

        self.start_btn = PillButton(
            right_ctrl, text="START CALIBRATION", command=self._start_calibration
        )
        self.start_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))


        # Progress bar


        # --- VLC Setup ---
        guide_path = PROJECT_ROOT / "assets" / "calibration.mp4"
        self.guide_video = str(guide_path)
        self._is_full = False
        self._muted = False
        self.duration = 0

        opts = ["--no-video-title-show", "--no-audio-time-stretch", "--quiet"]
        self.vlc_instance = vlc.Instance(opts)
        self.player = self.vlc_instance.media_player_new()

        if Path(self.guide_video).exists():
            media = self.vlc_instance.media_new(self.guide_video)
            self.player.set_media(media)
            self.after(100, self._attach_handle)
            self.after(200, self._poll_state)
        else:
            ph = tk.Label(
                self.video_canvas,
                text="(start-up-video.mp4 not found in /assets)",
                font=F("h3", ("Segoe UI", 14, "bold")),
                fg="#fff",
                bg=Colors.dark_card,
            )
            ph.pack(expand=True)

    # ---------- Calibration ----------
        # ---------- Calibration ----------
    def _start_calibration(self):
        import cv2
        import json
        from pathlib import Path

        print("[INFO] Starting calibration mode...")

        # 📁 Load selected camera index from configuration.json
        ROOT = Path(__file__).resolve().parents[2]
        config_path = ROOT / "Data" / "configuration.json"
        camera_index = 0  # default camera

        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    camera_index = config.get("camera", {}).get("index", 0)
        except Exception as e:
            print("⚠️ Failed to read config:", e)

        # 🎥 Try to open the selected camera
        cap = cv2.VideoCapture(camera_index)
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            # 🚫 Camera not working → show popup
            self._show_camera_error()
            print("[ERROR] Wrong camera selected.")
            return  # stop execution here

        # ✅ Camera works → Start calibration thread
        print("[OK] Camera working, starting calibration...")
        threading.Thread(target=calibrate_gaze, daemon=True).start()
        
        
    def _show_camera_error(self):
        """Show popup when the selected camera is not available."""
        popup = tk.Toplevel(self)
        popup.title("Camera Error")
        popup.configure(bg=Colors.dark_card)

        # Center popup dynamically on screen
        popup_width, popup_height = 480, 180
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = int((screen_w / 2) - (popup_width / 2))
        y = int((screen_h / 2) - (popup_height / 2))
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        popup.resizable(False, False)

        # Heading
        tk.Label(
            popup,
            text="Camera Not Available!",
            fg="white", bg=Colors.dark_card,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(20, 10))

        # Instruction text
        tk.Label(
            popup,
            text="You are selecting the wrong camera option.\n"
                 "Go to the Settings option and select the correct camera.",
            fg="#e5e7eb", bg=Colors.dark_card,
            font=("Segoe UI", 10),
            justify="center"
        ).pack(pady=(0, 20))

        # OK button
        tk.Button(
            popup,
            text="OK",
            command=popup.destroy,
            bg="#ef4444",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            width=6,
            cursor="hand2"
        ).pack(pady=(0, 12))



    # ---------- VLC Controls ----------
    def _attach_handle(self):
        try:
            self.video_canvas.update_idletasks()
            hwnd = self.video_canvas.winfo_id()
            self.player.set_hwnd(hwnd)
            self.player.video_set_scale(0)
        except Exception as e:
            print("Attach handle failed:", e)

    def _toggle_play(self):
        state = self.player.get_state()
        try:
            if state in (vlc.State.Playing, vlc.State.Buffering):
                self.player.pause()
                self.btn_play.config(text="▶")
            else:
                if hasattr(self, "preview_label"):
                    self.preview_label.destroy()

                self.player.play()
                self.btn_play.config(text="❚❚")
        except Exception as e:
            print("toggle_play error:", e)

    def _toggle_mute(self):
        self._muted = not self._muted
        self.player.audio_set_mute(self._muted)
        self.btn_vol.config(text="🔇" if self._muted else "🔊")

    def _toggle_fullscreen(self):
        if not self._is_full:
            self.controller.attributes("-fullscreen", True)
            self._is_full = True
            self.controller.bind("<Escape>", lambda e: self._toggle_fullscreen())
        else:
            self.controller.attributes("-fullscreen", False)
            self._is_full = False
            self.controller.unbind("<Escape>")

    def _progress_click(self, event):
        if self.duration <= 0:
            return
        w = max(1, self.progress.winfo_width() - 20)
        x = min(max(10, event.x), w + 10) - 10
        pct = x / w
        self.player.set_time(int(self.duration * 1000 * pct))
        self._draw_progress()

    def _draw_progress(self):
        c = self.progress
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 0 or h <= 0:
            return
        pad, y = 10, h // 2
        c.create_line(pad, y, w - pad, y, fill="#dbe5f3", width=6, capstyle="round")
        cur_ms = self.player.get_time() or 0
        if self.duration > 0:
            x = pad + int((w - 2 * pad) * (cur_ms / (self.duration * 1000)))
            c.create_line(pad, y, x, y, fill="#ef4444", width=6, capstyle="round")
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill="#ef4444", outline="#ef4444")

    def _poll_state(self):
        try:
            dur_ms = self.player.get_length()
            if dur_ms > 0:
                self.duration = dur_ms // 1000
        except Exception:
            pass
        self._draw_progress()
        self.after(200, self._poll_state)
