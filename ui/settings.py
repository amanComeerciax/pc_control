import tkinter as tk
from threading import Thread
import platform

class SettingsUI:
    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.root = None
        self.is_mac = platform.system() == "Darwin"
        
    def _run(self):
        self.root = tk.Tk()
        self.root.title("Gesture PC Control")
        self.root.geometry("300x200")
        self.root.attributes("-topmost", True)
        
        self.status_var = tk.StringVar(value="Status: OFF")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, font=("Helvetica", 16, "bold"))
        self.status_label.pack(pady=20)
        
        self.gesture_var = tk.StringVar(value="Gesture: NONE")
        tk.Label(self.root, textvariable=self.gesture_var, font=("Helvetica", 12)).pack(pady=10)
        
        tk.Label(self.root, text="Hold OPEN hand for 2s to toggle ON/OFF", font=("Helvetica", 9), fg="gray").pack(side="bottom", pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_ui()
        self.root.mainloop()
        
    def start(self):
        if self.is_mac:
            print("Tkinter UI disabled on macOS (GUI thread restriction). All status updates will be shown directly in the camera preview window!")
            return
        self.thread = Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        
    def update_ui(self):
        if not self.root:
            return
            
        status = "ON" if self.state_manager.is_active else "OFF"
        self.status_var.set(f"Status: {status}")
        self.status_label.config(fg="green" if self.state_manager.is_active else "red")
        
        gesture = self.state_manager.current_gesture or "NONE"
        self.gesture_var.set(f"Gesture: {gesture}")
        
        # update every 100ms
        self.root.after(100, self.update_ui)
        
    def on_close(self):
        # We don't want the UI closing to kill the whole app unless intended,
        # but for simplicity we just hide it or destroy it.
        self.root.destroy()
