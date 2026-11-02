import pytest
from core.smoothing import OneEuroFilter
from core.state import StateManager

def test_one_euro_filter():
    f = OneEuroFilter(t0=1.0, x0=0.0)
    res = f(1.1, 0.1)
    assert res > 0.0 and res < 0.1
    res = f(1.2, 10.0)
    assert res > 1.0

def test_state_manager():
    config = {
        "gestures": {
            "hold_frames": 3,
            "cooldown_frames": 5,
            "toggle_hold_seconds": 0.5,
            "pinch_threshold_press": 0.05,
            "pinch_threshold_release": 0.08
        }
    }
    sm = StateManager(config)
    
    assert sm.is_active is False
    sm.update_gesture("OPEN", 1.0)
    triggered, toggled = sm.update_gesture("OPEN", 1.6)
    assert toggled is True
    assert sm.is_active is True
    
    sm.update_gesture("FIST", 2.0)
    triggered, _ = sm.update_gesture("FIST", 2.1)
    assert triggered is False
    triggered, _ = sm.update_gesture("FIST", 2.2)
    assert triggered is True
    
    sm.set_cooldown("FIST")
    triggered, _ = sm.update_gesture("FIST", 2.3)
    assert triggered is False
