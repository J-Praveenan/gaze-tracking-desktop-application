import cv2, dlib
import numpy as np
from imutils import face_utils
from tensorflow.keras.models import load_model
import winsound
import pyautogui
import time
import win32gui
import json
from pathlib import Path
import mediapipe as mp
import threading
import speech_recognition as sr
import pyttsx3
import os
import webbrowser
from json import JSONDecodeError
from typing import Tuple
import threading
from Voice_Model.voice_autodictation import start_voice_autodictation
# main.py (simplified snippet)




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

# ---- Anchor globals ----
ANCHOR_MARGIN_PX = 24       # keep off the exact screen edge
ANCHOR_ORDER = ("center", "left","center", "right","top","center","bottom")  # cycle order
_anchor_points = []
_anchor_idx = 0



def _start_cursor_smoother():
        global _smoother_started, _target_pos
        if _smoother_started:
            return
        _smoother_started = True

        # init target at current cursor
        x, y = pyautogui.position()
        _target_pos = (x, y)

        def _loop():
            period = 1.0 / SMOOTH_HZ
            while True:
                try:
                    cx, cy = pyautogui.position()
                    tx, ty = _target_pos
                    # exponential smoothing (lerp)
                    nx = cx + (tx - cx) * SMOOTH_ALPHA
                    ny = cy + (ty - cy) * SMOOTH_ALPHA
                    pyautogui.moveTo(nx, ny, duration=0)  # instantaneous tiny step
                except Exception:
                    pass
                time.sleep(period)

        threading.Thread(target=_loop, daemon=True).start()


def main():
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
        font = cv2.FONT_HERSHEY_SIMPLEX
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
            
            
            


    ROOT = Path(__file__).resolve().parent
    THRESH_FILE = (ROOT / "Data" / "gaze_thresholds.json") 
    CLASS_LABELS = (ROOT / "Models" / "class_labels.json") 

    with open(THRESH_FILE, "r", encoding="utf-8") as f:
            thresholds = json.load(f)

    # LEFT_THRESHOLD = thresholds["LEFT_THRESHOLD"] + 4
    # RIGHT_THRESHOLD = thresholds["RIGHT_THRESHOLD"] - 4
    
    LEFT_THRESHOLD = thresholds["LEFT_THRESHOLD"]
    RIGHT_THRESHOLD = thresholds["RIGHT_THRESHOLD"]
    
    UP_THRESHOLD = thresholds["UP_THRESHOLD"]
    DOWN_THRESHOLD = thresholds["DOWN_THRESHOLD"] 

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
    EAR_CLOSED = 0.2           # eye considered closed below this
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

    # start smoother once at startup (after imports)
    # _start_cursor_smoother()



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
    WINK_MIN_SEC = 0.08  #0.2         # valid wink duration window
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
        global _last_cursor_move_ts, _target_pos

        if accuracy < ACCURACY_GATE:
            return

        now = time.time()
        if now - _last_cursor_move_ts < MOVE_COOLDOWN_SEC:
            return
        _last_cursor_move_ts = now

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


    # Define model and labels path
    model_path = base_dir / "Models" / "gazemodel.h5"
    # model_path = r"E:\FinalYearProject\GazeTrackingModel\GazeTrackingSystem\Models\gazemodel.h5"


    labels_path = base_dir / "Models" / "class_labels.json"


    IMG_SIZE = (64,56)
    B_SIZE = (34, 26)
    margin = 95

    confirm_mode = None  # "zoom_popup", "join_button", "chat_send", "end_confirm"

    # DEFAULT_LABELS = ["center", "left", "right", "up", "down", "blink"]
    
    DEFAULT_LABELS = [
    "center", "left", "right", "up", "down", 
    "blink", "left_blink", "right_blink", "closed"
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
    EAR_THRESHOLD = 0.1
    CONSEC_FRAMES = 3
    blink_counter = 0
    blink_total = 0
    blink_confirmed = False


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


    def detect_gaze(eye_img, blink_confirmed, mesh_points, is_eye_closed, left_ear=None, right_ear=None):
        
        """
            Returns gaze direction with special cases:
            - "left_blink" → left eye closed only
            - "right_blink" → right eye closed only
            - "closed" → both eyes closed
        """
    
        if is_eye_closed:
            return "closed", 100
        
        
        
        
        if blink_confirmed:
            return "blink", accuracy
        # elif (left_ear < EAR_CLOSED and right_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN)) and (left_ear < EAR_CLOSED and right_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN)) :
        #     return "--"
        # elif left_ear < EAR_CLOSED and right_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN):
        #     _click_debounced("left")   # trigger left click
        #     return "left_blink", 100

        # elif right_ear < EAR_CLOSED and left_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN):
        #     _click_debounced("right")  # trigger right click
        #     return "right_blink", 100
        elif left_ear < EAR_CLOSED and right_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN):
            _click_debounced("left")
            return "left_blink", 100

        elif right_ear < EAR_CLOSED and left_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN):
            _click_debounced("right") 
            return "right_blink", 100



            
        
        
        
        # --- Left blink (wink) ---
        # if left_ear is not None and right_ear is not None:
        #     if left_ear < EAR_CLOSED and right_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN):
        #         return "left_blink", 100

        # --- Right blink (wink) ---
        # if right_ear < EAR_CLOSED and left_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN):
        #     return "right_blink", 100
        
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
        print("Horizontal offset Right            : ", right_eye_horizontal_offset)
            
            # ==============Left Eye Gaze Detection========================
        left_eye_center_x = (mesh_points[362][0] + mesh_points[263][0]) // 2
        left_iris_center_x = (mesh_points[476][0] + mesh_points[474][0]) // 2
        left_eye_horizontal_offset = left_iris_center_x - left_eye_center_x
        print("Horizontal offset Left             : ", left_eye_horizontal_offset)
        
            
            
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
        
        print("Right Eye Vertical Offset for DOWN : ", left_eye_offset_y)
        print("Left Eye Vertical Offset for DOWN  : ", right_eye_offset_y)
        
        
        print("Right Eye Vertical Offset for UP   : ", delta_r_y)
        print("Left Eye Vertical Offset for UP    : ", delta_l_y)
        

        
        landmark_up_boolean = False
        landmark_down_boolean = False
        
        
        
        # if (right_eye_horizontal_offset >= LEFT_THRESHOLD) and (left_eye_horizontal_offset >= LEFT_THRESHOLD):
        #     landmark_left_boolean = True
        #     print("Looking LEFT (Landmarks)")
        # elif (right_eye_horizontal_offset <= RIGHT_THRESHOLD) and (left_eye_horizontal_offset <= RIGHT_THRESHOLD):
        #     landmark_right_boolean = True
        #     print("Looking RIGHT (Landmarks)")
        # elif delta_r_y <= UP_THRESHOLD and delta_l_y <= UP_THRESHOLD:
        #     landmark_up_boolean = True
        #     print("Looking UP (Landmarks)")
        # elif left_eye_offset_y > DOWN_THRESHOLD and right_eye_offset_y > DOWN_THRESHOLD:
        #     landmark_down_boolean = True
        #     print("Looking DOWN (Landmarks)")
        # elif (RIGHT_THRESHOLD < right_eye_horizontal_offset < LEFT_THRESHOLD) and (RIGHT_THRESHOLD < left_eye_horizontal_offset < LEFT_THRESHOLD):
        #     landmark_center_boolean = True
        #     print("Looking CENTER (Landmarks)")
        
        if (RIGHT_THRESHOLD < right_eye_horizontal_offset < LEFT_THRESHOLD) and (RIGHT_THRESHOLD < left_eye_horizontal_offset < LEFT_THRESHOLD):
            landmark_center_boolean = True
            print("Looking CENTER (Landmarks)")
        elif left_eye_offset_y > DOWN_THRESHOLD and right_eye_offset_y > DOWN_THRESHOLD:
            landmark_down_boolean = True
            print("Looking DOWN (Landmarks)")
        if (right_eye_horizontal_offset >= LEFT_THRESHOLD) and (left_eye_horizontal_offset >= LEFT_THRESHOLD):
            landmark_left_boolean = True
            print("Looking LEFT (Landmarks)")
        elif (right_eye_horizontal_offset <= RIGHT_THRESHOLD) and (left_eye_horizontal_offset <= RIGHT_THRESHOLD):
            landmark_right_boolean = True
            print("Looking RIGHT (Landmarks)")
        elif delta_r_y <= UP_THRESHOLD and delta_l_y <= UP_THRESHOLD:
            landmark_up_boolean = True
            print("Looking UP (Landmarks)")
        
        


            
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
            
        

        if gaze == "down" or landmark_down_boolean:
            gaze = "down"
            print("Final Gaze direction: ", gaze)
        elif gaze == "center" or landmark_center_boolean:
            gaze = "center"
            print("Final Gaze direction: ", gaze)       
        elif gaze == "right" and landmark_right_boolean:
            gaze = "right"
            print("Final Gaze direction: ", gaze)
        elif gaze == "up" :
            gaze = "up"
            print("Final Gaze direction: ", gaze)      
        elif gaze == "left" and landmark_left_boolean:
            gaze = "left"
            print("Final Gaze direction: ", gaze)
        else:
            gaze = "center"
            print("Final Gaze direction: ", gaze)

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




    cap = cv2.VideoCapture(1)

    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from webcam")
        exit()

    # Set resolution for virtual camera
    height, width = frame.shape[:2]


    frames_to_blink = 6
    blinking_frames = 0
    last_prediction_time = time.time()
    blink_start_time = None

        
    # Define the window as resizable
    cv2.namedWindow("result", cv2.WINDOW_NORMAL)

            # Get screen size
    screen_width = pyautogui.size().width
    screen_height = pyautogui.size().height

            # Calculate 3/4 width and keep height proportional or fixed
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.75)  # Or use a fixed value

            # Resize the OpenCV window
    cv2.resizeWindow("result", window_width, window_height)

            # Optional: move window to center
    x_pos = (screen_width - window_width) // 2
    y_pos = (screen_height - window_height) // 2
    cv2.moveWindow("result", x_pos, y_pos)

    while cap.isOpened():
        
        
        # swap your compose_ui(...) with this one
        def compose_ui(frame: np.ndarray,
                eye_left_view: np.ndarray,
                eye_right_view: np.ndarray,
                gaze: str, acc: int, blink_total: int, fps: float) -> np.ndarray:
            """
                Wider layout + title icon.
                • Full-width title bar with icon on the left and FPS on the right
                • Wide strip above the video (eye thumbnails on the left, badges on the right)
                • Video centered and as wide as possible
            """
            H, W = UI_H, UI_W
            canvas = np.full((H, W, 3), COL["bg"], np.uint8)

            # -------- Title bar --------
            draw_card(canvas, 0, 0, W, TITLE_BAR_H, radius=0, color=COL["card2"], shadow=False)

            # Icon + title text
            x_title = MARGIN_X
            if _icon_rgba is not None:
                _paste_rgba(canvas, _icon_rgba, x_title, 10, w=40, h=40, radius=8)
                x_title += 48 + 10  # icon width + spacing

            put_text(canvas, "REAL TIME GAZE ESTIMATION", (x_title, 46), 1.1, COL["text"], 3)
            put_text(canvas, f"{fps:.1f} FPS", (W - MARGIN_X, 46), 0.9, COL["muted"], 2, align="right")

            # -------- Compute available area for strip + video --------
            y_top = TITLE_BAR_H + MARGIN_Y
            # We'll center the video; the strip will align to the video's width
            # Make the video as wide as possible inside margins
            fh, fw = frame.shape[:2]
            max_w = W - 2*MARGIN_X
            max_h = H - y_top - MARGIN_Y - STRIP_H - 24  # space for strip + spacing

            scale = min(max_w / fw, max_h / fh)
            vw, vh = int(fw * scale), int(fh * scale)

            # video position (center horizontally)
            vx = (W - vw) // 2
            # strip sits above; add small gap (16)
            strip_y = y_top
            strip_x = vx - 16
            strip_w = vw + 32
            strip_h = STRIP_H

            # -------- Top strip (eyes left, badges right) --------
            draw_card(canvas, strip_x, strip_y, strip_w, strip_h, radius=18, color=COL["card2"])

            # Eye thumbs (bigger to match the wider strip)
            thumb_h, thumb_w = strip_h - 28, 220
            pad = 16
            tx = strip_x + pad
            ty = strip_y + (strip_h - thumb_h) // 2

            def _place_thumb(src, x, y, label):
                if src is None:
                    return x
                th = cv2.resize(src, (thumb_w, thumb_h))
                if th.ndim == 2:
                    th = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
                sub = canvas[y:y+thumb_h, x:x+thumb_w]
                tmask = _rounded_rect_mask(thumb_h, thumb_w, 10)
                sub[:] = np.where(tmask[..., None] == 255, th, sub)
                put_text(canvas, label, (x, y-6), 0.65, COL["muted"])
                return x + thumb_w + 12

            tx = _place_thumb(eye_left_view,  tx, ty, "Left")
            tx = _place_thumb(eye_right_view, tx, ty, "Right")

            # Badges on the right end of strip
            bx = strip_x + strip_w - pad
            by = strip_y + 16
            acc_txt = f"{acc}%"
            gaze_txt = gaze.upper()

            def _badge_wh(text):
                size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
                return size[0] + 2*12, size[1] + 2*10

            acc_w, acc_h = _badge_wh(acc_txt)
            gaze_w, gaze_h = _badge_wh(gaze_txt)

            draw_card(canvas, bx-acc_w, by, acc_w, acc_h, radius=14, color=COL["accent"])
            put_text(canvas, acc_txt, (bx-acc_w+12, by+acc_h-12), 0.75, (255,255,255), 2)
            bx -= (acc_w + 12)
            draw_card(canvas, bx-gaze_w, by, gaze_w, gaze_h, radius=14, color=COL["accent2"])
            put_text(canvas, gaze_txt, (bx-gaze_w+12, by+gaze_h-12), 0.75, (255,255,255), 2)
            
            
                    # --- Click badges (live) just below the gaze/accuracy badges ---
            # layout
            now = time.time()
            flash = (now < _last_click_flash_until)

            row_y = by + max(acc_h, gaze_h) + 10
            gap = 10

            # Left-click badge
            left_text = f"L: {left_click_count}"
            left_w, left_h = _badge_wh(left_text)

            # Right-click badge
            right_text = f"R: {right_click_count}"
            right_w, right_h = _badge_wh(right_text)

            # Choose colors; flash the one that was clicked last
            left_bg  = COL["accent2"] if flash and (_last_click_side in ("left", "left_dbl")) else COL["accent"]
            right_bg = COL["accent2"] if flash and (_last_click_side == "right") else COL["accent"]

            # place from right edge inward, under existing badges
            # first right badge
            draw_card(canvas, bx-right_w, row_y, right_w, right_h, radius=14, color=right_bg)
            put_text(canvas, right_text, (bx-right_w+12, row_y+right_h-12), 0.75, (255,255,255), 2)
            bx -= (right_w + gap)

            # then left badge
            draw_card(canvas, bx-left_w, row_y, left_w, left_h, radius=14, color=left_bg)
            put_text(canvas, left_text, (bx-left_w+12, row_y+left_h-12), 0.75, (255,255,255), 2)
            # done; bx now points to left of click badges


            # -------- Video card (just below the strip) --------
            vy = strip_y + strip_h + 8
            draw_card(canvas, vx - 16, vy - 16, vw + 32, vh + 12, radius=20, color=COL["card"])
            resized = cv2.resize(frame, (vw, vh))
            mask = _rounded_rect_mask(vh, vw, 16)
            roi = canvas[vy:vy+vh, vx:vx+vw]
            roi[:] = np.where(mask[..., None] == 255, resized, roi)

            # overlay small gradient & blink count
            overlay = roi.copy()
            grad = np.linspace(110, 0, 110).astype(np.uint8)
            grad = np.repeat(grad[:, None], vw, axis=1)
            grad = cv2.merge([grad, grad, grad])
            overlay[0:110] = cv2.addWeighted(overlay[0:110], 1.0, grad, 0.55, 0)
            roi[:] = overlay

            put_text(canvas, f"Blinks: {blink_total}", (vx+20, vy+40), 0.8, COL["text"], 2)

            return canvas


        output = np.zeros((900,820,3), dtype="uint8")
        ret, img = cap.read()
        h, w = (112, 128)
        if not ret:
            break
        
        # UI-only mirror
        display = cv2.flip(img, 1)

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

        # If no usable landmarks, render UI and continue
        if mesh_points is None:
            if 't_prev' not in globals():
                t_prev = time.perf_counter()
            fps = 1.0 / max(1e-6, (time.perf_counter() - t_prev))
            t_prev = time.perf_counter()

            ui = compose_ui(
                frame=display,
                eye_left_view=None,
                eye_right_view=None,
                gaze="--",
                acc=0,
                blink_total=blink_total,
                fps=fps
            )
            cv2.imshow("result", ui)
            if cv2.waitKey(1) in (ord('q'), ord('Q')): break
            continue

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
                frame=display,
                eye_left_view=None,
                eye_right_view=None,
                gaze="--",
                acc=0,
                blink_total=blink_total,
                fps=fps
            )
            cv2.imshow("result", ui)
            if cv2.waitKey(1) in (ord('q'), ord('Q')): break
            continue

        # Now it’s safe to use EAR values
        avg_ear = (left_ear + right_ear) / 2
        is_eye_closed = avg_ear < EAR_THRESHOLD
        
        wink_in_progress = (_left_wink_start is not None) or (_right_wink_start is not None)
        both_closed_now  = (left_ear < EAR_CLOSED) and (right_ear < EAR_CLOSED)

        # time-based quiet period
        now = time.time()
        time_quiet = (now < _suppress_until_ts)

        # suppress_gaze = is_eye_closed and both_closed_now or wink_in_progress or time_quiet    
            
        


        # --- Robust wink + long-blink handling ---
        t = time.monotonic()

        # Hysteresis booleans
        left_closed  = (left_ear  < EAR_CLOSED)
        right_closed = (right_ear < EAR_CLOSED)
        left_open    = (left_ear  > EAR_OPEN_HYST)
        right_open   = (right_ear > EAR_OPEN_HYST)

        # 1) LEFT-EYE WINK → LEFT CLICK
        # left must be closed; right must be clearly open
        if left_closed and (right_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN)):
            if _left_wink_start is None:
                _left_wink_start = t
        else:
            if _left_wink_start is not None and left_open and right_open:
                dur = t - _left_wink_start
                if WINK_MIN_SEC <= dur <= WINK_MAX_SEC:
                    # _click_debounced("left")
                    _double_click_debounced()
                    _suppress_until_ts = time.time() + SUPPRESS_AFTER_BLINK_SEC
            _left_wink_start = None

        # 2) RIGHT-EYE WINK → RIGHT CLICK
        # right must be closed; left must be clearly open
        if right_closed and (left_ear > (EAR_OPEN_HYST + WINK_OPEN_MARGIN)):
            if _right_wink_start is None:
                _right_wink_start = t
        else:
            if _right_wink_start is not None and left_open and right_open:
                dur = t - _right_wink_start
                if WINK_MIN_SEC <= dur <= WINK_MAX_SEC:
                    _click_debounced("right")
                    _suppress_until_ts = time.time() + SUPPRESS_AFTER_BLINK_SEC
            _right_wink_start = None

        # 3) BOTH EYES CLOSED LONG (≥ LONG_BLINK_SEC) → WARP TO NEXT EDGE MIDPOINT
        both_closed = left_closed and right_closed
        both_open   = left_open and right_open

        if both_closed:
            if long_blink_start is None:
                long_blink_start = t
            else:
                held = t - long_blink_start
                if long_blink_armed and (t >= long_blink_cooldown_until) and held >= LONG_BLINK_SEC:
                    _warp_to_next_anchor()
                    winsound.Beep(1200, 120)  # optional audio cue
                    blink_total += 1 
                    long_blink_armed = False
                    _suppress_until_ts = time.time() + SUPPRESS_AFTER_BLINK_SEC
                    long_blink_cooldown_until = t + LONG_BLINK_COOLDOWN
        else:
            # only fully reopen re-arms; flutter won't reset timer
            if both_open:
                long_blink_start = None
                if not long_blink_armed and (t >= long_blink_cooldown_until):
                    long_blink_armed = True

        if not results.multi_face_landmarks:
            cv2.imshow("result", output)  # or whatever you draw
            if cv2.waitKey(1) in (ord('q'), ord('Q')): break
            continue

            
            
        if avg_ear < EAR_THRESHOLD:
            # Eyes likely closed — treat only as potential blink, NOT gaze
            is_eye_closed = True
        else:
            is_eye_closed = False
            
            
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

        # Use hysteresis: must be *firmly* closed to count, *firmly* open to reset
        both_closed = (left_ear < EAR_CLOSED) and (right_ear < EAR_CLOSED)
        both_open   = (left_ear > EAR_OPEN_HYST) and (right_ear > EAR_OPEN_HYST)

        if both_closed:
            if long_blink_start is None:
                long_blink_start = t
                # debug
                print(f"[long-blink] timer started at {long_blink_start:.2f}")
            else:
                held = t - long_blink_start
                if long_blink_armed and (t >= long_blink_cooldown_until) and held >= LONG_BLINK_SEC:
                    # cycle anchors: center → left → top → right → bottom → center...
                    _warp_to_next_anchor()
                    winsound.Beep(1200, 120)
                    print(f"[long-blink] WARP after {held:.2f}s")
                    long_blink_armed = False
                    long_blink_cooldown_until = t + LONG_BLINK_COOLDOWN
        else:
            # only fully reopen re-arms; minor eyelid flutter won't reset timer
            if both_open:
                long_blink_start = None
                if not long_blink_armed and (t >= long_blink_cooldown_until):
                    long_blink_armed = True
                    print("[long-blink] re-armed")





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
            
            
            
            
            #=================PREDICTION PROCESS========================================

            gaze, accuracy = detect_gaze(
                eye_input_g, 
                blink_confirmed, 
                mesh_points, 
                is_eye_closed,
                left_ear=left_ear,
                right_ear=right_ear
            )



            # Only allow new gaze prediction after a short interval      
            # if (gaze in ("left", "right", "up", "down")):
            #     move_cursor_for_gaze(gaze, accuracy)

            
        
            # Move mouse (function has its own cooldown & accuracy gate)
            if not is_eye_closed and gaze in ("left", "right", "up", "down"):
                move_cursor_for_gaze(gaze, accuracy)
            

            if gaze == class_labels[1]:
                blinking_frames += 1
                if blinking_frames == frames_to_blink:
                    winsound.Beep(1000,250)
            elif gaze == class_labels[2]:
                blinking_frames += 1
                if blinking_frames == frames_to_blink:
                    winsound.Beep(1000,250)
            else:
                blinking_frames = 0
                
                
                
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
            blink_confirmed = False
            
            
            # --- FPS calculation ---
            if 't_prev' not in globals():
                t_prev = time.perf_counter()
            fps = 1.0 / max(1e-6, (time.perf_counter() - t_prev))
            t_prev = time.perf_counter()

            # --- Compose polished UI ---
            ui = compose_ui(
                frame=display,  
                # your camera frame (BGR)
                eye_left_view=eye_img_r_view,
                eye_right_view=eye_img_l_view,
                gaze=gaze,
                acc=accuracy,
                blink_total=blink_total,
                fps=fps
            )

            cv2.imshow("result", ui)
            
                    
        if cv2.waitKey(1) == ord('q') or cv2.waitKey(1) == ord('Q') : 
            break
    cap.release()
    cv2.destroyAllWindows()    


if __name__ == "__main__":
    # start the dictation listener
    main()
    start_voice_autodictation()