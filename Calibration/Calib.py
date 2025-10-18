import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import json
import time
import os

# Initialize camera and FaceMesh
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()

# Automatically detect the root GazeDesktop directory and save to the outer Data folder
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level from Calibration/
data_dir = os.path.join(base_dir, "Data")
os.makedirs(data_dir, exist_ok=True)
output_path = os.path.join(data_dir, "threshold.json")


# Helper function to show calibration screen with red circle
def show_calibration_screen(position="left", duration=5):
    white_screen = np.ones((screen_h, screen_w, 3), dtype=np.uint8) * 255
    radius = 15

    # Position the red circle depending on direction
    if position == "left":
        center_x = int(screen_w * 0.005)
        center_y = int(screen_h / 2)
    elif position == "right":
        center_x = int(screen_w * 0.995)
        center_y = int(screen_h / 2)
    elif position == "up":
        center_x = screen_w // 2
        center_y = int(screen_h * 0.005)
    elif position == "down":
        center_x = screen_w // 2
        center_y = int(screen_h * 0.995)
    else:
        center_x = screen_w // 2
        center_y = screen_h // 2

    cv2.circle(white_screen, (center_x, center_y), radius, (0, 0, 255), -1)

    cv2.namedWindow("Calibration", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("Calibration", white_screen)

    values = {"left_eye": [], "right_eye": []}
    start_time = time.time()

    while time.time() - start_time < duration:
        _, frame = cam.read()
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        landmark_points = output.multi_face_landmarks

        if landmark_points:
            landmarks = landmark_points[0].landmark

            if position == "left":
                # Left Eye horizontal distance (471 - 33)
                left_left_x1 = landmarks[33].x
                left_left_x2 = landmarks[471].x
                left_dist = left_left_x2 - left_left_x1
                values["left_eye"].append(left_dist)

                # Right Eye horizontal distance (474 - 362)
                right_left_x1 = landmarks[474].x
                right_left_x2 = landmarks[362].x
                right_dist = right_left_x1 - right_left_x2
                values["right_eye"].append(right_dist)

            elif position == "right":
                # Left Eye horizontal distance (133 - 469)
                left_right_x1 = landmarks[469].x
                left_right_x2 = landmarks[133].x
                left_dist = left_right_x2 - left_right_x1
                values["left_eye"].append(left_dist)

                # Right Eye horizontal distance (263 - 469)
                right_right_x1 = landmarks[469].x
                right_right_x2 = landmarks[263].x
                right_dist = right_right_x2 - right_right_x1
                values["right_eye"].append(right_dist)

            elif position == "up":
                # Left Eye vertical distance (159 - 470)
                left_up_y1 = landmarks[470].y
                left_up_y2 = landmarks[159].y
                left_dist = (left_up_y2 - left_up_y1) + 0.001
                values["left_eye"].append(left_dist)

                # Right Eye vertical distance (386 - 475)
                right_up_y1 = landmarks[475].y
                right_up_y2 = landmarks[386].y
                right_dist = (right_up_y2 - right_up_y1)+ 0.001
                values["right_eye"].append(right_dist)

            elif position == "down":
                # Left Eye vertical distance (145 - 159)
                left_down_y1 = landmarks[159].y
                left_down_y2 = landmarks[145].y
                left_dist = left_down_y2 - left_down_y1
                values["left_eye"].append(left_dist)

                # Right Eye vertical distance (374 - 386)
                right_down_y1 = landmarks[386].y
                right_down_y2 = landmarks[374].y
                right_dist = right_down_y2 - right_down_y1
                values["right_eye"].append(right_dist)

        cv2.imshow("Calibration", white_screen)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyWindow("Calibration")

    if values["left_eye"] and values["right_eye"]:
        avg_left = sum(values["left_eye"]) / len(values["left_eye"])
        avg_right = sum(values["right_eye"]) / len(values["right_eye"])
        return avg_left, avg_right
    else:
        return None, None


# ---------- Step 1: LEFT EDGE ----------
print("\n🟢 Step 1: Look at the red dot on the LEFT edge...")
left_avg_left, left_avg_right = show_calibration_screen("left", duration=5)

# ---------- Step 2: RIGHT EDGE ----------
print("\n🟢 Step 2: Look at the red dot on the RIGHT edge...")
right_avg_left, right_avg_right = show_calibration_screen("right", duration=5)

# ---------- Step 3: UP EDGE ----------
print("\n🟢 Step 3: Look at the red dot on the TOP edge...")
up_avg_left, up_avg_right = show_calibration_screen("up", duration=5)

# ---------- Step 4: DOWN EDGE ----------
print("\n🟢 Step 4: Look at the red dot on the BOTTOM edge...")
down_avg_left, down_avg_right = show_calibration_screen("down", duration=5)

# ---------- Save Results ----------
if all(v is not None for v in [
    left_avg_left, left_avg_right,
    right_avg_left, right_avg_right,
    up_avg_left, up_avg_right,
    down_avg_left, down_avg_right
]):
    data = {
        "left_eye_horizontal_threshold_left_direction": left_avg_left,
        "right_eye_horizontal_threshold_left_direction": left_avg_right,
        "left_eye_horizontal_threshold_for_right_direction": right_avg_left,
        "right_eye_horizontal_threshold_for_right_direction": right_avg_right,
        "left_eye_vertical_threshold_for_up_direction": up_avg_left,
        "right_eye_vertical_threshold_for_up_direction": up_avg_right,
        "left_eye_vertical_threshold_for_down_direction": down_avg_left,
        "right_eye_vertical_threshold_for_down_direction": down_avg_right
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)

    print("\n✅ Calibration complete!")
    for key, val in data.items():
        print(f"{key}: {val}")
    print(f"\n📁 Saved to {output_path}")
else:
    print("⚠️ Some calibration data missing. Please retry.")

# Release resources
cam.release()
cv2.destroyAllWindows()
