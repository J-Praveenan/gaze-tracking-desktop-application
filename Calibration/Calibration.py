import cv2
import time
import json
import numpy as np
import mediapipe as mp
from pathlib import Path
import ctypes
from utils.common import speak

# ==============================
# Config
# ==============================
SAMPLE_TARGET_PER_POINT = 60
MIN_FACE_DETECTIONS = 20
CALIBRATION_HOLD_SEC = 3
FPS_THROTTLE = 60
WINDOW_NAME = "Calibration"

# ==============================
# Screen size
# ==============================
def get_screen_size():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080

SCREEN_W, SCREEN_H = get_screen_size()
MARGIN_PCT = 0.01
mx, my = int(SCREEN_W * MARGIN_PCT), int(SCREEN_H * MARGIN_PCT)

def build_cal_points(w, h, margin_x, margin_y):
    cx, cy = w // 2, h // 2
    return {
        "CENTER": (cx, cy),
        "LEFT": (margin_x, cy),
        "RIGHT": (w - margin_x, cy),
        "UP": (cx, margin_y),
        "DOWN": (cx, h - margin_y),
    }

CAL_POINTS = build_cal_points(SCREEN_W, SCREEN_H, mx, my)

# ==============================
# Drawing Helpers
# ==============================
def put_center_text(img, text, y, fs, thick, color=(0, 0, 0)):
    tsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, thick)[0]
    cv2.putText(img, text, ((img.shape[1] - tsize[0]) // 2, y),
                cv2.FONT_HERSHEY_SIMPLEX, fs, color, thick, cv2.LINE_AA)

def draw_calibration_screen(point_name: str, secs_left: int):
    canvas = np.ones((SCREEN_H, SCREEN_W, 3), dtype=np.uint8) * 255
    # cv2.circle(canvas, CAL_POINTS[point_name], 30, (0, 0, 255), -1)
    center = CAL_POINTS[point_name]
    # Draw black border (slightly larger circle)
    cv2.circle(canvas, center, 22, (0, 0, 0), -1, lineType=cv2.LINE_AA)
    
    # Draw inner red filled circle
    cv2.circle(canvas, center, 18, (0, 0, 255), -1, lineType=cv2.LINE_AA)
    put_center_text(canvas, f"Look at the {point_name} point", SCREEN_H // 2, 1.5, 3)
    put_center_text(canvas, f"Hold steady… {secs_left}s", SCREEN_H - 120, 1.2, 2)
    return canvas

# ==============================
# MediaPipe Setup
# ==============================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
)

# ==============================
# Save thresholds
# ==============================
def save_thresholds(thresholds: dict):
    out_dir = Path("Data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "gaze_thresholds.json"
    with open(out_path, "w") as f:
        json.dump(thresholds, f, indent=4)
    return str(out_path)

# ==============================
# Main Calibration
# ==============================
def calibrate_gaze():
    # ==========================
    # Load saved camera index
    # ==========================
    config_path = Path("Data") / "configuration.json"
    camera_index = 0  # default fallback

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                camera_index = config.get("camera", {}).get("index", 0)
        except Exception as e:
            print("⚠️ Failed to read configuration.json, using default camera (0):", e)

    # ==========================
    # Open the selected camera
    # ==========================
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera (index {camera_index}).")

    cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    thresholds = {}
    directions = ["LEFT", "RIGHT", "UP", "DOWN", "CLOSED"]

    try:
        for direction in directions:
            # --- Countdown phase ---
            start = time.time()
    
            if direction == "CLOSED":
                speak(f"Close both eyes for {CALIBRATION_HOLD_SEC} seconds")
            else:
                speak(f"Look at the {direction} point and hold steady for {CALIBRATION_HOLD_SEC} seconds")

                
            
            while True:
                secs_left = max(0, CALIBRATION_HOLD_SEC - int(time.time() - start))
                
            
                if direction == "CLOSED":
                    canvas = np.ones((SCREEN_H, SCREEN_W, 3), dtype=np.uint8) * 255
                    put_center_text(canvas, "Close both eyes for 3 seconds", SCREEN_H // 2, 1.5, 3)
                    put_center_text(canvas, f"Hold steady… {secs_left}s", SCREEN_H - 120, 1.2, 2)
                else:
                    canvas = draw_calibration_screen(direction, secs_left)

                # canvas = draw_calibration_screen(direction, secs_left)
                cv2.imshow(WINDOW_NAME, canvas)
                if cv2.waitKey(16) & 0xFF == 27:
                    raise KeyboardInterrupt
                if time.time() - start >= CALIBRATION_HOLD_SEC:
                    break

            # --- Data collection ---
            collected = []
            last_ts = 0.0
            while len(collected) < SAMPLE_TARGET_PER_POINT:
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
                landmarks = np.array([(p.x, p.y) for p in mesh.landmark])

                # Compute values depending on direction
                try:
                    if direction == "LEFT":
                        left_val = landmarks[263][0] - landmarks[473][0]
                        right_val = landmarks[133][0] - landmarks[468][0]
                    elif direction == "RIGHT":
                        left_val = landmarks[473][0] - landmarks[362][0]
                        right_val = landmarks[468][0] - landmarks[33][0]
                    elif direction == "UP":
                        left_val = landmarks[386][1] - landmarks[475][1]
                        right_val = landmarks[159][1] - landmarks[470][1]
                    elif direction == "DOWN":
                        left_val = landmarks[374][1] - landmarks[386][1]
                        right_val = landmarks[145][1] - landmarks[159][1]
                    elif direction == "CLOSED":
                        left_val = landmarks[374][1] - landmarks[386][1]
                        right_val = landmarks[145][1] - landmarks[159][1]
                    else:
                        continue

                    collected.append((left_val, right_val))
                except Exception:
                    continue

            if len(collected) < MIN_FACE_DETECTIONS:
                raise RuntimeError(f"Not enough valid frames for {direction}")

            data = np.array(collected)
            left_avg, right_avg = np.mean(data[:, 0]), np.mean(data[:, 1])

            # Store results in JSON keys
            if direction == "LEFT":
                thresholds["LEFT_EYE_LEFT_DIRECTION_THRESHOLD"] = float(left_avg - 0.0005)
                thresholds["RIGHT_EYE_LEFT_DIRECTION_THRESHOLD"] = float(right_avg - 0.0005)
            elif direction == "RIGHT":
                thresholds["LEFT_EYE_RIGHT_DIRECTION_THRESHOLD"] = float(left_avg - 0.0005)
                thresholds["RIGHT_EYE_RIGHT_DIRECTION_THRESHOLD"] = float(right_avg - 0.0005)
            elif direction == "UP":
                thresholds["LEFT_EYE_UP_DIRECTION_THRESHOLD"] = float(left_avg - 0.0005)
                thresholds["RIGHT_EYE_UP_DIRECTION_THRESHOLD"] = float(right_avg - 0.0005)
            elif direction == "DOWN":
                thresholds["LEFT_EYE_DOWN_DIRECTION_THRESHOLD"] = float(left_avg - 0.005)   # - 0.005
                thresholds["RIGHT_EYE_DOWN_DIRECTION_THRESHOLD"] = float(right_avg - 0.005) # - 0.005
            elif direction == "CLOSED":
                thresholds["LEFT_EYE_CLOSED_THRESHOLD"] = float(left_avg + 0.002) # + 0.003
                thresholds["RIGHT_EYE_CLOSED_THRESHOLD"] = float(right_avg + 0.002) # + 0.003


        out_file = save_thresholds(thresholds)
        cv2.destroyAllWindows()
        print("\n✅ Calibration complete. Thresholds saved to:", out_file)
        
        speak("The calibration process successfully completed.")
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
