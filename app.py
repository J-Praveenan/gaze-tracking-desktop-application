from pathlib import Path
import traceback
import os, platform
from UI.pages.setup import SetupPage
from UI.pages.apps import AppsPage
from UI.pages.system import SystemPage
from UI.pages.tips import TipsPage
from UI.pages.info import InfoPage
from UI.pages.settings import SettingsPage
from threading import Thread
from voice.voice_typing import run_voice_typing_loop
import gaze_estimation 
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
from UI.pages.home import HomePage
from utils.paths import data_path
from UI.pages.guide import GuideVideoPage

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
        self.configure(bg=Colors.bg)

        apply_base_style(self)

        # Load originals (shared)
        self._bg_raw   = Image.open(BG_IMG_PATH) if BG_IMG_PATH.exists() else None
        self._logo_raw = Image.open(LOGO_IMG_PATH) if LOGO_IMG_PATH.exists() else None

        # Header
        self.header = TitleBar(self, logo_img=self.get_logo(70), title_text=APP_TITLE)
        self.header.pack(fill="x", side="top")

        # Page container
        self.container = tk.Frame(self, bg=Colors.bg)
        self.container.pack(fill="both", expand=True)

        # --- Instantiate pages ---
        self.pages = {}

        # splash / guide / home
        self._add_page(SplashPage, "SplashPage")
        self._add_page(GuideVideoPage, "GuideVideoPage", guide_video_path=GUIDE_MP4)
        self._add_page(HomePage, "HomePage")

        # the other sections used by the sidebar
        self._add_page(SetupPage, "SetupPage")
        self._add_page(AppsPage, "AppsPage")
        self._add_page(SystemPage, "SystemPage")
        self._add_page(TipsPage, "TipsPage")
        self._add_page(InfoPage, "InfoPage")
        self._add_page(SettingsPage, "SettingsPage")

        # keep this line if you want the splash first
        self.show("SplashPage")

    # ------------- shared assets -------------
    def get_logo(self, size: int):
        if not self._logo_raw:
            return None
        img = self._logo_raw.copy().convert("RGBA").resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

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
        self.pages[name].tkraise()
        self.pages[name].on_show()

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
    
    Thread(target=run_voice_typing_loop, daemon=True).start()
    
    # Start gaze tracker (main.py) in background thread
    # threading.Thread(target=gaze_estimation.main, daemon=True).start()
    
    # install Tk callback error reporter
    tk.Tk.report_callback_exception = _report_callback_exception
    
    app = App()
    app.mainloop()
