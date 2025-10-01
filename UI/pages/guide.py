# UI/pages/guide.py
import os, platform, ctypes
from pathlib import Path
import tkinter as tk

from UI.widgets import RoundedCard, PillButton
from UI.theme import Colors, Fonts
from .base import BasePage

# -------- VLC bootstrap (use bundled runtime) --------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VLC_DIR = PROJECT_ROOT / "third_party" / "vlc"
LIBVLC = VLC_DIR / "libvlc.dll"
PLUGINS = VLC_DIR / "plugins"

if platform.system() == "Windows":
    if LIBVLC.exists():
        try:
            os.add_dll_directory(str(VLC_DIR))
        except Exception:
            pass
        os.environ["PATH"] = str(VLC_DIR) + os.pathsep + os.environ.get("PATH", "")
        os.environ["PYTHON_VLC_LIB_PATH"] = str(LIBVLC)
        os.environ.setdefault("VLC_PLUGIN_PATH", str(PLUGINS))

        print("VLC (guide.py):", LIBVLC, "exists ->", LIBVLC.exists())
        try:
            ctypes.CDLL(str(LIBVLC))
        except OSError as e:
            print("!! ctypes could not load libvlc.dll:", e)
    else:
        print("!! libvlc.dll not found at:", LIBVLC)

import vlc
# -------- end VLC bootstrap --------


class GuideVideoPage(BasePage):
    def __init__(self, parent, controller, guide_video_path: Path,show_skip=True):
        super().__init__(parent, controller)
        self.guide = guide_video_path
        self._is_full = False
        self._muted = False
        self.duration = 0

        # VLC instance
        opts = [
    "--aout=directsound",
    "--no-video-title-show",
    "--no-audio-time-stretch",
    "--quiet",   # suppress logs
]

        print("Starting VLC with options:", opts)
        self.vlc_instance = vlc.Instance(opts)
        if not self.vlc_instance:
            raise RuntimeError("libVLC failed to initialize.")
        self.player = self.vlc_instance.media_player_new()

        # --- Card container ---
        self.card = RoundedCard(
            self.overlay, radius=4, pad=5, bg=Colors.card_bg, tight=False
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center",
                        relwidth=0.92, relheight=0.82)

        # --- Video surface ---
        self.video = tk.Canvas(
            self.card.body, bg=self.card.cget("bg"),
            highlightthickness=0, bd=0
        )
        self.video.pack(fill="both", expand=True)
        self.video.bind("<Configure>", lambda e: self._attach_handle())

        # --- Controls row ---
        ctrl_bg = self.card.cget("bg")
        self.controls = tk.Frame(self.card.body, bg=ctrl_bg)
        self.controls.pack(fill="x", pady=(5, 0))

        # left controls
        left = tk.Frame(self.controls, bg=ctrl_bg)
        left.pack(side="left")
        self.btn_back = tk.Button(left, text="⏪", command=lambda: self._seek_rel(-5),
                                  font=("Segoe UI Symbol", 11), fg="#ffffff",
                                  bg=ctrl_bg, bd=0, cursor="hand2")
        self.btn_back.pack(side="left", padx=4)
        self.btn_play = tk.Button(left, text="▶", command=self._toggle_play,
                                  font=("Segoe UI Symbol", 12, "bold"), fg="#ffffff",
                                  bg=ctrl_bg, bd=0, cursor="hand2")
        self.btn_play.pack(side="left", padx=6)
        self.btn_fwd = tk.Button(left, text="⏩", command=lambda: self._seek_rel(5),
                                 font=("Segoe UI Symbol", 11), fg="#ffffff",
                                 bg=ctrl_bg, bd=0, cursor="hand2")
        self.btn_fwd.pack(side="left", padx=4)

        # progress
        mid = tk.Frame(self.controls, bg=ctrl_bg)
        mid.pack(side="left", fill="x", expand=True, padx=(8, 0))   # no right pad
        self.progress = tk.Canvas(mid, height=10, bg=ctrl_bg,
                                  highlightthickness=0, bd=0)
        self.progress.pack(fill="x")
        self.progress.bind("<Button-1>", self._progress_click)
        self.progress.bind("<B1-Motion>", self._progress_click)
        self.progress.bind("<Configure>", lambda e: self._draw_progress())

        # right controls (volume, fullscreen, skip)
        right = tk.Frame(self.controls, bg=ctrl_bg)
        right.pack(side="right", padx=0)

        self.btn_vol = tk.Button(right, text="🔊", command=self._toggle_mute,
                                 font=("Segoe UI Symbol", 11), fg="#ffffff",
                                 bg=ctrl_bg, bd=0, cursor="hand2")
        self.btn_vol.pack(side="left", padx=(6, 2))

        self.btn_full = tk.Button(right, text="⤢", command=self._toggle_full,
                                  font=("Segoe UI Symbol", 12), fg="#ffffff",
                                  bg=ctrl_bg, bd=0, cursor="hand2")
        self.btn_full.pack(side="left", padx=(6, 2))

        if show_skip:
            self.btn_skip = PillButton(
    right,
    text="SKIP  ⏭",
    command=self._skip_video
)
            self.btn_skip.pack(side="left", padx=(8, 0))   # flush with right edge

        # --- Load video if present ---
        if self.guide and Path(self.guide).exists():
            media = self.vlc_instance.media_new(str(self.guide))
            self.player.set_media(media)
            self.after(200, self._poll_state)
        else:
            ph = tk.Label(self.video, text="( Put guide.mp4 in /assets )",
                          font=Fonts.h3, fg="#ffffff", bg=ctrl_bg)
            ph.pack(expand=True)

    # ---------- VLC hooks ----------
    
    
    
    def _skip_video(self):
        try:
            if self.player and self.player.is_playing():
                self.player.stop()   # stop playback immediately
            # optional: free resources
            # self.player.release()
        except Exception as e:
            print("skip_video error:", e)

        self.controller.show("HomePage")

    def _attach_handle(self):
        try:
            self.video.update_idletasks()
            hwnd = self.video.winfo_id()
            self.player.set_hwnd(hwnd)
            self.player.video_set_scale(0)
            self.player.video_set_aspect_ratio(None)
        except Exception as e:
            print("set_hwnd failed:", e)

    def _poll_state(self):
        try:
            dur_ms = self.player.get_length()
            if dur_ms and dur_ms > 0:
                self.duration = dur_ms // 1000
        except Exception:
            pass

        self._draw_progress()

        if self.player.get_state() == vlc.State.Ended:
            self.controller.show("HomePage")
            return

        self.after(200, self._poll_state)

    # ---------- controls ----------
    def _toggle_play(self):
        st = self.player.get_state()
        if st in (vlc.State.Playing, vlc.State.Buffering):
            self.player.pause()
            self.btn_play.config(text="▶")
        else:
            self.player.play()
            self.btn_play.config(text="❚❚")

    def _seek_rel(self, secs: int):
        if self.duration <= 0: return
        cur = (self.player.get_time() or 0) // 1000
        new = max(0, min(cur + secs, self.duration))
        self.player.set_time(new * 1000)

    def _toggle_mute(self):
        self._muted = not self._muted
        self.player.audio_set_mute(self._muted)
        self.btn_vol.config(text="🔇" if self._muted else "🔊")

    def _toggle_full(self):
        if not self._is_full:
            self.controller.attributes("-fullscreen", True)
            self._is_full = True
            self.controller.bind("<Escape>", lambda e: self._toggle_full())
        else:
            self.controller.attributes("-fullscreen", False)
            self._is_full = False
            self.controller.unbind("<Escape>")

    # ---------- progress ----------
    def _progress_click(self, event):
        if self.duration <= 0: return
        w = max(1, self.progress.winfo_width() - 20)
        x = min(max(10, event.x), w + 10) - 10
        pct = x / w
        self.player.set_time(int(self.duration * 1000 * pct))
        self._draw_progress()

    def _draw_progress(self):
        c = self.progress
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 0 or h <= 0: return
        pad, y = 10, h // 2
        c.create_line(pad, y, w - pad, y, fill="#dbe5f3",
                      width=6, capstyle="round")
        cur_ms = self.player.get_time() or 0
        x = pad if self.duration <= 0 else pad + int((w - 2*pad) *
                                                     (cur_ms / (self.duration * 1000)))
        c.create_line(pad, y, x, y, fill="#ef4444",
                      width=6, capstyle="round")
        c.create_oval(x - 6, y - 6, x + 6, y + 6,
                      fill="#ef4444", outline="#ef4444")

    # ---------- lifecycle ----------
    def on_show(self):
        self.after(50, self._attach_handle)
        try:
            self.player.play()
            self.btn_play.config(text="❚❚")
        except Exception as e:
            print("play() error:", e)
