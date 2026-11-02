import os
import subprocess
import platform

class AppLauncher:
    def __init__(self, config):
        self.config = config
        
    def launch(self, gesture):
        if gesture in self.config["apps"]:
            app_path = self.config["apps"][gesture]
            try:
                if platform.system() == "Windows":
                    os.startfile(app_path)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", app_path])
                else:
                    subprocess.Popen([app_path])
                print(f"Launched {app_path}")
            except Exception as e:
                print(f"Failed to launch {app_path}: {e}")
