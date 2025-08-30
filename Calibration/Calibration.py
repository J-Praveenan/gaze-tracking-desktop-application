# calibration.py
import cv2
import time
import json
import math
import numpy as np
import mediapipe as mp
from pathlib import Path
import ctypes

# ==============================
# Config
# ==============================
SAMPLE_TARGET_PER_POINT = 60          # total samples to collect per direction
MIN_FACE_DETECTIONS = 20              # require at least this many valid frames per point
CALIBRATION_HOLD_SEC = 3              # on-screen hold per point before sampling
FPS_THROTTLE = 60                     # cap read loop to reduce CPU
OUTLIER_STD_CUTOFF = 2.0              # z-score cutoff for outlier removal
WINDOW_NAME = "Calibration"

# ==============================
# Screen size (dynamic) + points
# ==============================
def get_screen_size():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080

SCREEN_W, SCREEN_H = get_screen_size()

MARGIN_PCT = 0.01  # 3% margin
mx = int(SCREEN_W * MARGIN_PCT)
my = int(SCREEN_H * MARGIN_PCT)

def build_cal_points(w, h, margin_x, margin_y):
    cx, cy = w // 2, h // 2
    return {
        "CENTER": (cx, cy),
        "LEFT":   (margin_x, cy),
        "RIGHT":  (w - margin_x, cy),
        "UP":     (cx, margin_y),
        "DOWN":   (cx, h - margin_y),
    }

CAL_POINTS = build_cal_points(SCREEN_W, SCREEN_H, mx, my)

# Scale drawing (relative to 1080p baseline)
BASE_H = 1080.0
SCALE = min(SCREEN_W, SCREEN_H) / BASE_H
R_OUT = max(12, int(22 * SCALE))
R_IN  = max(8,  int(16 * SCALE))
TITLE_FS   = 1.6 * SCALE
COUNT_FS   = 1.4 * SCALE
THICK      = max(2, int(3 * SCALE))

# ==============================
# MediaPipe FaceMesh
# ==============================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
)

# ==============================
# Helpers
# ==============================
def put_center_text(img, text, y, fs, thick, color=(0,0,0)):
    tsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, thick)[0]
    cv2.putText(img, text, ((img.shape[1] - tsize[0]) // 2, y),
                cv2.FONT_HERSHEY_SIMPLEX, fs, color, thick, cv2.LINE_AA)

def draw_calibration_screen(point_name: str, secs_left: int):
    """Fullscreen with dot + instruction + countdown."""
    canvas = np.ones((SCREEN_H, SCREEN_W, 3), dtype=np.uint8) * 255

    # target dot
    cv2.circle(canvas, CAL_POINTS[point_name], R_OUT, (0, 0, 0), -1)
    cv2.circle(canvas, CAL_POINTS[point_name], R_IN,  (0, 0, 255), -1)

    # Instruction text
    title = f"Look at the {point_name} point"
    put_center_text(canvas, title, SCREEN_H // 2, TITLE_FS, THICK, (0, 0, 0))

    # Countdown
    cmsg = f"Hold steady… {secs_left}s"
    put_center_text(canvas, cmsg, SCREEN_H - int(120 * SCALE), COUNT_FS, THICK, (0,0,0))

    return canvas

def get_offsets(mesh_points):
    # Horizontal
    left_eye_center_x  = (mesh_points[362][0] + mesh_points[263][0]) // 2
    left_iris_center_x = (mesh_points[476][0] + mesh_points[474][0]) // 2
    left_offset_x = left_iris_center_x - left_eye_center_x

    right_eye_center_x  = (mesh_points[33][0] + mesh_points[133][0]) // 2
    right_iris_center_x = (mesh_points[469][0] + mesh_points[471][0]) // 2
    right_offset_x = right_iris_center_x - right_eye_center_x

    horizontal = (left_offset_x + right_offset_x) / 2.0

    # Vertical
    right_eye_center_y  = (mesh_points[159][1] + mesh_points[145][1]) // 2
    right_iris_center_y = (mesh_points[470][1] + mesh_points[472][1]) // 2
    up_offset = right_iris_center_y - right_eye_center_y

    left_eye_center_y  = (mesh_points[386][1] + mesh_points[374][1]) // 2
    left_iris_center_y = (mesh_points[475][1] + mesh_points[477][1]) // 2
    down_offset = left_iris_center_y - left_eye_center_y

    vertical = (up_offset + down_offset) / 2.0
    return float(horizontal), float(vertical)

def robust_mean(samples_np):
    mean = np.mean(samples_np, axis=0)
    std = np.std(samples_np, axis=0) + 1e-6
    z = np.abs((samples_np - mean) / std)
    mask = (z <= OUTLIER_STD_CUTOFF).all(axis=-1) if samples_np.ndim == 2 else (z <= OUTLIER_STD_CUTOFF)
    filtered = samples_np[mask]
    if len(filtered) == 0:
        filtered = samples_np
    return np.mean(filtered, axis=0)

def save_thresholds(thresholds: dict):
    out_dir = Path("Data") if Path("Data").exists() else Path(".")
    out_path = out_dir / "gaze_thresholds.json"
    with open(out_path, "w") as f:
        json.dump(thresholds, f, indent=4)
    return str(out_path)

# ==============================
# Main Calibration
# ==============================
def calibrate_gaze():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    thresholds = {}
    directions = ["LEFT", "RIGHT", "UP", "DOWN"]

    try:
        for direction in directions:
            # Show the dot + instruction + countdown
            start = time.time()
            while True:
                secs_left = max(0, CALIBRATION_HOLD_SEC - int(time.time() - start))
                canvas = draw_calibration_screen(direction, secs_left)
                cv2.imshow(WINDOW_NAME, canvas)
                key = cv2.waitKey(16) & 0xFF
                if key == 27:
                    raise KeyboardInterrupt
                if time.time() - start >= CALIBRATION_HOLD_SEC:
                    break

            # Collect samples
            samples = []
            last_ts = 0.0
            while len(samples) < SAMPLE_TARGET_PER_POINT:
                ret, frame = cap.read()
                if not ret:
                    continue

                now = time.time()
                if now - last_ts < (1.0 / max(1, FPS_THROTTLE)):
                    continue
                last_ts = now

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)

                if not results.multi_face_landmarks:
                    continue

                mesh = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                mesh_points = np.array([(int(p.x * w), int(p.y * h)) for p in mesh.landmark])

                try:
                    offsets = get_offsets(mesh_points)
                except Exception:
                    continue

                samples.append(offsets)

            if len(samples) < MIN_FACE_DETECTIONS:
                raise RuntimeError(f"Not enough valid frames for {direction}")

            samples_np = np.array(samples, dtype=np.float32)
            avg_horizontal, avg_vertical = robust_mean(samples_np)

            if direction == "LEFT":
                thresholds["LEFT_THRESHOLD"] = int(math.ceil(avg_horizontal))
            elif direction == "RIGHT":
                thresholds["RIGHT_THRESHOLD"] = int(math.ceil(avg_horizontal))
            elif direction == "UP":
                thresholds["UP_THRESHOLD"] = int(math.ceil(avg_vertical))
            elif direction == "DOWN":
                left_eye_offset_y = mesh_points[386][1] - mesh_points[374][1]
                right_eye_offset_y = mesh_points[159][1] - mesh_points[145][1]
                down_baseline = (left_eye_offset_y + right_eye_offset_y) / 2.0
                thresholds["DOWN_THRESHOLD"] = int(math.ceil(down_baseline))

        out_file = save_thresholds(thresholds)
        cv2.destroyAllWindows()
        print("\n✅ Calibration complete. Thresholds saved to:", out_file)
        print(json.dumps(thresholds, indent=4))
        return thresholds

    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        print("\n⚠️ Calibration cancelled by user.")
        return None
    except Exception as e:
        cv2.destroyAllWindows()
        print("\n❌ Calibration failed:", str(e))
        return None
    finally:
        cap.release()

if __name__ == "__main__":
    calibrate_gaze()
