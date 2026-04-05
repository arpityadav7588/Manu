import hashlib
import cv2
import os
import datetime

class SecurityManager:
    def __init__(self, password="manu"):
        self.password_hash = self._hash_password(password)
        self.locked = True
        
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password):
        if self._hash_password(password) == self.password_hash:
            self.locked = False
            return True
        else:
            self.capture_intruder()
            return False

    def lock_session(self):
        self.locked = True
        return "Session locked. I'll keep your data safe while I rest."

    def capture_intruder(self):
        """
        Captures a photo using the default webcam and saves it to security logs.
        """
        try:
            if not os.path.exists("data/security_logs"):
                os.makedirs("data/security_logs")
                
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"data/security_logs/intruder_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Intruder captured: {filename}")
            cap.release()
        except Exception as e:
            print(f"Webcam capture failed: {e}")

if __name__ == "__main__":
    security = SecurityManager()
    if security.verify_password("wrong_pass"):
        print("Unlocked!")
    else:
        print("Access denied.")
