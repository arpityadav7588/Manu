import hashlib
import time
import getpass
import os
import datetime
import json
import pickle
from pathlib import Path
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
        self.face_encoding_path = config.DATA_DIR / "security" / "face_encoding.pkl"

    @property
    def is_locked(self):
        return self._is_locked

    def verify_password(self, password):
        """Hash input and compare to stored hash; also check 4-digit PIN."""
        stored_hash = self.memory.get_setting("password_hash")
        stored_pin = self.memory.get_setting("quick_pin")
        
        if not stored_hash:
            return False

        input_hash = self.hash_password(password)
        if input_hash == stored_hash or (stored_pin and password == stored_pin):
            self.auth_attempts = 0
            self._is_locked = False
            return True
        else:
            self.auth_attempts += 1
            if self.auth_attempts >= 2:
                # Capture intruder after 2 fails
                self.log_intrusion(f"Failed Auth (Attempt {self.auth_attempts})")
                
                # Optional: Try face verification as a last resort
                if self.verify_face():
                    self.auth_attempts = 0
                    self._is_locked = False
                    return True
            return False

    def verify_face(self) -> bool:
        """Capture a frame and compare to enrolled face encodings from pickle."""
        if not HAS_FACE or not HAS_CV2: return False
        
        if not self.face_encoding_path.exists(): return False
        
        try:
            with open(self.face_encoding_path, "rb") as f:
                enrolled_encodings = pickle.load(f)
        except: return False
        
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return False
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(enrolled_encodings, face_encoding, tolerance=0.6)
            if True in matches:
                return True
        
        return False

    def enroll_face(self, callback=None):
        """Capture 5 webcam frames and save face encodings to pkl."""
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
                encodings.append(face_encodings[0])
                count += 1
                if callback: callback(count)
                print(f"[*] Enrolled face frame {count}/5")
                time.sleep(0.5)
        
        cap.release()
        if encodings:
            with open(self.face_encoding_path, "wb") as f:
                pickle.dump(encodings, f)
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
            self.memory.set_setting("password_hash", self.hash_password(pwd))
            break
            
        while True:
            pin = input("Set a 4-digit quick PIN (optional, Enter to skip): ").strip()
            if not pin: break
            if len(pin) == 4 and pin.isdigit():
                self.memory.set_setting("quick_pin", pin)
                break
            print("PIN must be exactly 4 digits.")
            
        print("\n[*] Optional: Enroll face for bio-verification?")
        if input("Enroll now? (y/n): ").lower() == 'y':
            self.enroll_face()

        print(f"Welcome, {name}! Security initialized.")
        self.tts.speak(f"Welcome! Security set. I'm ready, {name}!")

    def log_intrusion(self, reason):
        """Capture frame and log intrusion detail to data/captures/intruder_*.jpg."""
        if not HAS_CV2: return
        
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = config.DATA_DIR / "captures" / f"intruder_{ts}.jpg"
                cv2.imwrite(str(filename), frame)
                
                log_detail = f"[{datetime.datetime.now()}] FAILED_AUTH | {reason} | Photo: {filename.name}"
                
                # Database log
                self.memory.log_security_event("INTRUSION", log_detail)
                
                # File log (Task 5c)
                log_path = config.DATA_DIR / "security" / "log.txt"
                with open(log_path, "a") as f:
                    f.write(f"{log_detail}\n")
                    
                print(f"⚠️ Security: Intrusion captured: {filename.name}")
        except Exception as e:
            print(f"Intrusion capture error: {e}")

    def lock_session(self):
        self._is_locked = True

    @staticmethod
    def hash_password(pwd):
        return hashlib.sha256(pwd.encode()).hexdigest()
