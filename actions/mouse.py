import pyautogui
import pynput

import time

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

class MouseController:
    def __init__(self, config):
        self.config = config
        self.screen_w, self.screen_h = pyautogui.size()
        
        margin_x = config["tracking"]["active_zone_margin_x"]
        margin_y = config["tracking"]["active_zone_margin_y"]
        
        self.min_x = margin_x
        self.max_x = 1.0 - margin_x
        self.min_y = margin_y
        self.max_y = 1.0 - margin_y
        
        self.mouse = pynput.mouse.Controller()
        
    def map_to_screen(self, x, y):
        x = max(self.min_x, min(x, self.max_x))
        y = max(self.min_y, min(y, self.max_y))
        
        norm_x = (x - self.min_x) / (self.max_x - self.min_x)
        norm_y = (y - self.min_y) / (self.max_y - self.min_y)
        
        return int(norm_x * self.screen_w), int(norm_y * self.screen_h)
        
    def move(self, x, y):
        screen_x, screen_y = self.map_to_screen(x, y)
        self.mouse.position = (screen_x, screen_y)
        
    def click(self, button='left'):
        btn = pynput.mouse.Button.left if button == 'left' else pynput.mouse.Button.right
        self.mouse.press(btn)
        time.sleep(0.03)  # 30ms tap duration ensures macOS registers click
        self.mouse.release(btn)
            
    def press(self):
        self.mouse.press(pynput.mouse.Button.left)
        
    def release(self):
        self.mouse.release(pynput.mouse.Button.left)
        
    def scroll(self, amount):
        self.mouse.scroll(0, amount)
