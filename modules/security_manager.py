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

try:
    import face_recognition
    import numpy as np
    HAS_FACE = True
except ImportError:
    HAS_FACE = False

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
        stored_pin = self.memory.get_setting("quick_pin")
        
        if not stored_hash:
            return False

        input_hash = self.hash_password(password)
        if input_hash == stored_hash or password == stored_pin:
            self.auth_attempts = 0
            self._is_locked = False
            return True
        else:
            self.auth_attempts += 1
            if self.auth_attempts >= 2:
                self.log_intrusion("Failed Password/PIN")
            return False

    def verify_face(self) -> bool:
        """Capture a frame and compare to enrolled face encodings."""
        if not HAS_FACE or not HAS_CV2: return False
        
        enrolled_json = self.memory.get_setting("face_encodings")
        if not enrolled_json: return False
        
        enrolled_encodings = [np.array(e) for e in json.loads(enrolled_json)]
        
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return False
        
        # Resize for speed
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(enrolled_encodings, face_encoding, tolerance=0.6)
            if True in matches:
                self._is_locked = False
                return True
        
        return False

    def enroll_face(self, callback=None):
        """Webcam wizard to capture 5 frames of the user's face."""
        if not HAS_FACE or not HAS_CV2: return False
        
        cap = cv2.VideoCapture(0)
        encodings = []
        count = 0
        
        while count < 5:
            ret, frame = cap.read()
            if not ret: break
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            if face_encodings:
                encodings.append(face_encodings[0].tolist())
                count += 1
                if callback: callback(count)
                time.sleep(0.5)
        
        cap.release()
        if encodings:
            self.memory.set_setting("face_encodings", json.dumps(encodings))
            return True
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

    def log_intrusion(self, reason):
        """Capture frame and log intrusion detail to database and log.txt."""
        if not HAS_CV2: return
        
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = config.DATA_DIR / "captures" / f"intrusion_{ts}.jpg"
                cv2.imwrite(str(filename), frame)
                
                detail = f"Reason: {reason} | Image: {filename.name}"
                self.memory.log_security_event("INTRUSION", detail)
                
                # Append to log.txt for Task 5
                log_path = config.DATA_DIR / "security" / "log.txt"
                with open(log_path, "a") as f:
                    f.write(f"[{ts}] {detail}\n")
                    
                print(f"⚠️ Security: Intrusion logged at {ts}")
        except Exception as e:
            print(f"Intrusion capture error: {e}")

    def lock_session(self):
        self._is_locked = True

    @staticmethod
    def hash_password(pwd):
        return hashlib.sha256(pwd.encode()).hexdigest()
