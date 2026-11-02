import os
import platform

try:
    from pynput.keyboard import Controller, Key
    KEYBOARD_SUPPORTED = True
except ImportError:
    KEYBOARD_SUPPORTED = False

try:
    if platform.system() == "Windows":
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        WINDOWS_AUDIO_SUPPORTED = True
    else:
        WINDOWS_AUDIO_SUPPORTED = False
except ImportError:
    WINDOWS_AUDIO_SUPPORTED = False
    print("Warning: pycaw or comtypes not available. Volume control disabled.")

class SystemController:
    def __init__(self):
        self.keyboard = Controller() if KEYBOARD_SUPPORTED else None
        self.volume = None
        
        if WINDOWS_AUDIO_SUPPORTED:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = interface.QueryInterface(IAudioEndpointVolume)
            except Exception as e:
                print(f"Failed to initialize audio: {e}")
                self.volume = None

    def alt_tab(self):
        if not self.keyboard:
            print("Keyboard control not supported.")
            return
        
        self.keyboard.press(Key.alt)
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        self.keyboard.release(Key.alt)

    def set_volume(self, normalized_y):
        """Map normalized_y (0.0 to 1.0) to volume."""
        if not self.volume:
            return
            
        vol_range = self.volume.GetVolumeRange()
        min_vol = vol_range[0]
        max_vol = vol_range[1]
        
        # Clamp y between 0.2 (top) and 0.8 (bottom)
        y = max(0.2, min(normalized_y, 0.8))
        vol_perc = 1.0 - ((y - 0.2) / 0.6)
        
        target_vol = min_vol + (max_vol - min_vol) * vol_perc
        self.volume.SetMasterVolumeLevel(target_vol, None)
