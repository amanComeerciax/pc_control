import math

def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def get_hand_size(landmarks):
    """Calculate hand size as the distance from wrist (0) to middle MCP (9)."""
    return distance(landmarks[0], landmarks[9])

def get_pinch_ratio(landmarks):
    """Normalize pinch distance by hand size."""
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    dist = distance(thumb_tip, index_tip)
    hand_size = get_hand_size(landmarks)
    if hand_size == 0:
        return 1.0
    return dist / hand_size

def get_fingers_up(landmarks):
    """Returns a list of 5 booleans indicating if each finger is up."""
    fingers_up = []
    
    # Thumb: compare distance from tip (4) to pinky MCP (17) vs IP (3) to pinky MCP
    # This works relatively well regardless of hand orientation
    thumb_tip_dist = distance(landmarks[4], landmarks[17])
    thumb_ip_dist = distance(landmarks[3], landmarks[17])
    fingers_up.append(thumb_tip_dist > thumb_ip_dist)
    
    # Index, Middle, Ring, Pinky
    # Compare tip y to PIP y
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    
    for tip, pip in zip(tips, pips):
        # MediaPipe y goes from top (0) to bottom (1)
        # So smaller y means higher on the screen
        fingers_up.append(landmarks[tip].y < landmarks[pip].y)
        
    return fingers_up

def detect_gesture(landmarks, pinch_threshold=0.06):
    """
    Returns the string name of the detected gesture.
    Gestures: POINT, PINCH, TWO_FINGERS, THREE_FINGERS, FIST, OPEN, L_SHAPE, UNKNOWN
    """
    fingers_up = get_fingers_up(landmarks)
    thumb, index, middle, ring, pinky = fingers_up
    
    pinch_ratio = get_pinch_ratio(landmarks)
    is_pinch = pinch_ratio < pinch_threshold
    
    if is_pinch:
        return "PINCH"
        
    # Open: all fingers up
    if index and middle and ring and pinky:
        return "OPEN"
        
    # Fist: no fingers up (except maybe thumb depending on how it's tucked)
    if not index and not middle and not ring and not pinky:
        return "FIST"
        
    # Point: only index up (thumb might be up or down, don't care)
    if index and not middle and not ring and not pinky:
        return "POINT"
        
    # Two fingers: index and middle
    if index and middle and not ring and not pinky:
        return "TWO_FINGERS"
        
    # Three fingers: index, middle, ring
    if index and middle and ring and not pinky:
        return "THREE_FINGERS"
        
    return "UNKNOWN"
