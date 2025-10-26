from pathlib import Path
import traceback
import os, platform
from UI.pages.setup import SetupPage
from UI.pages.tips import TipsPage
from UI.pages.info import InfoPage
from UI.pages.settings import SettingsPage
from threading import Thread
from voice.voice_typing import run_voice_typing_loop
import gaze_estimation 
from UI.pages.sidebar import Sidebar
import threading
# ...


# ---- VLC bootstrap: use bundled runtime ----


BASE_DIR = Path(__file__).resolve().parent
BUNDLED_VLC = BASE_DIR / "third_party" / "vlc"  # where you copied DLLs and plugins/


import platform, struct
print("Python version:", platform.python_version())
print("Machine type:", platform.machine())
print("Python bitness:", struct.calcsize("P") * 8, "bit")

if platform.system() == "Windows":
    if (BUNDLED_VLC / "libvlc.dll").exists():
        try:
            os.add_dll_directory(str(BUNDLED_VLC))   # make libvlc.dll visible
        except Exception:
            pass
        os.environ.setdefault("VLC_PLUGIN_PATH", str(BUNDLED_VLC / "plugins"))
    else:
        # Helpful debug if files are missing / in the wrong folder
        print("!! Bundled VLC not found at:", BUNDLED_VLC)
        print("   Expected files:", BUNDLED_VLC / "libvlc.dll", "and plugins/ subfolder")
# ---- end VLC bootstrap ----

# in app.py, right after the VLC bootstrap block
print("VLC dir (app.py):", BUNDLED_VLC, (BUNDLED_VLC / "libvlc.dll").exists())

# in UI/pages/guide.py, after you set the directory but before `import vlc`

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from UI.theme import Colors, apply_base_style
from UI.widgets import TitleBar
from UI.pages.splash import SplashPage
from UI.pages.home import HomePage, launch_gaze_app, speak
from utils.paths import data_path
from UI.pages.guide import GuideVideoPage
from UI.pages.gaze_test import GazeTestPage

APP_TITLE = "LOOK TRACK VISION"
BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"

BG_IMG_PATH   = ASSETS / "bg.jpg"
LOGO_IMG_PATH = ASSETS / "eyelogo.jpg"
GUIDE_MP4 = data_path("assets", "guide.mp4")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(1000, 680)
        self.configure(bg=Colors.page_bg)
        self.gaze_running = False  # ✅ Add this line here
        apply_base_style(self)

        # Load originals (shared)
        self._bg_raw   = Image.open(BG_IMG_PATH) if BG_IMG_PATH.exists() else None
        self._logo_raw = Image.open(LOGO_IMG_PATH) if LOGO_IMG_PATH.exists() else None

        # Header
        self.header = TitleBar(self, logo_img=self.get_logo(70), title_text=APP_TITLE,
            on_toggle_gaze=self._handle_global_gaze_toggle)
        self.header.pack(fill="x", side="top")

        # Main frame holds sidebar + content (so we can grid safely)
        main_frame = tk.Frame(self, bg=Colors.page_bg)
        main_frame.pack(fill="both", expand=True)

        # === Layout using grid (inside main_frame) ===
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Sidebar (created once)
        self.sidebar = Sidebar(main_frame, self)
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(20, 10), pady=20)

        # Page container (for right content)
        self.container = tk.Frame(main_frame, bg=Colors.page_bg)
        self.container.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)



        # --- Instantiate pages ---
        self.pages = {}

        # splash / guide / home
        self._add_page(SplashPage, "SplashPage")
        self._add_page(GuideVideoPage, "GuideVideoPage", guide_video_path=GUIDE_MP4)
        self._add_page(HomePage, "HomePage")

        # the other sections used by the sidebar
        self._add_page(SetupPage, "SetupPage")
        self._add_page(GazeTestPage, "GazeTestPage")
        self._add_page(TipsPage, "TipsPage")
        self._add_page(InfoPage, "InfoPage")
        self._add_page(SettingsPage, "SettingsPage")

        # keep this line if you want the splash first
        self.show("SplashPage")
        # === Start background voice listener only in MANUAL mode ===
        


    # ------------- shared assets -------------
    def get_logo(self, size: int):
        if not self._logo_raw:
            return None
        img = self._logo_raw.copy().convert("RGBA").resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    
    def _handle_global_gaze_toggle(self, running: bool):
        """Called by TitleBar or HomePage — controls gaze and syncs both buttons."""
        from UI.pages.home import launch_gaze_app, speak
        from pathlib import Path
        import json

        self.gaze_running = running  # update global state

        # === Read control mode from config ===
        control_mode = "auto"
        try:
            base_dir = Path(__file__).resolve().parent
            config_path = base_dir / "Data" / "configuration.json"
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    control_mode = config.get("control", {}).get("mode", "auto")
        except Exception as e:
            print(f"[WARN] Could not read configuration.json: {e}")

        # === Handle gaze startup/shutdown ===
        if running:
            print(f"[APP] Starting Look Track Vision (mode: {control_mode})")

            if control_mode == "auto":
                # Auto Mode → Start gaze tracking directly
                launch_gaze_app(enable_mouse_control=True)
                speak("Gaze control started.")
            else:
                # Manual Mode → Load gaze system, but wait for voice command
                print("[APP] Manual Control mode active — system in standby, waiting for 'Start gaze control' voice command.")
                launch_gaze_app(enable_mouse_control=False)
                speak("Manual mode enabled. Say 'Start gaze control' to begin gaze tracking.")

                # ✅ Start background voice listener now
                try:
                    from voice.transcription import start_voice_listener_thread
                    print("[APP] Voice listener started (manual mode).")
                    start_voice_listener_thread()
                except Exception as e:
                    print(f"[WARN] Could not start voice listener: {e}")
        else:
            # ✅ Stop gaze in all modes
            print("[APP] Stopping Look Track Vision.")
            launch_gaze_app(enable_mouse_control=False)
            speak("Gaze control stopped.")

    def _sync_gaze_buttons(self):
        """Sync the START/STOP button states across TitleBar and HomePage."""
        # Update TitleBar
        self.header.update_gaze_button(self.gaze_running)

        # Update HomePage if it exists
        home_page = self.pages.get("HomePage")
        if home_page and hasattr(home_page, "update_gaze_button"):
            home_page.update_gaze_button(self.gaze_running)
            

    def get_bg_photo(self, w: int, h: int):
        """Return a PhotoImage that 'covers' the window."""
        if not self._bg_raw:
            return None
        img = self._bg_raw.copy()
        img_ratio = img.width / img.height
        win_ratio = w / max(1, h)
        if win_ratio > img_ratio:
            new_h = h
            new_w = int(h * img_ratio)
        else:
            new_w = w
            new_h = int(w / img_ratio)
        img = img.resize((max(1, new_w), max(1, new_h)), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    # ------------- navigation -------------
    def _add_page(self, PageClass, name: str, **kwargs):
        page = PageClass(parent=self.container, controller=self, **kwargs)
        self.pages[name] = page
        page.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show(self, name: str):
        # raise the requested page
        self.pages[name].tkraise()
        self.pages[name].on_show()

        # Check if this page should hide the sidebar
        if name in ("SplashPage", "GuideVideoPage"):
            # Hide sidebar
            self.sidebar.grid_remove()

            # Set full background to dark mode for splash/guide
            self.configure(bg=Colors.bg)
            self.container.configure(bg=Colors.bg)

            # Also change main frame background
            self.container.master.configure(bg=Colors.bg)  # main_frame
        else:
            # Show sidebar again
            self.sidebar.grid()

            # Restore the light page background for normal pages
            self.configure(bg=Colors.page_bg)
            self.container.configure(bg=Colors.page_bg)
            self.container.master.configure(bg=Colors.page_bg)  # main_frame

            # highlight correct sidebar item
            key = name.lower().replace("page", "")
            self.sidebar.highlight_selected(key)





    # ------------- window resize -------------
    def _on_resize(self, _evt=None):
        w = max(200, self.winfo_width())
        h = max(200, self.winfo_height())
        # update header logo
        self.header.set_logo(self.get_logo(70))
        # tell pages to refresh bg
        bg_photo = self.get_bg_photo(w, h)
        for page in self.pages.values():
            if hasattr(page, "set_bg"):
                page.set_bg(bg_photo)


def _report_callback_exception(self, exc, val, tb):
    """Show full Tk callback errors in the terminal instead of a vague popup."""
    traceback.print_exception(exc, val, tb)

if __name__ == "__main__":
      
    # install Tk callback error reporter
    tk.Tk.report_callback_exception = _report_callback_exception
    
    app = App()
    app.mainloop()
