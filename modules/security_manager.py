import hashlib
import time
import getpass
import os
import datetime
from pathlib import Path
import socket
import re
import config

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

class SecurityManager:
    def __init__(self, speech, memory):
        self.speech = speech
        self.memory = memory
        self.is_locked = True
        self.auth_attempts = 0
        self.password_hash = config.PASSWORD_HASH
        
        if not self.password_hash:
            # First run setup
            self.setup_wizard()

    def verify_password(self, entered_text):
        """Hash entered_text with SHA-256. Compare to config.PASSWORD_HASH."""
        if not self.password_hash: return False
        
        entered_hash = self.hash_password(entered_text)
        if entered_hash == self.password_hash:
            self.auth_attempts = 0
            self.is_locked = False
            self.memory.log_security_event("AUTH_SUCCESS", "User authenticated successfully.")
            return True
        else:
            self.auth_attempts += 1
            self.memory.log_security_event("AUTH_FAIL", f"Attempt {self.auth_attempts} failed.")
            if self.auth_attempts >= config.MAX_AUTH_ATTEMPTS:
                self.lockout()
            return False

    def setup_wizard(self):
        """First-time setup for user name and password."""
        print("\n" + "="*40)
        print("🛡️  MANU ASSISTANT SETUP WIZARD  🛡️")
        print("="*40 + "\n")
        
        self.speech.speak("Welcome! Let's set up your secure profile.")
        
        name = input("Hi! I'm Manu. What should I call you? [Friend]: ").strip() or "Friend"
        self.memory.set_setting("user_name", name)
        
        while True:
            pwd = getpass.getpass("Set your Manu password: ")
            pwd_confirm = getpass.getpass("Confirm password: ")
            
            if pwd == pwd_confirm and len(pwd) >= 1:
                hashed = self.hash_password(pwd)
                self._write_to_config("PASSWORD_HASH", hashed)
                self._write_to_config("USER_NAME", name)
                config.PASSWORD_HASH = hashed
                config.USER_NAME = name
                self.password_hash = hashed
                break
            else:
                print("Passwords didn't match or were empty. Try again.")

        self.speech.speak(f"Setup complete! It's an honor to meet you, {name}.")
        print("\n🔒 Setup finished. Please restart Manu to apply all changes.")

    def lock_session(self):
        self.memory.log_security_event("SLEEP_MODE", "Session locked by command.")
        self.is_locked = True

    def lockout(self):
        msg = f"Critical alert! Maximum authentication attempts ({config.MAX_AUTH_ATTEMPTS}) reached."
        self.speech.speak(msg)
        if config.WEBCAM_ON_FAIL:
            self.capture_webcam("LOCKOUT")
        self.memory.log_security_event("LOCKOUT", "Maximum login attempts exceeded.")

    def capture_webcam(self, reason="security"):
        """Use OpenCV to capture a frame from the webcam."""
        if not HAS_CV2:
            print("Webcam capture failed: OpenCV (cv2) not installed.")
            return

        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return
            
            time.sleep(1.0) # Wait for camera to warm up
            ret, frame = cap.read()
            if ret:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{reason}_{timestamp}.jpg"
                save_path = config.CAPTURES_DIR / filename
                cv2.imwrite(str(save_path), frame)
                self.memory.log_security_event("WEBCAM_CAPTURE", f"Saved to {filename}")
            cap.release()
        except Exception as e:
            print(f"Error capturing webcam: {e}")

    def check_internet(self):
        """Check for internet connectivity."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    @staticmethod
    def hash_password(pwd):
        return hashlib.sha256(pwd.encode()).hexdigest()

    def _write_to_config(self, key, value):
        """Update config.py file with new values."""
        config_path = config.BASE_DIR / "config.py"
        content = config_path.read_text(encoding="utf-8")
        
        # Replace PASSWORD_HASH = "" or existing hash
        if key == "PASSWORD_HASH":
            content = re.sub(r'PASSWORD_HASH\s+=\s+".*?"', f'PASSWORD_HASH = "{value}"', content)
        elif key == "USER_NAME":
            content = re.sub(r'USER_NAME\s+=\s+".*?"', f'USER_NAME = "{value}"', content)
            
        config_path.write_text(content, encoding="utf-8")
