import hashlib
import time
import os
import datetime
from pathlib import Path
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
        self.max_attempts = 3
        self.auth_file = config.DATA_DIR / "auth.hash"

    @property
    def is_locked(self):
        return self._is_locked

    def first_run_if_needed(self):
        """Task 7: Setup if no password hash exists."""
        if not self.auth_file.exists():
            print("\n--- Manu First-Run Setup ---")
            pwd = input("Set your security password: ")
            if pwd:
                pwd_hash = self.hash_password(pwd)
                with open(self.auth_file, "w") as f:
                    f.write(pwd_hash)
                print("[*] Security: Password set. Encrypting brain...")
                self.tts.speak("Security set. I'm ready for duty.")

    def verify_password(self, password):
        """Task 7: Hash and compare; handle lockout."""
        if not self.auth_file.exists():
            return True # No password yet, bypass
            
        with open(self.auth_file, "r") as f:
            stored_hash = f.read().strip()
            
        if self.hash_password(password) == stored_hash:
            self._is_locked = False
            self.auth_attempts = 0
            self.unlock_session()
            return True
        else:
            self.auth_attempts += 1
            self.memory.log_security("FAILED_ATTEMPT", f"Attempt {self.auth_attempts}")
            
            if self.auth_attempts >= self.max_attempts:
                self.lock_session()
                self.capture_webcam("LOCKOUT")
                print(f"⚠️ Security: Max attempts reached. Lockout active.")
            
            return False

    def capture_webcam(self, reason="security"):
        """Task 7: Capture frames on failure."""
        if not HAS_CV2:
            print("[!] Security: OpenCV missing. Cannot capture intruder photo.")
            return

        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[!] Security: Could not access webcam.")
                return
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = config.DATA_DIR / "captures" / f"intruder_{ts}.jpg"
                filename.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(filename), frame)
                self.memory.log_security(reason, f"Photo saved to {filename.name}")
        except Exception as e:
            print(f"Security: Webcam capture error: {e}")

    def lock_session(self):
        """Task 7: State management."""
        self._is_locked = True
        self.memory.log_security("SESSION_LOCKED", "Manual or Lockout")

    def unlock_session(self):
        """Task 7: State management."""
        self._is_locked = False
        self.memory.log_security("SESSION_UNLOCKED", "Valid auth")

    @staticmethod
    def hash_password(pwd):
        return hashlib.sha256(pwd.encode()).hexdigest()
