import pytest
from core.gestures import detect_gesture, get_fingers_up, get_pinch_ratio

class DummyLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def create_hand(finger_states, is_pinch=False):
    lm = [DummyLandmark(0.5, 0.9)] * 21
    
    lm[0] = DummyLandmark(0.5, 0.9)
    lm[17] = DummyLandmark(0.7, 0.7)
    lm[9] = DummyLandmark(0.5, 0.6)
    
    if finger_states[0]:
        lm[4] = DummyLandmark(0.2, 0.5)
        lm[3] = DummyLandmark(0.3, 0.6)
    else:
        lm[4] = DummyLandmark(0.6, 0.7)
        lm[3] = DummyLandmark(0.6, 0.7)
        
    lm[6] = DummyLandmark(0.4, 0.6)
    lm[8] = DummyLandmark(0.4, 0.3) if finger_states[1] else DummyLandmark(0.4, 0.8)
    
    lm[10] = DummyLandmark(0.5, 0.6)
    lm[12] = DummyLandmark(0.5, 0.3) if finger_states[2] else DummyLandmark(0.5, 0.8)
    
    lm[14] = DummyLandmark(0.6, 0.6)
    lm[16] = DummyLandmark(0.6, 0.3) if finger_states[3] else DummyLandmark(0.6, 0.8)
    
    lm[18] = DummyLandmark(0.7, 0.6)
    lm[20] = DummyLandmark(0.7, 0.3) if finger_states[4] else DummyLandmark(0.7, 0.8)
    
    if is_pinch:
        lm[4] = DummyLandmark(0.4, 0.3)
        lm[8] = DummyLandmark(0.41, 0.31)
        
    return lm

def test_fingers_up():
    lm = create_hand([True, True, True, True, True])
    assert get_fingers_up(lm) == [True, True, True, True, True]
    
    lm = create_hand([False, False, False, False, False])
    assert get_fingers_up(lm) == [False, False, False, False, False]
    
def test_detect_gesture():
    lm = create_hand([True, True, True, True, True])
    assert detect_gesture(lm) == "OPEN"
    
    lm = create_hand([False, False, False, False, False])
    assert detect_gesture(lm) == "FIST"
    
    lm = create_hand([False, True, False, False, False])
    assert detect_gesture(lm) == "POINT"
    
    lm = create_hand([True, True, False, False, False])
    assert detect_gesture(lm) == "POINT"
    
    lm = create_hand([False, True, True, False, False])
    assert detect_gesture(lm) == "TWO_FINGERS"
    
    lm = create_hand([False, True, True, True, False])
    assert detect_gesture(lm) == "THREE_FINGERS"
    
    lm = create_hand([False, True, False, False, False], is_pinch=True)
    assert detect_gesture(lm) == "PINCH"
