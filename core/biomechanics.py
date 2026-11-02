import math
import cv2
import numpy as np

def calculate_angle_3d(p1, p2, p3):
    """
    Calculates angle at joint p2 formed by vectors (p1 - p2) and (p3 - p2).
    Supports both 3D landmarks (x, y, z) and 2D fallback (x, y).
    Returns angle in degrees in range [0.0, 180.0].
    """
    z1 = getattr(p1, 'z', 0.0)
    z2 = getattr(p2, 'z', 0.0)
    z3 = getattr(p3, 'z', 0.0)

    v1 = (p1.x - p2.x, p1.y - p2.y, z1 - z2)
    v2 = (p3.x - p2.x, p3.y - p2.y, z3 - z2)

    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)

    if mag1 == 0 or mag2 == 0:
        return 180.0

    cos_angle = dot / (mag1 * mag2)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))

# Temporal history buffer for flicker-free view detection
_view_history = []

def detect_hand_view(landmarks):
    """
    Detects whether the hand is in a Lateral (side profile) or Front (palmar/dorsal) orientation.
    Uses palm width ratio with temporal smoothing to eliminate single-frame flickering.
    """
    global _view_history
    if not landmarks or len(landmarks) < 21:
        return "UNKNOWN"
        
    p0 = landmarks[0]   # Wrist
    p5 = landmarks[5]   # Index MCP
    p9 = landmarks[9]   # Middle MCP
    p17 = landmarks[17] # Pinky MCP

    # Palm width: horizontal spread of knuckles
    palm_width = abs(p5.x - p17.x)
    # Palm height: wrist to middle finger knuckle
    palm_height = math.sqrt((p9.x - p0.x)**2 + (p9.y - p0.y)**2)
    
    if palm_height == 0:
        return "FRONT"
    
    ratio = palm_width / palm_height
    raw_view = "LATERAL" if ratio < 0.28 else "FRONT"
    
    _view_history.append(raw_view)
    if len(_view_history) > 7:
        _view_history.pop(0)
        
    lateral_count = _view_history.count("LATERAL")
    return "LATERAL" if lateral_count >= 4 else "FRONT"

def get_hand_joint_angles(landmarks):
    """
    Calculates Range of Motion (ROM) angles for all 5 fingers, separating
    MCP, PIP, and DIP joints individually.
    
    Landmark Indices:
      Thumb: CMC (1), MCP (2), IP (3), Tip (4)
      Index: MCP (5), PIP (6), DIP (7), Tip (8)
      Middle: MCP (9), PIP (10), DIP (11), Tip (12)
      Ring: MCP (13), PIP (14), DIP (15), Tip (16)
      Pinky: MCP (17), PIP (18), DIP (19), Tip (20)
    """
    if not landmarks or len(landmarks) < 21:
        return {}

    # Separate MCP, PIP, DIP for each finger
    index_mcp = calculate_angle_3d(landmarks[0], landmarks[5], landmarks[6])
    index_pip = calculate_angle_3d(landmarks[5], landmarks[6], landmarks[7])
    index_dip = calculate_angle_3d(landmarks[6], landmarks[7], landmarks[8])

    middle_mcp = calculate_angle_3d(landmarks[0], landmarks[9], landmarks[10])
    middle_pip = calculate_angle_3d(landmarks[9], landmarks[10], landmarks[11])
    middle_dip = calculate_angle_3d(landmarks[10], landmarks[11], landmarks[12])

    ring_mcp = calculate_angle_3d(landmarks[0], landmarks[13], landmarks[14])
    ring_pip = calculate_angle_3d(landmarks[13], landmarks[14], landmarks[15])
    ring_dip = calculate_angle_3d(landmarks[14], landmarks[15], landmarks[16])

    pinky_mcp = calculate_angle_3d(landmarks[0], landmarks[17], landmarks[18])
    pinky_pip = calculate_angle_3d(landmarks[17], landmarks[18], landmarks[19])
    pinky_dip = calculate_angle_3d(landmarks[18], landmarks[19], landmarks[20])

    thumb_mcp = calculate_angle_3d(landmarks[1], landmarks[2], landmarks[3])
    thumb_ip = calculate_angle_3d(landmarks[2], landmarks[3], landmarks[4])

    return {
        # Overall finger angle (PIP) for backward compatibility
        "Thumb": thumb_ip,
        "Index": index_pip,
        "Middle": middle_pip,
        "Ring": ring_pip,
        "Pinky": pinky_pip,

        # Detailed individual joint breakdown
        "Thumb_MCP": thumb_mcp,
        "Thumb_IP": thumb_ip,

        "Index_MCP": index_mcp,
        "Index_PIP": index_pip,
        "Index_DIP": index_dip,

        "Middle_MCP": middle_mcp,
        "Middle_PIP": middle_pip,
        "Middle_DIP": middle_dip,

        "Ring_MCP": ring_mcp,
        "Ring_PIP": ring_pip,
        "Ring_DIP": ring_dip,

        "Pinky_MCP": pinky_mcp,
        "Pinky_PIP": pinky_pip,
        "Pinky_DIP": pinky_dip,

        "View": detect_hand_view(landmarks)
    }

def get_angle_color(angle):
    """
    Returns BGR color based on extension / flexion degree.
    >= 150 deg: Green (Full Extension / Straight)
    110 - 150 deg: Gold/Yellow (Partial Flexion)
    < 110 deg: Deep Orange/Cyan (High Flexion / Bent)
    """
    if angle >= 150:
        return (0, 255, 0)      # Green
    elif angle >= 110:
        return (0, 215, 255)    # Gold/Yellow
    else:
        return (0, 140, 255)    # Orange

def draw_goniometer_arc(frame, p_prev, p_joint, p_next, col, radius=20):
    """
    Draws a visual angle arc (goniometer arc) around the joint showing the angular opening.
    """
    v1 = (p_prev[0] - p_joint[0], p_prev[1] - p_joint[1])
    v2 = (p_next[0] - p_joint[0], p_next[1] - p_joint[1])
    
    ang1 = math.degrees(math.atan2(v1[1], v1[0])) % 360
    ang2 = math.degrees(math.atan2(v2[1], v2[0])) % 360
    
    start_ang = min(ang1, ang2)
    end_ang = max(ang1, ang2)
    if end_ang - start_ang > 180:
        start_ang, end_ang = end_ang, start_ang + 360
        
    cv2.ellipse(frame, p_joint, (radius, radius), 0, start_ang, end_ang, col, 2, cv2.LINE_AA)

def draw_biomechanics_overlay(frame, landmarks, angles):
    """
    Renders clean, non-cluttering visual indicators directly on the camera frame:
    - In LATERAL view: Goniometer arcs at Index MCP, PIP, DIP.
    - In FRONT view: Small colored dots on PIP joints.
    NO text or telemetry is drawn on the camera frame itself to prevent any overlap.
    """
    if not landmarks or not angles:
        return

    h, w, _ = frame.shape
    view_type = angles.get("View", "FRONT")

    if view_type == "LATERAL":
        pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in range(21)]
        # Goniometer arcs at Index MCP (5), PIP (6), DIP (7)
        draw_goniometer_arc(frame, pts[0], pts[5], pts[6], get_angle_color(angles.get("Index_MCP", 180)))
        draw_goniometer_arc(frame, pts[5], pts[6], pts[7], get_angle_color(angles.get("Index_PIP", 180)))
        draw_goniometer_arc(frame, pts[6], pts[7], pts[8], get_angle_color(angles.get("Index_DIP", 180)))

        # Clean dot markers at Index finger joints
        for idx in [5, 6, 7]:
            cv2.circle(frame, pts[idx], 5, (0, 255, 120), -1)
            cv2.circle(frame, pts[idx], 5, (255, 255, 255), 1)
    else:
        # Small colored dots on 5 finger PIP joints (minimalist)
        pip_joints = [
            ("Thumb_IP", 3),
            ("Index_PIP", 6),
            ("Middle_PIP", 10),
            ("Ring_PIP", 14),
            ("Pinky_PIP", 18)
        ]
        for key, lm_idx in pip_joints:
            if key in angles and lm_idx < len(landmarks):
                pt = (int(landmarks[lm_idx].x * w), int(landmarks[lm_idx].y * h))
                col = get_angle_color(angles[key])
                cv2.circle(frame, pt, 5, col, -1)
                cv2.circle(frame, pt, 5, (255, 255, 255), 1)

def create_clinical_dashboard(h, angles, view_type="FRONT", state_active=True, gesture="NONE", pinch_ratio=1.0):
    """
    Creates a dedicated, high-contrast dark clinical telemetry dashboard panel (320px width)
    to display alongside the camera view. Zero clutter on video!
    """
    panel_w = 330
    panel = np.zeros((h, panel_w, 3), dtype=np.uint8)
    panel[:] = (18, 18, 22)  # Sleek dark matte background

    # Top border / separator line
    cv2.line(panel, (0, 0), (0, h), (45, 45, 55), 2)

    # 1. Header
    cv2.putText(panel, "CLINICAL TELEMETRY", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Mode Badge
    view_col = (0, 255, 120) if view_type == "LATERAL" else (0, 215, 255)
    cv2.rectangle(panel, (15, 42), (panel_w - 15, 72), (28, 28, 36), -1)
    cv2.rectangle(panel, (15, 42), (panel_w - 15, 72), view_col, 1)
    cv2.putText(panel, f"VIEW: {view_type}", (25, 63), cv2.FONT_HERSHEY_SIMPLEX, 0.46, view_col, 1, cv2.LINE_AA)

    # 2. System Status Summary
    stat_col = (0, 255, 0) if state_active else (80, 80, 220)
    cv2.putText(panel, f"Status: {'TRACKING ACTIVE' if state_active else 'STANDBY'}", (15, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.38, stat_col, 1, cv2.LINE_AA)
    cv2.putText(panel, f"Gesture: {gesture}", (15, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(panel, f"Pinch Ratio: {pinch_ratio:.2f}", (15, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)

    # Divider
    cv2.line(panel, (15, 150), (panel_w - 15, 150), (45, 45, 55), 1)

    if view_type == "LATERAL":
        # 3. LATERAL VIEW: Detailed Goniometer breakdown with visual progress bars
        cv2.putText(panel, "INDEX PROFILE (GONIOMETER)", (15, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 120), 1, cv2.LINE_AA)
        
        idx_mcp = angles.get("Index_MCP", 180)
        idx_pip = angles.get("Index_PIP", 180)
        idx_dip = angles.get("Index_DIP", 180)

        def get_stat(deg):
            if deg >= 150: return "Extended"
            if deg >= 110: return "Partial Flex"
            return "Full Flex"

        joints = [
            ("MCP Joint", idx_mcp),
            ("PIP Joint", idx_pip),
            ("DIP Joint", idx_dip)
        ]

        cur_y = 205
        for name, deg in joints:
            col = get_angle_color(deg)
            cv2.putText(panel, f"{name}:", (15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1, cv2.LINE_AA)
            cv2.putText(panel, f"{int(round(deg))}°", (130, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.46, col, 1, cv2.LINE_AA)
            cv2.putText(panel, get_stat(deg), (195, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.36, col, 1, cv2.LINE_AA)

            # Degree Progress Bar (0 to 180 deg)
            bar_x = 15
            bar_w = panel_w - 30
            bar_h = 6
            cv2.rectangle(panel, (bar_x, cur_y + 6), (bar_x + bar_w, cur_y + 6 + bar_h), (40, 40, 50), -1)
            fill_w = int(bar_w * (max(0, min(180, deg)) / 180.0))
            cv2.rectangle(panel, (bar_x, cur_y + 6), (bar_x + fill_w, cur_y + 6 + bar_h), col, -1)

            cur_y += 38

        # Thumb
        t_ip = angles.get("Thumb_IP", 180)
        cv2.putText(panel, f"Thumb IP Joint: {int(round(t_ip))}°", (15, cur_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, get_angle_color(t_ip), 1, cv2.LINE_AA)

    else:
        # 3. FRONT VIEW: Complete Joint Matrix Table
        cv2.putText(panel, "RANGE OF MOTION (ROM)", (15, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 215, 255), 1, cv2.LINE_AA)
        
        # Table Header
        cv2.putText(panel, "Finger", (15, 202), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 140, 150), 1, cv2.LINE_AA)
        cv2.putText(panel, "MCP", (90, 202), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 140, 150), 1, cv2.LINE_AA)
        cv2.putText(panel, "PIP", (165, 202), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 140, 150), 1, cv2.LINE_AA)
        cv2.putText(panel, "DIP", (240, 202), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 140, 150), 1, cv2.LINE_AA)
        cv2.line(panel, (15, 210), (panel_w - 15, 210), (45, 45, 55), 1)

        fingers = [
            ("Index", "Index_MCP", "Index_PIP", "Index_DIP"),
            ("Middle", "Middle_MCP", "Middle_PIP", "Middle_DIP"),
            ("Ring", "Ring_MCP", "Ring_PIP", "Ring_DIP"),
            ("Pinky", "Pinky_MCP", "Pinky_PIP", "Pinky_DIP"),
        ]

        row_y = 232
        for name, mcp_k, pip_k, dip_k in fingers:
            mcp = angles.get(mcp_k, 180)
            pip = angles.get(pip_k, 180)
            dip = angles.get(dip_k, 180)

            cv2.putText(panel, name, (15, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1, cv2.LINE_AA)
            cv2.putText(panel, f"{int(round(mcp))}°", (90, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, get_angle_color(mcp), 1, cv2.LINE_AA)
            cv2.putText(panel, f"{int(round(pip))}°", (165, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, get_angle_color(pip), 1, cv2.LINE_AA)
            cv2.putText(panel, f"{int(round(dip))}°", (240, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, get_angle_color(dip), 1, cv2.LINE_AA)
            row_y += 24

        t_ip = angles.get("Thumb_IP", 180)
        cv2.putText(panel, f"Thumb IP: {int(round(t_ip))}°", (15, row_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, get_angle_color(t_ip), 1, cv2.LINE_AA)

    # Footer note
    cv2.line(panel, (15, h - 35), (panel_w - 15, h - 35), (45, 45, 55), 1)
    cv2.putText(panel, "Press 'r' to toggle Dashboard", (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (120, 120, 130), 1, cv2.LINE_AA)

    return panel
