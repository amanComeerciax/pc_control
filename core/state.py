class StateManager:
    def __init__(self, config):
        self.config = config
        self.is_active = False
        self.current_gesture = None
        self.gesture_frames = 0
        self.cooldowns = {}
        
        self.pinch_active = False
        self.last_open_time = 0
        
    def update_gesture(self, gesture, timestamp):
        """Returns (triggered, toggled)."""
        # OPEN hold toggle logic
        if gesture == "OPEN":
            if self.current_gesture == "OPEN":
                if timestamp - self.last_open_time > self.config["gestures"]["toggle_hold_seconds"]:
                    self.is_active = not self.is_active
                    self.last_open_time = timestamp + 2.0 # Cooldown for toggle
                    return False, True
            else:
                self.last_open_time = timestamp
        
        if gesture == self.current_gesture:
            self.gesture_frames += 1
        else:
            self.current_gesture = gesture
            self.gesture_frames = 1
            
        is_stable = self.gesture_frames >= self.config["gestures"]["hold_frames"]
        
        if not is_stable:
            return False, False
            
        if gesture in self.cooldowns:
            if self.gesture_frames - self.cooldowns[gesture] < self.config["gestures"]["cooldown_frames"]:
                return False, False
                
        return True, False
        
    def set_cooldown(self, gesture):
        self.cooldowns[gesture] = self.gesture_frames
        
    def update_pinch(self, pinch_ratio):
        """Hysteresis for pinch state (drag/drop)."""
        if not self.pinch_active and pinch_ratio < self.config["gestures"]["pinch_threshold_press"]:
            self.pinch_active = True
            return "PRESS"
        elif self.pinch_active and pinch_ratio > self.config["gestures"]["pinch_threshold_release"]:
            self.pinch_active = False
            return "RELEASE"
        return "HOLD" if self.pinch_active else "NONE"
