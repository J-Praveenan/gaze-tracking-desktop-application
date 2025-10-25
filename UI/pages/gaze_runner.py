# UI/pages/gaze_runner.pyimport sys
import sys
from pathlib import Path

# --- Ensure project root is in sys.path ---
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


import cv2, dlib, numpy as np, pyautogui, time, json, winsound, threading
from imutils import face_utils
import mediapipe as mp
from pathlib import Path


from Voice_Model.voice_autodictation import start_voice_autodictation
from voice.voice_typing import run_voice_typing_loop
import winsound
import pyautogui
import time
import win32gui
import json
import threading
import speech_recognition as sr
import pyttsx3
import os, sys
import webbrowser
from json import JSONDecodeError
from typing import Tuple
import threading
from utils.common import speak_action_confirmation
import tkinter as tk
import threading
from UI.theme import Colors, Fonts
from UI.widgets import RoundedCard, PillButton
from UI.pages.base import BasePage
from UI.pages.sidebar import Sidebar

from tensorflow.keras.models import load_model

from utils.common import speak_action_confirmation, speak


# Disable TensorFlow imports to prevent protobuf errors
import os, sys

# 🧠 Disable TensorFlow import *only* inside MediaPipe
os.environ["MEDIAPIPE_DISABLE_TF_IMPORT"] = "1"

import mediapipe as mp

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
except ImportError:
    print("⚠️ TensorFlow not found — please install it with `pip install tensorflow`")
    raise


class HeadPoseEstimator:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

    def estimate(self, frame):
        """Estimate head pose, draw overlay, and return (image, direction)."""
        start = time.time()
        image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.face_mesh.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        direction = "Forward"  # default if no detection

        img_h, img_w, _ = image.shape
        face_3d, face_2d = [], []

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx in [33, 263, 1, 61, 291, 199]:
                        if idx == 1:
                            nose_2d = (lm.x * img_w, lm.y * img_h)
                            nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 3000)
                        x, y = int(lm.x * img_w), int(lm.y * img_h)
                        face_2d.append([x, y])
                        face_3d.append([x, y, lm.z])

                face_2d = np.array(face_2d, dtype=np.float64)
                face_3d = np.array(face_3d, dtype=np.float64)
                focal_length = img_w
                cam_matrix = np.array([
                    [focal_length, 0, img_h / 2],
                    [0, focal_length, img_w / 2],
                    [0, 0, 1]
                ])
                dist_matrix = np.zeros((4, 1), dtype=np.float64)
                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
                rmat, _ = cv2.Rodrigues(rot_vec)
                angles, *_ = cv2.RQDecomp3x3(rmat)
                x, y, z = [a * 360 for a in angles]

                # classify direction
                if y < -12:
                    direction = "Left"
                elif y > 12:
                    direction = "Right"
                elif x < -12:
                    direction = "Down"
                elif x > 14:
                    direction = "Up"
                else:
                    direction = "Forward"

                # draw annotations
                # cv2.putText(image, direction, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

        return image, direction


# ==== Load thresholds from JSON ====
threshold_path = r"E:\FinalYearProject\GazeTrackingModel\GazeTrackingSystem\Data\threshold.json"

if not os.path.exists(threshold_path):
    raise FileNotFoundError("⚠️ Threshold file not found. Please run calibration first!")

with open(threshold_path, "r") as f:
    thresholds = json.load(f)
    
    
    
# ---- Global control flag ----
RUN_GAZE = False
RUN_GAZE_LOCK = threading.Lock()

# Add this
SMOOTHER_STOP = threading.Event()
stop_signal = threading.Event()

# main.py (simplified snippet)
# global reference to the Tkinter app
ui_app = None

# ---- Control Mode ----
SCROLL_MODE = False

# ---- Cursor smoother globals ----
SMOOTH_HZ = 120                # how often to update the cursor
SMOOTH_ALPHA = 0.22            # 0..1, higher = snappier, lower = smoother
_target_pos = None             # (x, y)
_smoother_started = False


# ---- Cursor move gating ----
MOVE_COOLDOWN_SEC = 0.08
_last_cursor_move_ts = 0.0   # initialize globally


# ---- Click globals ----
CLICK_COOLDOWN_SEC = 0.5   # debounce interval for clicks
_last_click_ts = 0.0       # last click timestamp
_left_wink_start = None
_right_wink_start = None
left_click_count = 0
right_click_count = 0
_last_click_flash_until = 0.0
_last_click_side = None

_last_wink_time = 0.0
WINK_SUPPRESS_SEC = 0.4   # 0.5 seconds after a wink, ignore gaze updates

# ---- Anchor globals ----
ANCHOR_MARGIN_PX = 24       # keep off the exact screen edge
ANCHOR_ORDER = ("center", "left","center", "right","top","center","bottom")  # cycle order
_anchor_points = []
_anchor_idx = 0

# Determine if we are running in integrated Tkinter mode
INTEGRATED_UI = "ui_app" in globals() and ui_app is not None


class GazeSession:
    def __init__(self, enable_mouse_control=False, show_video=True):
        self.enable_mouse_control = enable_mouse_control
        self.show_video = show_video
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            print("[INFO] Gaze session already running.")
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            print(f"[INFO] Starting Gaze Session (mouse_control={self.enable_mouse_control}, video={self.show_video})")
            # ⬇️ Move your current `main()` body logic here ⬇️
            main(enable_mouse_control=self.enable_mouse_control, show_video=self.show_video, external_stop=self.stop_event)
        except Exception as e:
            print("[ERROR] Gaze session crashed:", e)

    def stop(self):
        print("[INFO] Stopping Gaze Session")
        RUN_GAZE = False
        self.stop_event.set()


def _right_click_debounced():
    """Trigger a single right-click with debounce."""
    global _last_click_ts, right_click_count, _last_click_flash_until, _last_click_side
    now = time.time()
    if now - _last_click_ts < CLICK_COOLDOWN_SEC:
        return
    _last_click_ts = now
    pyautogui.click(button="right")

    # record for UI
    right_click_count += 1
    _last_click_side = "right"
    _last_click_flash_until = time.time() + 0.6  # flash for 0.6s



def _double_click_debounced(interval=0.15):
    global _last_click_ts, left_click_count, _last_click_flash_until, _last_click_side
    now = time.time()
    if now - _last_click_ts < CLICK_COOLDOWN_SEC:
        return
    _last_click_ts = now
    pyautogui.click(clicks=2, interval=interval, button="left")  # double-click
    pyautogui.press('enter')
    left_click_count += 1
    _last_click_side = "left_dbl"
    _last_click_flash_until = time.time() + 0.6




def toggle_scroll_mode():
    """Toggle between cursor move and scroll modes."""
    global SCROLL_MODE
    SCROLL_MODE = not SCROLL_MODE
    mode = "🧾 Scroll Mode" if SCROLL_MODE else "🖱️ Cursor Mode"
    if mode == "🖱️ Cursor Mode":
        speak_action_confirmation("Cursor mode is activated now")
    else:
        speak_action_confirmation("Scroll mode is activated now")
    print(f"[MODE SWITCHED] {mode}")
    winsound.Beep(1000 if SCROLL_MODE else 700, 150)


def _start_cursor_smoother():
        global _smoother_started, _target_pos, SMOOTHER_STOP
        if _smoother_started:
            return
        _smoother_started = True

        # init target at current cursor
        x, y = pyautogui.position()
        _target_pos = (x, y)
        
        SMOOTHER_STOP.clear()  # reset stop signal before starting

        def _loop():
            period = 1.0 / SMOOTH_HZ
            while not SMOOTHER_STOP.is_set():
                try:
                    cx, cy = pyautogui.position()
                    tx, ty = _target_pos
                    # exponential smoothing (lerp)
                    nx = cx + (tx - cx) * SMOOTH_ALPHA
                    ny = cy + (ty - cy) * SMOOTH_ALPHA

                    # ✅ Clamp cursor within screen bounds
                    sw, sh = pyautogui.size()
                    nx = max(0, min(nx, sw - 2))
                    ny = max(0, min(ny, sh - 2))

                    pyautogui.moveTo(nx, ny, duration=0)
                except Exception:
                    pass
                time.sleep(period)

            print("[INFO] Cursor smoother stopped.")
            global _smoother_started
            _smoother_started = False


        threading.Thread(target=_loop, daemon=True).start()


def main(enable_mouse_control=False, show_video=False, external_stop=None):
    global left_blink_count, right_blink_count, both_blink_count
    left_blink_count = 0
    right_blink_count = 0
    both_blink_count = 0
    
    scroll_blink_start = None
    scroll_blink_active = False

    global _last_wink_time  # ✅ add this line
    global RUN_GAZE, SMOOTHER_STOP
    

    SMOOTHER_STOP.clear()
    
    global stop_signal
    stop_signal.clear()  # ✅ reset stop event before starting new session

   
    # 🟩 Start gaze control
    with RUN_GAZE_LOCK:
        RUN_GAZE = True
    print("[INFO] Starting gaze control.")
    
    if not enable_mouse_control:
        print("[INFO] Running in TEST MODE (no mouse control).")
    else:
        print("[INFO] Running in FULL CONTROL MODE (mouse enabled).")

    
    # ===== THEME (approximate to your 2nd screenshot; tweak hex to match exactly) =====
    def _hex(h):  # hex -> BGR tuple for OpenCV
        h = h.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (b, g, r)

    COL = {
        # deep teal page background, light bluish cards, brand blue accent
        "bg":      _hex("#103A43"),
        "card":    _hex("#E8EFF8"),
        "card2":   _hex("#DFE7F3"),
        "text":    _hex("#0E1116"),
        "muted":   _hex("#6B7B8C"),
        "accent":  _hex("#5D7BEA"),   # buttons/badges
        "accent2": _hex("#E85D7B"),   # progress / secondary
        "shadow":  (0, 0, 0),
    }


    def _rounded_rect_mask(h, w, radius):
        mask = np.zeros((h, w), np.uint8)
        cv2.rectangle(mask, (radius,0), (w-radius, h), 255, -1)
        cv2.rectangle(mask, (0,radius), (w, h-radius), 255, -1)
        for x, y in [(radius, radius), (w-radius-1, radius), (radius, h-radius-1), (w-radius-1, h-radius-1)]:
            cv2.circle(mask, (x,y), radius, 255, -1)
        return mask

    def draw_card(canvas: np.ndarray, x: int, y: int, w: int, h: int,
                radius: int = 16, color=COL["card"], shadow=True):
        """Draw a rounded 'material' card with optional soft shadow."""
        if shadow:
            pad = 12
            shadow_img = np.zeros_like(canvas)
            cv2.rectangle(shadow_img, (x+pad, y+pad), (x+w+pad, y+h+pad), COL["shadow"], -1)
            shadow_img = cv2.GaussianBlur(shadow_img, (21,21), 18)
            canvas[:] = cv2.addWeighted(canvas, 1.0, shadow_img, 0.35, 0)

        card = np.zeros((h, w, 3), np.uint8)
        mask = _rounded_rect_mask(h, w, radius)
        card[:] = color
        roi = canvas[y:y+h, x:x+w]
        card = np.where(mask[...,None]==255, card, roi)
        canvas[y:y+h, x:x+w] = card

    def put_text(img, text, org, scale=0.7, color=COL["text"], weight=1, align="left"):
        th = weight
        font = cv2.FONT_HERSHEY_DUPLEX  
        size, _ = cv2.getTextSize(text, font, scale, th)
        (x, y) = org
        if align == "center":
            x = int(x - size[0]//2)
        elif align == "right":
            x = int(x - size[0])
        cv2.putText(img, text, (x, y), font, scale, color, th, cv2.LINE_AA)

    def draw_badge(img, text, x, y, pad=8, radius=12, fg=COL["text"], bg=COL["accent"]):
        size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        w, h = size[0] + pad*2, size[1] + pad*2
        draw_card(img, x, y, w, h, radius=radius, color=bg, shadow=False)
        put_text(img, text, (x+pad, y+h-pad-2), scale=0.6, color=fg, weight=1)

    def draw_progress(img, x, y, w, h, pct, radius=10, fg=COL["accent2"], bg=COL["card2"]):
        draw_card(img, x, y, w, h, radius=radius, color=bg, shadow=False)
        fill = max(0, min(w, int(w * pct)))
        if fill > 0:
            draw_card(img, x, y, fill, h, radius=radius, color=fg, shadow=False)
            
            
            


    ROOT = Path(__file__).resolve().parents[2]   # project root
    THRESH_FILE = ROOT / "Data" / "gaze_thresholds.json"
    CLASS_LABELS = ROOT / "Models" / "class_labels.json"


    with open(THRESH_FILE, "r", encoding="utf-8") as f:
            thresholds = json.load(f)

    # LEFT_THRESHOLD = thresholds["LEFT_THRESHOLD"] + 1
    # RIGHT_THRESHOLD = thresholds["RIGHT_THRESHOLD"] - 1
    
    # LEFT_THRESHOLD = thresholds["LEFT_THRESHOLD"]
    # RIGHT_THRESHOLD = thresholds["RIGHT_THRESHOLD"]
    
    # UP_THRESHOLD = thresholds["UP_THRESHOLD"]
    # DOWN_THRESHOLD = thresholds["DOWN_THRESHOLD"] 
    
    # New Threshold values ============================================
    LEFT_EYE_LEFT_DIRECTION_THRESHOLD = thresholds["LEFT_EYE_LEFT_DIRECTION_THRESHOLD"]
    RIGHT_EYE_LEFT_DIRECTION_THRESHOLD = thresholds["RIGHT_EYE_LEFT_DIRECTION_THRESHOLD"]
    LEFT_EYE_RIGHT_DIRECTION_THRESHOLD = thresholds["LEFT_EYE_RIGHT_DIRECTION_THRESHOLD"]
    RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD = thresholds["RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD"]
    LEFT_EYE_UP_DIRECTION_THRESHOLD = thresholds["LEFT_EYE_UP_DIRECTION_THRESHOLD"]             # + 0.0005
    RIGHT_EYE_UP_DIRECTION_THRESHOLD = thresholds["RIGHT_EYE_UP_DIRECTION_THRESHOLD"]           # + 0.0005
    LEFT_EYE_DOWN_DIRECTION_THRESHOLD = thresholds["LEFT_EYE_DOWN_DIRECTION_THRESHOLD"]         # - 0.005
    RIGHT_EYE_DOWN_DIRECTION_THRESHOLD = thresholds["RIGHT_EYE_DOWN_DIRECTION_THRESHOLD"]       # - 0.005

    def click_on_blink():
        global _last_click_ts
        now = time.time()
        if now - _last_click_ts < CLICK_COOLDOWN_SEC:
            return
        _last_click_ts = now
        x, y = pyautogui.position()
        pyautogui.click(x, y)
        
        
        
    # --- Gaze suppression after blinks/winks ---
    SUPPRESS_AFTER_BLINK_SEC = 0.15   # small quiet period after any wink/long-blink
    _suppress_until_ts = 0.0          # timestamp; while now < this, don't predict



    # ====== Mouse control settings ======
    CURSOR_STEP_PX = 40         # how far to move per command (tune this)
    CURSOR_MOVE_DURATION = 0.05 # slight easing; set 0 for instant
    ACCURACY_GATE = 65          # only move when model confidence >= this



    # ===== Smooth cursor controller =====
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0


    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    
        
    # --- Long-blink tuning ---

    # --- Wink & long-blink tuning (adjust to taste) ---
    EAR_CLOSED = 0.18           # eye considered closed below this
    EAR_OPEN_HYST = 0.16        # must be clearly open above this
    WINK_OPEN_MARGIN = 0.02     # the OTHER eye must be this much more open
    WINK_MIN_SEC = 0.08        # ignore micro twitches
    WINK_MAX_SEC = 1.20         # long holds won't count as a wink

    LONG_BLINK_SEC = 1
    # both eyes closed for this long → warp
    LONG_BLINK_COOLDOWN = 0.6   # don't fire twice back-to-back


    # state for winks / long-blink
    _left_wink_start = None
    _right_wink_start = None
    long_blink_start = None
    long_blink_armed = True
    long_blink_cooldown_until = 0.0


    def _compute_anchors():
        sw, sh = pyautogui.size()
        m = ANCHOR_MARGIN_PX
        return {
            "left":   (m,        sh // 2),
            "top":    (sw // 2,  m),
            "right":  (sw - m,   sh // 2),
            "bottom": (sw // 2,  sh - m),
            "center": (sw // 2,  sh // 2),  # include if you want it in the cycle
        }

    _anchor_idx = 0
    def _warp_to_next_anchor():
        """Recompute anchors each time in case resolution changed; then warp."""
        global _anchor_idx, _target_pos
        anchors = _compute_anchors()
        cycle = [anchors[name] for name in ANCHOR_ORDER]
        pos = cycle[_anchor_idx % len(cycle)]
        _anchor_idx += 1
        _target_pos = pos                 # tell the smoother
        pyautogui.moveTo(*pos, duration=0)



    _anchor_points = _compute_anchors()

    # ===== UI sizing =====
    UI_W = 1600        # overall canvas width  (↑ this to make everything wider)
    UI_H = 950         # overall canvas height
    TITLE_BAR_H = 68   # height of the top title bar
    STRIP_H = 120      # height of the strip above video
    MARGIN_X = 44      # left/right margin around content

    MARGIN_Y = 40      # top/bottom margin around content

    # Optional: app icon in the title bar (PNG supported, with alpha)
    ICON_PATH = (ROOT / "Assets" / "logo.png")  # <-- put your icon here
    _icon_rgba = None
    if ICON_PATH.exists():
        _icon_rgba = cv2.imread(str(ICON_PATH), cv2.IMREAD_UNCHANGED)

    def _paste_rgba(dst, rgba, x, y, w=None, h=None, radius=None):
        """
        Paste an RGBA PNG onto BGR canvas with alpha blending. Optionally resize and
        round its corners (radius in px).
        """
        if rgba is None:
            return
        img = rgba.copy()
        if w and h:
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)

        if img.shape[2] == 3:
            # no alpha channel; synthesize opaque
            bgr = img
            alpha = np.full((img.shape[0], img.shape[1], 1), 255, np.uint8)
            img = np.concatenate([bgr, alpha], axis=2)

        b, g, r, a = cv2.split(img)


        if radius:
            # rounded alpha
            mask = np.zeros_like(a)
            cv2.rectangle(mask, (radius,0), (mask.shape[1]-radius, mask.shape[0]), 255, -1)
            cv2.rectangle(mask, (0,radius), (mask.shape[1], mask.shape[0]-radius), 255, -1)
            for cx, cy in [(radius, radius),
                        (mask.shape[1]-radius-1, radius),
                        (radius, mask.shape[0]-radius-1),
                        (mask.shape[1]-radius-1, mask.shape[0]-radius-1)]:
                cv2.circle(mask, (cx, cy), radius, 255, -1)
            a = cv2.bitwise_and(a, mask)

        # destination ROI
        h0, w0 = a.shape
        roi = dst[y:y+h0, x:x+w0]

        # blend
        alpha_f = (a.astype(float) / 255.0)[..., None]
        bgr = cv2.merge([b, g, r]).astype(float)
        blended = alpha_f * bgr + (1 - alpha_f) * roi.astype(float)
        dst[y:y+h0, x:x+w0] = blended.astype(np.uint8)



    # ===== Wink (single-eye blink) → click =====
    CLICK_COOLDOWN_SEC = 0.5     # reuse/adjust
    WINK_MIN_SEC = 0.08  #0.08          # valid wink duration window
    WINK_MAX_SEC = 1.20
    WINK_OPEN_MARGIN = 0.04      # other eye must be clearly open

    _last_click_ts = 0.0
    _left_wink_start = None
    _right_wink_start = None

    def _click_debounced(button="left"):
        global _last_click_ts, left_click_count, right_click_count, _last_click_flash_until, _last_click_side
        now = time.time()
        if now - _last_click_ts < CLICK_COOLDOWN_SEC:
            return
        _last_click_ts = now
        pyautogui.click(button=button)

        # record for UI
        if button == "left":
            left_click_count += 1
            _last_click_side = "left"
        else:
            right_click_count += 1
            _last_click_side = "right"
        _last_click_flash_until = time.time() + 0.6  # flash for 0.6s
        
    def _double_click_debounced(interval=0.15):
        global _last_click_ts, left_click_count, _last_click_flash_until, _last_click_side
        now = time.time()
        if now - _last_click_ts < CLICK_COOLDOWN_SEC:
            return
        _last_click_ts = now
        pyautogui.click(clicks=2, interval=interval, button="left")  # double-click for real
        pyautogui.press('enter')

        # record as two left-clicks
        left_click_count += 1
        _last_click_side = "left_dbl"
        _last_click_flash_until = time.time() + 0.6



    def move_cursor_for_gaze(gaze: str, accuracy: int):
        """
        Updates a smooth target position based on gaze direction.
        The background smoother thread moves the cursor toward this target.
        """
        global _last_cursor_move_ts, _target_pos, SCROLL_MODE

        if accuracy < ACCURACY_GATE:
            return

        now = time.time()
        if now - _last_cursor_move_ts < MOVE_COOLDOWN_SEC:
            return
        _last_cursor_move_ts = now
        
        
        if SCROLL_MODE:
            # --- Scroll Mode ---
            if gaze == "up":
                pyautogui.scroll(-200)
                print("🧾 Scrolled up")
                return
            elif gaze == "down":
                pyautogui.scroll(+200)
                print("🧾 Scrolled down")
                return
            elif gaze in ("left", "right"):
                print("⏩ Left/right gaze ignored in scroll mode")
                return
        else:
        # step vector from gaze
            dx = dy = 0
            if gaze == "left":
                dx = -CURSOR_STEP_PX
            elif gaze == "right":
                dx = CURSOR_STEP_PX
            elif gaze == "up":
                dy = -CURSOR_STEP_PX
            elif gaze == "down":
                dy = CURSOR_STEP_PX
            else:
                return

            # update target (clamped)
            sw, sh = pyautogui.size()
            cx, cy = pyautogui.position()  # current as base
            tx, ty = _target_pos if _target_pos is not None else (cx, cy)
            # nudge the target rather than the current cursor to avoid fighting the smoother
            ntx = _clamp(tx + dx, 0, sw - 1)
            nty = _clamp(ty + dy, 0, sh - 1)
            _target_pos = (ntx, nty)
        
        
    

    LEFT_IRIS = [474, 475, 476, 477]
    RIGHT_IRIS = [469, 470, 471, 472]

    # Left eye indices list
    LEFT_EYE =[ 362, 386, 263, 374]
    # Right eye indices list
    RIGHT_EYE=[ 33, 159, 133, 145]

    # Set the project base directory dynamically 
    base_dir = Path(__file__).resolve().parent


    # Use the project root (already defined as ROOT)
    model_path = ROOT / "Models" / "gazemodel.h5"
    labels_path = ROOT / "Models" / "class_labels.json"



    IMG_SIZE = (64,56)
    B_SIZE = (34, 26)
    margin = 95

    confirm_mode = None  # "zoom_popup", "join_button", "chat_send", "end_confirm"

    # DEFAULT_LABELS = ["center", "left", "right", "up", "down", "blink"]
    
    DEFAULT_LABELS = [
    "center", "left", "right", "up", "down", 
    "blink", "left_blink", "right_blink",
    ]


    def load_labels(path: Path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # sort by numeric key if dict form
                    items = sorted(data.items(), key=lambda kv: int(kv[0]))
                    return [name for _, name in items]
                elif isinstance(data, list):
                    return data
                else:
                    print("[WARN] Unexpected format in class_labels.json, using defaults")
        except (FileNotFoundError, JSONDecodeError):
            print("[WARN] Missing or invalid class_labels.json, using defaults")
        return DEFAULT_LABELS

    class_labels = load_labels(CLASS_LABELS)


        
    # Blinking detection function
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

    # EAR threshold to consider blink
    blink_total = 0


    # Landmark indices for left and right eye
    # LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
    # RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]

    LEFT_EYE_LANDMARKS  = [362, 385, 387, 263, 373, 380]  # subject's left
    RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]   # subject's right

    def euclidean(p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))


    def eye_aspect_ratio(landmarks, eye_indices):
        # landmarks is expected to be a numpy array of shape (>=478, 2)
        if landmarks is None or len(landmarks) == 0 or np.max(eye_indices) >= len(landmarks):
            return None
        p1 = landmarks[eye_indices[1]]
        p2 = landmarks[eye_indices[2]]
        p3 = landmarks[eye_indices[5]]
        p4 = landmarks[eye_indices[4]]
        p5 = landmarks[eye_indices[0]]
        p6 = landmarks[eye_indices[3]]
        vertical = (euclidean(p2, p4) + euclidean(p1, p3)) / 2.0
        horizontal = euclidean(p5, p6)
        return vertical / horizontal if horizontal > 1e-6 else None




    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

    font_letter = cv2.FONT_HERSHEY_PLAIN
    
    model = load_model(model_path)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )


    def detect_gaze(eye_img, mesh_points, left_ear=None, right_ear=None):
        
        """
            Returns gaze direction with special cases:
            - "left_blink" → left eye closed only
            - "right_blink" → right eye closed only
            
        """
    
        
        pred_l = model.predict(eye_img)
        accuracy = int(np.array(pred_l).max() * 100)
        gaze = class_labels[np.argmax(pred_l)]



        # Horizontal Geometry
        right_eye_right_x = mesh_points[33][0]
        right_eye_left_x = mesh_points[133][0]
            
        right_eye_top_y = mesh_points[159][0]
        right_eye_bottom_y = mesh_points[145][0]
            
        right_iris_right_x = mesh_points[471][0]
        right_iris_left_x = mesh_points[469][0]
            
        right_iris_top_y = mesh_points[470][0]
        right_iris_bottom_y = mesh_points[472][0]
            
        # Vertical Geometry
        left_eye_right_x = mesh_points[362][0]
        left_eye_left_x = mesh_points[263][0]
            
        left_eye_top_y = mesh_points[386][0]
        left_eye_bottom_y = mesh_points[374][0]
            
        left_iris_right_x = mesh_points[474][0]
        left_iris_left_x = mesh_points[476][0]
            
        left_iris_top_y = mesh_points[475][0]
        left_iris_bottom_y = mesh_points[477][0]
            
            
        vertical_distance = mesh_points[145][1] - mesh_points[159][1]
        # print("Vertical distance : ", vertical_distance)
            
        # ==============Right Eye Gaze Detection========================
        right_eye_center_x = (mesh_points[33][0] + mesh_points[133][0]) // 2
        right_iris_center_x = (mesh_points[469][0] + mesh_points[471][0]) // 2
        right_eye_horizontal_offset = right_iris_center_x - right_eye_center_x
        # print("Horizontal offset Right            : ", right_eye_horizontal_offset)
            
        # ==============Left Eye Gaze Detection========================
        left_eye_center_x = (mesh_points[362][0] + mesh_points[263][0]) // 2
        left_iris_center_x = (mesh_points[476][0] + mesh_points[474][0]) // 2
        left_eye_horizontal_offset = left_iris_center_x - left_eye_center_x
        # print("Horizontal offset Left             : ", left_eye_horizontal_offset)
        
            
            
        landmark_left_boolean = False
        landmark_right_boolean = False
        landmark_center_boolean = False
            
        cnn_left_boolean = False
        cnn_right_boolean = False
        cnn_center_boolean = False
            
        
        
        # Right Eye
        right_eye_center_y = (mesh_points[159][1] + mesh_points[145][1]) // 2
        right_iris_center_y = (mesh_points[470][1] + mesh_points[472][1]) // 2
        delta_r_y = right_iris_center_y - right_eye_center_y

        # Left Eye
        left_eye_center_y = (mesh_points[386][1] + mesh_points[374][1]) // 2
        left_iris_center_y = (mesh_points[475][1] + mesh_points[477][1]) // 2
        delta_l_y = left_iris_center_y - left_eye_center_y
        
        
        #============== modify
        left_eye_offset_y = (mesh_points[386][1] - mesh_points[374][1])
        right_eye_offset_y = (mesh_points[159][1] - mesh_points[145][1]) 
        
        # print("Right Eye Vertical Offset for DOWN : ", left_eye_offset_y)
        # print("Left Eye Vertical Offset for DOWN  : ", right_eye_offset_y)
        
        
        # print("Right Eye Vertical Offset for UP   : ", delta_r_y)
        # print("Left Eye Vertical Offset for UP    : ", delta_l_y)
        

        
        landmark_up_boolean = False
        landmark_down_boolean = False
        
        
        # =================================TNew Calibrated Threshold Implementation=================================================================================================================
        # =================================TNew Calibrated Threshold Implementation==================================
        if mesh_points is None or len(mesh_points) < 478:
            print("⚠️ No mesh points available this frame.")
            return gaze, accuracy

        # Convert mesh_points to normalized coordinates (0–1)
        frame_h, frame_w = frame.shape[:2]
        landmarks = [
            type("Point", (), {"x": p[0] / frame_w, "y": p[1] / frame_h}) for p in mesh_points
        ]
        
        
        # # (Optional) show iris landmarks
        # left = [landmarks[374], landmarks[386]]
        # right = [landmarks[145], landmarks[159]]

        
        
        # ==== Compute eye landmark distances ====
        # Left Eye
        # left_left_x1, left_left_x2 = landmarks[33].x, landmarks[471].x
        # left_right_x1, left_right_x2 = landmarks[469].x, landmarks[133].x
        # left_up_y1, left_up_y2 = landmarks[470].y, landmarks[159].y
        # left_down_y1, left_down_y2 = landmarks[159].y, landmarks[145].y

        # # # Right Eye
        # right_left_x1, right_left_x2 = landmarks[474].x, landmarks[362].x
        # right_right_x1, right_right_x2 = landmarks[469].x, landmarks[263].x
        # right_up_y1, right_up_y2 = landmarks[475].y, landmarks[386].y
        # right_down_y1, right_down_y2 = landmarks[386].y, landmarks[374].y
        
        
        left_eye_left_direction_threshold = landmarks[263].x- landmarks[476].x
        right_eye_left_direction_threshold = landmarks[133].x- landmarks[469].x
        
        left_eye_right_direction_threshold = landmarks[474].x- landmarks[362].x
        right_eye_right_direction_threshold = landmarks[471].x- landmarks[33].x
        
        left_eye_up_direction_threshold = landmarks[386].y- landmarks[475].y
        right_eye_up_direction_threshold = landmarks[159].y- landmarks[470].y
        
        left_eye_down_direction_threshold = landmarks[374].y- landmarks[386].y
        right_eye_down_direction_threshold = landmarks[145].y- landmarks[159].y
        
        
        #===================================================================
        print("Vertical Offset for Up direction LEFT  EYE: ",landmarks[386].y- landmarks[475].y) 
        print("Vertical Offset for Up direction RIGHT EYE: ",landmarks[159].y- landmarks[470].y)   
        
        print("Vertical Offset for Down direction LEFT EYE  : ",landmarks[374].y- landmarks[386].y) 
        print("Vertical Offset for Down direction RIGHT  EYE: ",landmarks[145].y- landmarks[159].y) 
        
        
        print("Horizontal Offset for Left direction LEFT EYE  : ",landmarks[263].x- landmarks[476].x) 
        print("Horizontal Offset for Left direction RIGHT  EYE: ",landmarks[133].x- landmarks[469].x) 
        
        print("Horizontal Offset for Right direction LEFT EYE  : ",landmarks[474].x- landmarks[362].x) 
        print("Horizontal Offset for Right direction RIGHT  EYE: ",landmarks[471].x- landmarks[33].x)
         
    
    
    
        # ==== Calculate direction values ====
        # left_eye_horizontal_for_left_direction = left_left_x2 - left_left_x1
        # right_eye_horizontal_for_left_direction = right_left_x1 - right_left_x2

        # left_eye_horizontal_for_right_direction = left_right_x2 - left_right_x1
        # right_eye_horizontal_for_right_direction = right_right_x2 - right_right_x1

        # left_eye_vertical_for_up_direction = left_up_y2 - left_up_y1
        # right_eye_vertical_for_up_direction = right_up_y2 - right_up_y1

        # left_eye_vertical_for_down_direction = left_down_y2 - left_down_y1
        # right_eye_vertical_for_down_direction = right_down_y2 - right_down_y1
        
        
        if(left_eye_down_direction_threshold <= 0 or right_eye_down_direction_threshold <= 0):
            print("=================Both EYE Blink====================")
            return "BOTH_BLINK", 100
        elif(left_eye_down_direction_threshold < LEFT_EYE_DOWN_DIRECTION_THRESHOLD - 0.005 and right_eye_down_direction_threshold > RIGHT_EYE_DOWN_DIRECTION_THRESHOLD):
            print("=================LEFT EYE Blink====================")
            return "LEFT_BLINK", 100
        elif(left_eye_down_direction_threshold > LEFT_EYE_DOWN_DIRECTION_THRESHOLD and right_eye_down_direction_threshold < RIGHT_EYE_DOWN_DIRECTION_THRESHOLD - 0.005):
            print("=================RIGHT EYE Blink====================")  
            return "RIGHT_BLINK", 100

       
            
        if((left_eye_left_direction_threshold > LEFT_EYE_LEFT_DIRECTION_THRESHOLD
            and right_eye_left_direction_threshold > RIGHT_EYE_LEFT_DIRECTION_THRESHOLD)and(left_eye_right_direction_threshold > LEFT_EYE_RIGHT_DIRECTION_THRESHOLD
            and right_eye_right_direction_threshold > RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD)and(left_eye_down_direction_threshold > LEFT_EYE_DOWN_DIRECTION_THRESHOLD
            and right_eye_down_direction_threshold > RIGHT_EYE_DOWN_DIRECTION_THRESHOLD)and(left_eye_up_direction_threshold < LEFT_EYE_UP_DIRECTION_THRESHOLD
            and right_eye_up_direction_threshold < RIGHT_EYE_UP_DIRECTION_THRESHOLD)):
            # landmark_center_boolean = True
            gaze = "center"
        
        elif (
            (left_eye_down_direction_threshold < LEFT_EYE_DOWN_DIRECTION_THRESHOLD
            and right_eye_down_direction_threshold < RIGHT_EYE_DOWN_DIRECTION_THRESHOLD) or gaze == "down"
        ):
            gaze = "down"
            print("Final Gaze direction: ", gaze)
        
        elif (
            (left_eye_up_direction_threshold > LEFT_EYE_UP_DIRECTION_THRESHOLD
            and right_eye_up_direction_threshold > RIGHT_EYE_UP_DIRECTION_THRESHOLD) and gaze == "up"
        ):
            gaze = "up"
            print("Final Gaze direction: ", gaze) 
            
        elif (
            (left_eye_right_direction_threshold < LEFT_EYE_RIGHT_DIRECTION_THRESHOLD
            and right_eye_right_direction_threshold < RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD) and gaze == "right"
        ):
            gaze = "right"
            print("Final Gaze direction: ", gaze) 
        
        elif (
            (left_eye_left_direction_threshold < LEFT_EYE_LEFT_DIRECTION_THRESHOLD
            and right_eye_left_direction_threshold < RIGHT_EYE_LEFT_DIRECTION_THRESHOLD) and gaze == "left"
        ):
            gaze = "left"
            print("Final Gaze direction: ", gaze)         
            
        else:
            gaze = "center"
            print("Final Gaze direction: ", gaze) 
            
            
        
        
        if((left_eye_left_direction_threshold > LEFT_EYE_LEFT_DIRECTION_THRESHOLD
            and right_eye_left_direction_threshold > RIGHT_EYE_LEFT_DIRECTION_THRESHOLD)and(left_eye_right_direction_threshold > LEFT_EYE_RIGHT_DIRECTION_THRESHOLD
            and right_eye_right_direction_threshold > RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD)and(left_eye_down_direction_threshold > LEFT_EYE_DOWN_DIRECTION_THRESHOLD
            and right_eye_down_direction_threshold > RIGHT_EYE_DOWN_DIRECTION_THRESHOLD)and(left_eye_up_direction_threshold < LEFT_EYE_UP_DIRECTION_THRESHOLD
            and right_eye_up_direction_threshold < RIGHT_EYE_UP_DIRECTION_THRESHOLD)):
            print("Looking CENTER (Landmarks)")
            
        elif (
            left_eye_down_direction_threshold < LEFT_EYE_DOWN_DIRECTION_THRESHOLD
            and right_eye_down_direction_threshold < RIGHT_EYE_DOWN_DIRECTION_THRESHOLD 
        ):
            print("Looking DOWN (Landmarks)")
        
        elif (
            left_eye_up_direction_threshold > LEFT_EYE_UP_DIRECTION_THRESHOLD
            and right_eye_up_direction_threshold > RIGHT_EYE_UP_DIRECTION_THRESHOLD 
        ):
            print("Looking UP (Landmarks)")
        
            
        elif (
            left_eye_right_direction_threshold < LEFT_EYE_RIGHT_DIRECTION_THRESHOLD
            and right_eye_right_direction_threshold < RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD 
        ):
            print("Looking RIGHT (Landmarks)")
        
        elif (
            left_eye_left_direction_threshold < LEFT_EYE_LEFT_DIRECTION_THRESHOLD
            and right_eye_left_direction_threshold < RIGHT_EYE_LEFT_DIRECTION_THRESHOLD 
        ):
            print("Looking LEFT (Landmarks)")

            
        else:
            print("Looking CENTER (Landmarks)")

    
    
        
        # =================================This section should be change or remove=================================================================================================================
        
        # if (RIGHT_THRESHOLD < right_eye_horizontal_offset < LEFT_THRESHOLD) and (RIGHT_THRESHOLD < left_eye_horizontal_offset < LEFT_THRESHOLD):
        #     landmark_center_boolean = True
        #     print("Looking CENTER (Landmarks)")
        # if left_eye_offset_y < DOWN_THRESHOLD and right_eye_offset_y < DOWN_THRESHOLD:
        #     landmark_down_boolean = True
        #     print("Looking DOWN (Landmarks)")
        # elif (right_eye_horizontal_offset > LEFT_THRESHOLD) and (left_eye_horizontal_offset > LEFT_THRESHOLD):
        #     landmark_left_boolean = True
        #     print("Looking LEFT (Landmarks)")
        # elif (right_eye_horizontal_offset < RIGHT_THRESHOLD) and (left_eye_horizontal_offset < RIGHT_THRESHOLD):
        #     landmark_right_boolean = True
        #     print("Looking RIGHT (Landmarks)")
        # elif delta_r_y < UP_THRESHOLD and delta_l_y < UP_THRESHOLD:
        #     landmark_up_boolean = True
        #     print("Looking UP (Landmarks)")
        # else:
        #     landmark_center_boolean = True
        #     print("Looking CENTER (Landmarks)")
        
        
        # ===================================================================================================================================================================================

            
        # Horizontal deltas (X axis)
        right_eye_center_x = (right_eye_left_x + right_eye_right_x) / 2
        delta_r = ((right_iris_left_x + right_iris_right_x) / 2) - right_eye_center_x

        left_eye_center_x = (left_eye_left_x + left_eye_right_x) / 2
        delta_l = ((left_iris_left_x + left_iris_right_x) / 2) - left_eye_center_x

        # Vertical deltas (Y axis)
        right_eye_center_y = (right_eye_top_y + right_eye_bottom_y) / 2
        delta_r_y = ((right_iris_top_y + right_iris_bottom_y) / 2) - right_eye_center_y

        left_eye_center_y = (left_eye_top_y + left_eye_bottom_y) / 2
        delta_l_y = ((left_iris_top_y + left_iris_bottom_y) / 2) - left_eye_center_y

            
        if gaze == "left":
            print("Looking LEFT (CNN model prediction)")
        elif gaze == "right":
            print("Looking RIGHT (CNN model prediction)")
        elif gaze == "center":
            print("Looking CENTER (CNN model prediction)")
        elif gaze == "up":
            print("Looking UP (CNN model prediction)")
        elif gaze == "down":
            print("Looking DOWN (CNN model prediction)")
        else:
            print("Looking CENTER (CNN model prediction)")
            

        return gaze, accuracy


    
    def crop_eye(img, eye_points):
        x1, y1 = np.amin(eye_points, axis=0)
        x2, y2 = np.amax(eye_points, axis=0)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

        w = (x2 - x1) * 1.2
        h = w * IMG_SIZE[1] / IMG_SIZE[0]
        

        margin_x, margin_y = w / 2, h / 2

        min_x, min_y = int(cx - margin_x), int(cy - margin_y)
        max_x, max_y = int(cx + margin_x), int(cy + margin_y)

        eye_rect = np.rint([min_x, min_y, max_x, max_y]).astype(int)

        eye_img = gray[eye_rect[1]:eye_rect[3], eye_rect[0]:eye_rect[2]]

        return eye_img, eye_rect



    # Initialize head pose estimator once
    pose_estimator = HeadPoseEstimator()

    # ==========================
    # Load saved camera index
    # ==========================
    # --- Load camera index from global config ---
    

    ROOT = Path(__file__).resolve().parents[2]  # 🟢 Go up two levels to project root
    config_path = ROOT / "Data" / "configuration.json"

    print(f"🔍 Loading config from: {config_path}")

    camera_index = 0  # default fallback
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                camera_index = config.get("camera", {}).get("index", 0)
        else:
            print(f"⚠️ Config file not found at {config_path}, using default camera (0).")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"⚠️ Failed to read configuration.json, using default camera (0): {e}")

    print(f"[INFO] Using camera index {camera_index}")

    cap = cv2.VideoCapture(camera_index)


    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from webcam")
        exit()
        
            
    # start smoother once at startup (after imports)
    if enable_mouse_control and not _smoother_started:
        _start_cursor_smoother()
        # speak("Gaze control enabled.")

    # Set resolution for virtual camera
    height, width = frame.shape[:2]



    last_prediction_time = time.time()
    blink_start_time = None

        
    # Define the window as resizable
    if show_video:
        cv2.namedWindow("Real Time Gaze Estimation", cv2.WINDOW_NORMAL)

                # Get screen size
        screen_width = pyautogui.size().width
        screen_height = pyautogui.size().height

                # Calculate 3/4 width and keep height proportional or fixed
        window_width = int(screen_width * 0.6)
        window_height = int(screen_height * 0.75)  # Or use a fixed value

                # Resize the OpenCV window
        cv2.resizeWindow("Real Time Gaze Estimation", window_width, window_height)

                # Optional: move window to center
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
        cv2.moveWindow("Real Time Gaze Estimation", x_pos, y_pos)
    
    # Initialize variables for UI placeholders
    eye_img_l_view = np.zeros((112, 128, 3), dtype=np.uint8)
    eye_img_r_view = np.zeros((112, 128, 3), dtype=np.uint8)
    gaze = "center"
    accuracy = 0


    while cap.isOpened() and (external_stop is None or not external_stop.is_set()):
        
        success, frame = cap.read()
        if not success:
            break
        
        with RUN_GAZE_LOCK:
            if not RUN_GAZE:
                print("[INFO] Gaze loop stopped by user.")
                break
        
        
        # swap your compose_ui(...) with this one
        def compose_ui(frame, eye_left_view, eye_right_view, gaze, acc, blink_total, left_blinks, right_blinks, fps):
            H, W = UI_H, UI_W
            canvas = np.full((H, W, 3), COL["bg"], np.uint8)
            

            # ---- Title Bar ----
            draw_card(canvas, 0, 0, W, TITLE_BAR_H, radius=0, color=COL["card2"], shadow=False)
            put_text(canvas, "REAL TIME GAZE ESTIMATION", (MARGIN_X, 46), 1.1, COL["text"], 3)
            put_text(canvas, f"{fps:.1f} FPS", (W - MARGIN_X, 46), 0.9, COL["muted"], 2, align="right")

            # ---- Layout sizes ----
            y_top = TITLE_BAR_H + MARGIN_Y
            cam_w = int(W * 0.65)       # left column
            right_w = W - cam_w - MARGIN_X * 2
            cam_h = H - y_top - MARGIN_Y

            # ---- Left: Video feed ----
            fh, fw = frame.shape[:2]
            scale = min(cam_w / fw, cam_h / fh)
            vw, vh = int(fw * scale), int(fh * scale)
            vx, vy = MARGIN_X, y_top
            
            
            
            draw_card(canvas, vx, vy, vw, vh, radius=20, color=COL["card"])
            resized = cv2.resize(frame, (vw, vh))
            mask = _rounded_rect_mask(vh, vw, 16)
            roi = canvas[vy:vy+vh, vx:vx+vw]
            roi[:] = np.where(mask[..., None] == 255, resized, roi)

            # ---- Right: Eye crops (side by side) ----
            rx = vx + vw + 30
            ry = y_top
            
            ry += 30 
            # 🟩 Add section title here
            put_text(canvas, "GAZE ESTIMATION RESULTS", (rx, ry - 15), 0.8, (255,255,255), 2)
            ry += 80 
            thumb_w, thumb_h = 120, 100
            gap = 160  # space between left and right eye
            if eye_left_view is not None and eye_right_view is not None:
                left_thumb = cv2.resize(eye_left_view, (thumb_w, thumb_h))
                right_thumb = cv2.resize(eye_right_view, (thumb_w, thumb_h))

                # Create a blank gap (same height, gap width, same channels)
                spacer = np.full((thumb_h, gap, 3), COL["bg"], dtype=np.uint8)

                # Combine with gap
                combined = np.hstack([left_thumb, spacer, right_thumb])

                # Paste into canvas
                canvas[ry:ry+thumb_h, rx:rx+2*thumb_w+gap] = combined

                # Labels (adjusted for gap)
                put_text(canvas, "LEFT EYE", (rx, ry-6), 0.6, (255,255,255))
                put_text(canvas, "RIGHT EYE", (rx+thumb_w+gap+10, ry-6), 0.6, (255,255,255))

                ry += thumb_h + 30

            # ---- Gaze + accuracy ----
            draw_card(canvas, rx, ry, right_w-40, 50, radius=14, color=COL["accent2"])
            put_text(canvas, f"GAZE    : {gaze.upper()}  ({acc}%)", (rx+12, ry+32), 0.8, (255,255,255), 2)
            ry += 70

            # ---- Blink counters ----
            draw_card(canvas, rx, ry, right_w-40, 50, radius=14, color=COL["accent"])
            put_text(canvas, f"Long Blinks Count  : {blink_total}", (rx+12, ry+32), 0.8, (255,255,255), 2)
            ry += 60
            draw_card(canvas, rx, ry, right_w-40, 50, radius=14, color=COL["accent"])
            put_text(canvas, f"Left Blink Count    : {left_blinks}", (rx+12, ry+32), 0.8, (255,255,255), 2)
            ry += 60
            draw_card(canvas, rx, ry, right_w-40, 50, radius=14, color=COL["accent"])
            put_text(canvas, f"Right Blink Count   : {right_blinks}", (rx+12, ry+32), 0.8, (255,255,255), 2)
            ry += 60
            draw_card(canvas, rx, ry, right_w-40, 50, radius=14, color=COL["accent2"])
            put_text(canvas, f"Head Pose Direction : {head_direction}", (rx+12, ry+32), 0.8, (255,255,255), 2)


            return canvas
        
        
        
    

        output = np.zeros((900,820,3), dtype="uint8")
        ret, img = cap.read()
        h, w = (112, 128)
        if not ret:
            break
        
        # UI-only mirror
        display = cv2.flip(img, 1)
        
        
        if ui_app:
            try:
                ui_app.update_from_gaze(
                    frame=display,  # raw frame or processed one
                    gaze=gaze,
                    acc=accuracy,
                    blink_total=blink_total,
                    left=left_blink_count,
                    right=right_blink_count 
                )
            except Exception as e:
                print("UI update failed:", e)

        # img = cv2.flip(img, 1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


        # Process the frame to get face landmarks
        results = face_mesh.process(rgb_frame)
        # ---------------- FaceMesh to mesh_points (safe) ----------------
        img_h, img_w = img.shape[:2]
        ih, iw = gray.shape

        mesh_points = None
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            pts = np.array([
                np.multiply([p.x, p.y], [iw, ih]).astype(int)
                for p in face_landmarks.landmark
            ])
            # You use iris indices up to 477; require them to exist
            if pts.shape[0] >= 478:
                mesh_points = pts

        flipped_frame = cv2.flip(img, 1)  # horizontally flip the video feed
        # If no usable landmarks, render UI and continue
        if mesh_points is None:
            if 't_prev' not in globals():
                t_prev = time.perf_counter()
            fps = 1.0 / max(1e-6, (time.perf_counter() - t_prev))
            t_prev = time.perf_counter()

            ui = compose_ui(
            frame=flipped_frame,
            eye_left_view=eye_img_l_view,
            eye_right_view=eye_img_r_view,
            gaze=gaze,
            acc=accuracy,
            blink_total=blink_total,
            left_blinks=left_blink_count,  # or your left blink variable
            right_blinks=right_blink_count, # or your right blink variable
            fps=fps
            )
            
            if ui_app:
                try:
                    ui_app.update_from_gaze(
                        frame=display,  # raw frame or processed one
                        gaze=gaze,
                        acc=accuracy,
                        blink_total=blink_total,
                        left=left_blink_count,
                        right=right_blink_count 
                    )
                except Exception as e:
                    print("UI update failed:", e)

            # if show_video:
            #     cv2.imshow("Real Time Gaze Estimation", ui)
            #     if cv2.waitKey(1) in (ord('q'), ord('Q')): break
            #     continue
            
            if show_video:
                cv2.imshow("Real Time Gaze Estimation", ui)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q')):
                    print("[INFO] Video window closed by user.")
                    cap.release()
                    show_video = False  # ✅ disable further imshow calls
                    cv2.destroyWindow("Real Time Gaze Estimation")  # ✅ close only the video window


        # ---------------- EARs (safe) ----------------
        left_ear  = eye_aspect_ratio(mesh_points, LEFT_EYE_LANDMARKS)
        right_ear = eye_aspect_ratio(mesh_points, RIGHT_EYE_LANDMARKS)

        # If EARs couldn’t be computed this frame, just draw and continue
        if left_ear is None or right_ear is None:
            if 't_prev' not in globals():
                t_prev = time.perf_counter()
            fps = 1.0 / max(1e-6, (time.perf_counter() - t_prev))
            t_prev = time.perf_counter()

            ui = compose_ui(
                frame=flipped_frame,
                eye_left_view=eye_img_l_view,
                eye_right_view=eye_img_r_view,
                gaze=gaze,
                acc=accuracy,
                blink_total=blink_total,
                left_blinks=left_blink_count,     # or your left blink variable
                right_blinks=right_blink_count,# or your right blink variable
                fps=fps
            )
            
            
            if ui_app:
                try:
                    ui_app.update_from_gaze(
                        frame=display,  # raw frame or processed one
                        gaze=gaze,
                        acc=accuracy,
                        blink_total=blink_total,
                        left=left_blink_count, 
                        right=right_blink_count 
                    )
                except Exception as e:
                    print("UI update failed:", e)
                    
            # if show_video:
            #     cv2.imshow("Real Time Gaze Estimation", ui)
            #     if cv2.waitKey(1) in (ord('q'), ord('Q')): break
            #     continue
            
            if show_video:
                cv2.imshow("Real Time Gaze Estimation", ui)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q')):
                    print("[INFO] Video window closed by user.")
                    cap.release()
                    show_video = False  # ✅ disable further imshow calls
                    cv2.destroyWindow("Real Time Gaze Estimation")  # ✅ close only the video window


        # Now it’s safe to use EAR values
        if left_ear is None or right_ear is None:
            # Skip frame if eyes not detected properly
            continue

        avg_ear = (left_ear + right_ear) / 2
        
        wink_in_progress = (_left_wink_start is not None) or (_right_wink_start is not None)
        both_closed_now  = (left_ear < EAR_CLOSED) and (right_ear < EAR_CLOSED)

        # time-based quiet period
        now = time.time()
        time_quiet = (now < _suppress_until_ts)

        # suppress_gaze = is_eye_closed and both_closed_now or wink_in_progress or time_quiet  
        frame_h, frame_w = frame.shape[:2]
        landmarks = [
            type("Point", (), {"x": p[0] / frame_w, "y": p[1] / frame_h}) for p in mesh_points
        ]
        
         
        left_eye_down_direction_threshold = landmarks[374].y- landmarks[386].y
        right_eye_down_direction_threshold = landmarks[145].y- landmarks[159].y
        
        # both_closed_now = (left_eye_down_direction_threshold <= 0) and (right_eye_down_direction_threshold <= 0)
            
        
    # --- Long both-eyes blink start ---
        if both_closed_now:
            if long_blink_start is None:
                long_blink_start = t
                long_blink_armed = True
                print(f"🕒 Long blink started at {t:.2f}")
        else:
            # Blink ended — eyes reopened
            if long_blink_start is not None:
                
                held = t - long_blink_start
                print(f"Blink duration: {held:.2f}s")

                if long_blink_armed and (t >= long_blink_cooldown_until):
                    if held >= 3.0:
                        toggle_scroll_mode()
                        winsound.Beep(900, 150)
                    elif held >= LONG_BLINK_SEC:
                        _warp_to_next_anchor()
                        winsound.Beep(1200, 120)

                    long_blink_armed = False
                    _suppress_until_ts = time.time() + SUPPRESS_AFTER_BLINK_SEC
                    long_blink_cooldown_until = t + LONG_BLINK_COOLDOWN

                long_blink_start = None  # reset timer

        # Re-arm after cooldown
        if not long_blink_armed and (t >= long_blink_cooldown_until):
            long_blink_armed = True





        # --- Robust wink + long-blink handling ---
        t = time.monotonic()

        # Hysteresis booleans
        left_closed  = (left_ear  < EAR_CLOSED)
        right_closed = (right_ear < EAR_CLOSED)
        left_open    = (left_ear  > EAR_OPEN_HYST)
        right_open   = (right_ear > EAR_OPEN_HYST)

        

        if not results.multi_face_landmarks:

            if ui_app:
                try:
                    ui_app.update_from_gaze(
                        frame=display,  # raw frame or processed one
                        gaze=gaze,
                        acc=accuracy,
                        blink_total=blink_total,
                        left=left_blink_count, 
                        right=right_blink_count 
                    )
                except Exception as e:
                    print("UI update failed:", e)
                    
            if show_video:       
                cv2.imshow("Real Time Gaze Estimation", output)  # or whatever you draw
                if cv2.waitKey(1) in (ord('q'), ord('Q')): break
                continue

            
        
            
            
    # --- Long both-eyes blink → anchor warp (robust) ---
    # state kept between frames
        try:
            long_blink_start
            long_blink_cooldown_until
            long_blink_armed
        except NameError:
            long_blink_start = None
            long_blink_cooldown_until = 0.0
            long_blink_armed = True

        t = time.monotonic()
    
        # ---------------- Draw iris landmarks (for visualization) ----------------

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Convert normalized landmarks to pixel coordinates
                mesh_points = np.array([
                    np.multiply([p.x, p.y], [img_w, img_h]).astype(int)
                    for p in face_landmarks.landmark
                ])

                # Draw enclosing circle for left iris
                (l_cx, l_cy), l_radius = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
                center_left = np.array([l_cx, l_cy], dtype=np.int32)
                cv2.circle(img, center_left, int(l_radius), (0, 255, 0), 1, cv2.LINE_AA)

                # Draw enclosing circle for right iris
                (r_cx, r_cy), r_radius = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
                center_right = np.array([r_cx, r_cy], dtype=np.int32)
                cv2.circle(img, center_right, int(r_radius), (0, 255, 0), 1, cv2.LINE_AA)
                

        for face in faces:
            shapes = predictor(gray, face)
            
            DRAW_EYE_SHAPE = False

            if DRAW_EYE_SHAPE:
                for n in range(36,42):
                    x= shapes.part(n).x
                    y = shapes.part(n).y
                    next_point = n+1
                    if n==41:
                        next_point = 36 
                    
                    x2 = shapes.part(next_point).x
                    y2 = shapes.part(next_point).y
                    cv2.line(img,(x,y),(x2,y2),(0,69,255),2)

                for n in range(42,48):
                    x= shapes.part(n).x
                    y = shapes.part(n).y
                    next_point = n+1
                    if n==47:
                        next_point = 42 
                    
                    x2 = shapes.part(next_point).x
                    y2 = shapes.part(next_point).y
                    cv2.line(img,(x,y),(x2,y2),(153,0,153),2)
            shapes = face_utils.shape_to_np(shapes)
            
            #=======================56,64 EYE IMAGE======================================
            eye_img_l, eye_rect_l = crop_eye(gray, eye_points=shapes[36:42])
            eye_img_r, eye_rect_r = crop_eye(gray, eye_points=shapes[42:48])
            
            #====================FOR THE EYE FINAL_WINDOW================================
            eye_img_l_view = cv2.resize(eye_img_l, dsize=(128,112))
            eye_img_l_view = cv2.cvtColor(eye_img_l_view,cv2.COLOR_BGR2RGB)
            eye_img_r_view = cv2.resize(eye_img_r, dsize=(128,112))
            eye_img_r_view = cv2.cvtColor(eye_img_r_view, cv2.COLOR_BGR2RGB)
            
            #===================FOR THE BLINK DETECTION=================================
            eye_blink_left = cv2.resize(eye_img_l.copy(), B_SIZE)
            eye_blink_right = cv2.resize(eye_img_r.copy(), B_SIZE)
            eye_blink_left_i = eye_blink_left.reshape((1, B_SIZE[1], B_SIZE[0], 1)).astype(np.float32) / 255.
            eye_blink_right_i = eye_blink_right.reshape((1, B_SIZE[1], B_SIZE[0], 1)).astype(np.float32) / 255.
            
            #==================FOR THE GAZE DETECTIOM===================================
            eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)
            eye_input_g = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
            
            
            # 🔹 Ignore gaze prediction right after a wink
            # 🔹 Ignore gaze prediction right after a wink
            if time.time() < _suppress_until_ts:
                print("🕒 Gaze temporarily suppressed during wink/blink.")
                gaze = "center"
                accuracy = 100
                
            # --- Head Pose Estimation ---
            frame_with_pose, head_direction = pose_estimator.estimate(frame)


            # 🧠 Head direction control logic
            # 🧠 Head direction control logic
            if head_direction != "Forward":
                # Speak only once every few seconds to avoid repetition
                if not hasattr(main, "_last_head_warn") or (time.time() - main._last_head_warn > 4):
                    speak(
                        f"You are looking {head_direction.lower()}. Please look forward to control the application using gaze direction."
                    )
                    main._last_head_warn = time.time()

                # ✅ Build the UI using this frame (keep the window active)
                ui = compose_ui(
                    frame=frame_with_pose,
                    eye_left_view=eye_img_r_view,
                    eye_right_view=eye_img_l_view,
                    gaze=gaze,
                    acc=accuracy,
                    blink_total=blink_total,
                    left_blinks=left_blink_count,
                    right_blinks=right_blink_count,
                    fps=fps
                )

                if show_video:
                    cv2.imshow("Real Time Gaze Estimation", ui)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), ord('Q')):
                        print("[INFO] Video window closed by user.")
                        cap.release()
                        show_video = False
                        cv2.destroyWindow("Real Time Gaze Estimation")
                continue  # 🚫 Skip gaze control for this frame

            # ✅ Smooth resume when forward
            elif getattr(main, "_head_warning_active", False) and head_direction == "Forward":
                from utils.common import stop_speech
                stop_speech()
                main._head_warning_active = False


            
            
            #=================PREDICTION PROCESS========================================
            if head_direction == "Forward":
                gaze, accuracy = detect_gaze(
                    
                    eye_input_g, 
                    mesh_points,
                    left_ear=left_ear,
                    right_ear=right_ear
                )
            
                # --- Count Blinks based on detection result ---
                if gaze == "LEFT_BLINK":
                    left_blink_count += 1
                    _double_click_debounced()     # 👈 triggers double left-click
                    print(f"👁️ Left blink count: {left_blink_count}")

                elif gaze == "RIGHT_BLINK":
                    right_blink_count += 1
                    _right_click_debounced()      # 👈 triggers single right-click
                    print(f"👁️ Right blink count: {right_blink_count}")

                elif gaze == "BOTH_BLINK":
                    both_blink_count += 1
                    blink_total += 1

                    # Blink ended — eyes reopened
                    if long_blink_start is not None:
                        held = t - long_blink_start
                        print(f"Blink duration: {held:.2f}s")

                        if long_blink_armed and (t >= long_blink_cooldown_until):
                            if held >= 3.0:  # 2+ seconds
                                toggle_scroll_mode()
                                winsound.Beep(900, 150)
                            elif held >= LONG_BLINK_SEC:  # 1–2 seconds
                                _warp_to_next_anchor()
                                winsound.Beep(1200, 120)
                                

                            long_blink_armed = False
                            _suppress_until_ts = time.time() + SUPPRESS_AFTER_BLINK_SEC
                            long_blink_cooldown_until = t + LONG_BLINK_COOLDOWN

                        long_blink_start = None  # reset timer
                        
                    # Re-arm after cooldown
                    if not long_blink_armed and (t >= long_blink_cooldown_until):
                        long_blink_armed = True



            # Only allow new gaze prediction after a short interval      
            # if (gaze in ("left", "right", "up", "down")):
            #     move_cursor_for_gaze(gaze, accuracy)

            
        
            # Move mouse (function has its own cooldown & accuracy gate)
            if gaze in ("left", "right", "up", "down"):
                move_cursor_for_gaze(gaze, accuracy)
                            
                
                
            #===========================FINAL_WINDOWS=========================================
            output = cv2.line(output,(400,200), (400,0),(0,255,0),thickness=2)
            cv2.putText(output,"LEFT EYE GAZE",(235,200), font_letter,1, (255,255,51),1)
    
            cv2.putText(output,"RIGHT EYE GAZE",(445,200), font_letter,1, (255,255,51),1)
            

            right_eye_x = (2*margin + 2*w)
            eye_width = eye_img_l_view.shape[1]
            left_eye_x = 400 - (right_eye_x + eye_width - 400)

            output[0:112, left_eye_x:left_eye_x + eye_width] = eye_img_l_view
            cv2.putText(output, gaze, (left_eye_x + 30, 150), font_letter, 2, (0,255,0), 2)
            cv2.putText(output, f"{accuracy}%", (left_eye_x + 30, 180), font_letter, 1.5, (255,255,255), 1)


            
            output[0:112, 2*margin+2*w:(2*margin+2*w)+w] = eye_img_r_view
            cv2.putText(output, gaze,((2*margin+2*w)+30,150), font_letter,2, (0,0,255),2)
            
            cv2.putText(output, gaze, ((2*margin+2*w)+30,150), font_letter, 2, (0,0,255), 2)
            cv2.putText(output, f"{accuracy}%", ((2*margin+2*w)+30,180), font_letter, 1.5, (255,255,255), 1)

            cv2.putText(output, f"Blinks: {blink_total}", (10, 30), font_letter, 2, (0, 255, 255), 2)
            
            output[235+100:715+100, 80:720] = img
            
            
            
            # --- FPS calculation ---
            if 't_prev' not in globals():
                t_prev = time.perf_counter()
            fps = 1.0 / max(1e-6, (time.perf_counter() - t_prev))
            t_prev = time.perf_counter()
            
            
            flipped_frame = cv2.flip(img, 1)  
            
            # Add head pose estimation on the same frame
            # frame_with_pose = pose_estimator.estimate(frame)
    
            

            
            # --- Compose polished UI ---
            ui = compose_ui(
                frame=frame_with_pose,
                eye_left_view=eye_img_r_view,
                eye_right_view=eye_img_l_view,
                gaze=gaze,
                acc=accuracy,
                blink_total=blink_total,
                left_blinks=left_blink_count,     # or your left blink variable
                right_blinks=right_blink_count,# or your right blink variable
                fps=fps
            )
            
            if ui_app:
                try:
                    ui_app.update_from_gaze(
                        frame=display,  # raw frame or processed one
                        gaze=gaze,
                        acc=accuracy,
                        blink_total=blink_total,
                        left=left_blink_count, 
                        right=right_blink_count 
                    )
                except Exception as e:
                    print("UI update failed:", e)

            if show_video:
                cv2.imshow("Real Time Gaze Estimation", ui)
        
                        
        # if cv2.waitKey(1) == ord('q') or cv2.waitKey(1) == ord('Q') : 
        #     break
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q')):
            print("[INFO] Closing only video window (camera continues).")
            RUN_GAZE = False
            cap.release()
            cv2.destroyWindow("Real Time Gaze Estimation")  # ✅ close window only
            show_video = False  # ✅ turn off display but keep detection alive
            continue  # ✅ continue loop (don’t break)
    cap.release()
    cv2.destroyAllWindows()   
    
    UN_GAZE = False
    SMOOTHER_STOP.set() 


def run():
    main()
    # start_voice_autodictation()



def stop_gaze():
    """Safely stop the running gaze control loop."""
    global RUN_GAZE, SMOOTHER_STOP, stop_signal
    with RUN_GAZE_LOCK:
        RUN_GAZE = False
    SMOOTHER_STOP.set()
    stop_signal.set()
    print("[INFO] Gaze control stopped (via stop_gaze()).")




