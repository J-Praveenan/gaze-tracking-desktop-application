# utils/paths.py
import sys
from pathlib import Path

def app_path() -> Path:
    if getattr(sys, "frozen", False):                 # PyInstaller EXE
        return Path(sys._MEIPASS)                    # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent     # adjust if you move this file

def data_path(*parts) -> Path:
    return app_path().joinpath(*parts)
