import hashlib
from pathlib import Path
import time

class SecurityManager:
    def __init__(self):
        try:
            Path("./data").mkdir(parents=True, exist_ok=True)
            self._hash_file = Path("./data/.manu_auth")
            self._stored_hash = self._load_hash()
            self._attempts = 0
            self.max_attempts = 3
        except Exception as e:
            pass

    def _load_hash(self) -> str | None:
        try:
            if self._hash_file.exists():
                return self._hash_file.read_text().strip()
            return None
        except Exception as e:
            return None

    def has_password(self) -> bool:
        try:
            return self._stored_hash is not None
        except Exception as e:
            return False

    def set_password(self, password: str):
        try:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            self._hash_file.write_text(hashed)
            self._stored_hash = hashed
        except Exception as e:
            pass

    def verify_password(self, password: str) -> bool:
        try:
            entered = hashlib.sha256(password.encode()).hexdigest()
            if entered == self._stored_hash:
                self._attempts = 0
                return True
            else:
                self._attempts += 1
                if self._attempts >= self.max_attempts:
                    self.capture_intruder()
                return False
        except Exception as e:
            return False

    def capture_intruder(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            time.sleep(0.5)
            ret, frame = cap.read()
            if ret:
                Path("./data/captures").mkdir(parents=True, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"./data/captures/{timestamp}.jpg", frame)
            cap.release()
        except ImportError:
            print("OpenCV not installed, skipping webcam capture")
        except Exception as e:
            print(f"Capture error: {e}")

    def lock_session(self):
        try:
            self._attempts = 0
            print("🔒 Session locked.")
        except Exception as e:
            pass
