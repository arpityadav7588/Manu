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
    def __init__(self, tts, memory):
        self.tts = tts
        self.memory = memory
        self._is_locked = True
        self.auth_attempts = 0

    @property
    def is_locked(self):
        return self._is_locked

    def verify_password(self, password):
        """Hash input and compare to stored hash from memory.get_setting('password_hash')."""
        stored_hash = self.memory.get_setting("password_hash")
        if not stored_hash:
            return False

        input_hash = self.hash_password(password)
        if input_hash == stored_hash:
            self.auth_attempts = 0
            self._is_locked = False
            return True
        else:
            self.auth_attempts += 1
            if self.auth_attempts >= 2:
                self.capture_intruder()
            return False

    def first_run_if_needed(self):
        """Check if password is set; if not, run wizard."""
        if not self.memory.get_setting("password_hash"):
            self.setup_wizard()

    def setup_wizard(self):
        print("\n--- Manu Setup Wizard ---")
        name = input("Enter your name: ").strip() or "User"
        self.memory.set_setting("user_name", name)
        
        while True:
            pwd = input("Set a security password: ")
            if len(pwd) < 1: continue
            
            pwd_hash = self.hash_password(pwd)
            self.memory.set_setting("password_hash", pwd_hash)
            break
            
        print(f"Welcome, {name}! Security initialized.")
        self.tts.speak(f"Welcome! Password set. I'm ready to serve you, {name}!")

    def capture_intruder(self):
        """Use OpenCV to grab a frame and save to data/captures/."""
        if not HAS_CV2: return
        
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = config.DATA_DIR / "captures" / f"intruder_{ts}.jpg"
                filename.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(filename), frame)
                print(f"📷 Intruder captured: {filename.name}")
            cap.release()
        except:
            pass

    def lock_session(self):
        self._is_locked = True

    @staticmethod
    def hash_password(pwd):
        return hashlib.sha256(pwd.encode()).hexdigest()
