import cv2
import json
import time
import os

from core.camera import Camera
from core.tracker import HandTracker
from core.gestures import detect_gesture, get_pinch_ratio
from core.smoothing import PointSmoother
from core.state import StateManager
from core.biomechanics import get_hand_joint_angles, draw_biomechanics_overlay, create_clinical_dashboard

from actions.mouse import MouseController
from actions.system import SystemController
from actions.apps import AppLauncher

from ui.settings import SettingsUI

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (9, 10), (10, 11), (11, 12),
    # Ring finger
    (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm knuckles & wrist
    (5, 9), (9, 13), (13, 17)
]

def draw_info(frame, state_manager, gesture, pinch_ratio, scroll_status="", show_rom=True):
    # Minimal top indicator on the camera frame
    state_color = (0, 255, 0) if state_manager.is_active else (80, 80, 220)
    cv2.circle(frame, (20, 25), 8, state_color, -1)
    status_msg = "TRACKING ACTIVE" if state_manager.is_active else "STANDBY (Open hand 2s to activate)"
    cv2.putText(frame, status_msg, (35, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

    if scroll_status:
        cv2.putText(frame, scroll_status, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)

def main():
    config = load_config()
    
    print("Initializing camera...")
    cam = Camera(
        src=config["camera"]["index"], 
        width=config["camera"]["width"], 
        height=config["camera"]["height"], 
        fps=config["camera"]["fps"]
    ).start()
    
    print("Initializing hand tracker...")
    tracker = HandTracker()
    
    smoother = PointSmoother(
        min_cutoff=config["smoothing"]["min_cutoff"], 
        beta=config["smoothing"]["beta"]
    )
    state = StateManager(config)
    
    mouse = MouseController(config)
    system = SystemController()
    apps = AppLauncher(config)
    
    ui = SettingsUI(config, state)
    ui.start()
    
    print("App started. Press 'q' in the preview window or Ctrl+C in console to quit.")
    print("Press 'r' in the preview window to toggle Joint Range of Motion (ROM) tracking.")
    
    show_rom = config.get("tracking", {}).get("show_joint_angles", True)
    
    window_name = "Gesture PC Control"
    if config["tracking"].get("show_preview", True):
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        try:
            import pyautogui
            screen_w, screen_h = pyautogui.size()
            win_w, win_h = 480, 360
            win_x = max(0, screen_w - win_w - 20)
            win_y = 45
            cv2.resizeWindow(window_name, win_w, win_h)
            cv2.moveWindow(window_name, win_x, win_y)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass
            
    prev_scroll_y = None
    
    try:
        while True:
            grabbed, frame = cam.read()
            if not grabbed:
                time.sleep(0.01)
                continue
                
            landmarks = tracker.process(frame)
            current_time = time.time()
            scroll_status = ""
            
            if landmarks:
                gesture = detect_gesture(landmarks, config["gestures"]["pinch_threshold_press"])
                pinch_ratio = get_pinch_ratio(landmarks)
                
                triggered, toggled = state.update_gesture(gesture, current_time)
                
                raw_x = landmarks[8].x
                raw_y = landmarks[8].y
                smooth_x, smooth_y = smoother(raw_x, raw_y)
                
                if state.is_active:
                    pinch_action = state.update_pinch(pinch_ratio)
                    
                    # Move cursor only when pointing and NOT in middle of clicking
                    if gesture == "POINT" and not state.pinch_active:
                        mouse.move(smooth_x, smooth_y)
                        
                    # Instant clean click when pinch starts
                    if pinch_action == "PRESS":
                        mouse.click("left")
                        print(">>> CLICKED!")
                        
                    # Smooth two-finger scrolling
                    if gesture == "TWO_FINGERS":
                        scroll_cfg = config.get("scroll", {})
                        invert = scroll_cfg.get("invert_direction", True)
                        mult = -1 if invert else 1
                        speed_mult = scroll_cfg.get("speed_multiplier", 1.5)
                        
                        if prev_scroll_y is not None:
                            dy = prev_scroll_y - smooth_y
                            if abs(dy) > 0.005:
                                # When inverted: moving hand down (dy < 0) sends positive scroll (scrolling page down on Mac)
                                steps = int(dy * 50 * mult * speed_mult)
                                if steps == 0:
                                    steps = 2 if (dy * mult) > 0 else -2
                                mouse.scroll(steps)
                                scroll_status = "SCROLL DOWN ⬇️" if dy < 0 else "SCROLL UP ⬆️"
                            elif smooth_y > 0.62:
                                # Holding hand in lower zone -> scroll page down
                                mouse.scroll(int(4 * speed_mult * abs(mult)))
                                scroll_status = "SCROLL DOWN ⬇️"
                            elif smooth_y < 0.38:
                                # Holding hand in upper zone -> scroll page up
                                mouse.scroll(int(-4 * speed_mult * abs(mult)))
                                scroll_status = "SCROLL UP ⬆️"
                        prev_scroll_y = smooth_y
                    else:
                        prev_scroll_y = None
                        
                    if triggered:
                        if gesture == "FIST":
                            mouse.click("right")
                            state.set_cooldown("FIST")
                        elif gesture == "THREE_FINGERS":
                            system.set_volume(smooth_y)
                            
            else:
                gesture = "NONE"
                pinch_ratio = 1.0
                prev_scroll_y = None
                state.update_gesture(gesture, current_time)
                time.sleep(0.01)
                
            if config["tracking"].get("show_preview", True):
                if landmarks:
                    h, w, _ = frame.shape
                    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
                    
                    # Draw skeleton lines for ALL fingers (Yellow)
                    for start_idx, end_idx in HAND_CONNECTIONS:
                        if start_idx < len(pts) and end_idx < len(pts):
                            cv2.line(frame, pts[start_idx], pts[end_idx], (0, 255, 255), 2)
                            
                    # Draw joints on all landmarks
                    for idx, pt in enumerate(pts):
                        r = 5 if idx in [4, 8, 12, 16, 20] else 3
                        cv2.circle(frame, pt, r, (0, 200, 255), -1)
                        
                    # Pinch line between thumb tip (4) and index tip (8)
                    pinch_col = (0, 255, 0) if state.pinch_active else (0, 255, 255)
                    cv2.line(frame, pts[4], pts[8], pinch_col, 3 if state.pinch_active else 2)
                    cv2.circle(frame, pts[4], 7, pinch_col, -1)
                    cv2.circle(frame, pts[8], 7, pinch_col, -1)

                    # Biomechanics / Range of Motion (ROM) Joint Angle tracking
                    if show_rom:
                        joint_angles = get_hand_joint_angles(landmarks)
                        draw_biomechanics_overlay(frame, landmarks, joint_angles)
                    else:
                        joint_angles = {}
                else:
                    joint_angles = {}
                
                draw_info(frame, state, gesture, pinch_ratio, scroll_status, show_rom=show_rom)
                
                # Draw subtle active zone boundary
                h, w, _ = frame.shape
                mx, my = config["tracking"]["active_zone_margin_x"], config["tracking"]["active_zone_margin_y"]
                cv2.rectangle(frame, (int(w*mx), int(h*my)), (int(w*(1-mx)), int(h*(1-my))), (100, 100, 100), 1)
                
                # Side-by-Side Split Window (Dashboard Style)
                if show_rom:
                    view_type = joint_angles.get("View", "FRONT")
                    dashboard_panel = create_clinical_dashboard(
                        h=h,
                        angles=joint_angles,
                        view_type=view_type,
                        state_active=state.is_active,
                        gesture=gesture,
                        pinch_ratio=pinch_ratio
                    )
                    display_frame = cv2.hconcat([frame, dashboard_panel])
                else:
                    display_frame = frame
                
                cv2.imshow("Gesture PC Control", display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    show_rom = not show_rom
                    print(f"ROM Dashboard: {'ENABLED' if show_rom else 'DISABLED'}")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        cam.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

# Vercel entrypoint fallback (if inspected by Vercel serverless runtime)
def handler(request=None, response=None):
    return {"status": 200, "message": "NeuroRehab Web Active"}

app = handler
application = handler
