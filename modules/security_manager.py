"""
modules/security_manager.py
Manu's authentication and session security.
SHA-256 password hashing. Webcam capture on failed auth.
"""

import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path

log = logging.getLogger("Manu.Security")

# If no password is configured, Manu runs in open mode (no-auth).
# To set a password: python -c "import hashlib; print(hashlib.sha256(b'yourpass').hexdigest())"
# Then paste the hash below or store it via MemoryManager settings.
STORED_HASH = ""   # Empty = no-auth mode


class SecurityManager:

    def __init__(self):
        self._stored_hash = STORED_HASH
        self._session_locked = False
        log.info(
            "SecurityManager ready. "
            f"Mode: {'password-protected' if self._stored_hash else 'open (no password set)'}"
        )

    def verify_password(self, entered: str) -> bool:
        """Verify entered password against stored SHA-256 hash."""
        if not self._stored_hash:
            # No password configured — always allow
            return True
        entered_hash = hashlib.sha256(entered.encode("utf-8")).hexdigest()
        match = entered_hash == self._stored_hash
        if not match:
            log.warning("Failed authentication attempt.")
            self.capture_webcam("failed_auth")
        return match

    def get_stored_hash(self) -> str:
        return self._stored_hash

    def set_password(self, new_password: str):
        """Hash and store a new password."""
        self._stored_hash = hashlib.sha256(
            new_password.encode("utf-8")
        ).hexdigest()
        log.info("Password updated.")

    def lock_session(self):
        """Mark session as locked."""
        self._session_locked = True
        log.info("Session locked.")

    def unlock_session(self):
        self._session_locked = False

    @property
    def is_locked(self) -> bool:
        return self._session_locked

    def capture_webcam(self, reason: str = "security"):
        """Capture webcam snapshot on suspicious event."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                log.warning("Webcam not accessible.")
                return

            import time
            time.sleep(0.4)   # Let camera warm up
            ret, frame = cap.read()
            cap.release()

            if ret:
                captures_dir = Path("data") / "captures"
                captures_dir.mkdir(parents=True, exist_ok=True)
                ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = captures_dir / f"{reason}_{ts}.jpg"
                cv2.imwrite(str(filename), frame)
                log.info(f"Security capture saved: {filename.name}")
        except ImportError:
            log.debug("opencv not installed — webcam capture skipped.")
        except Exception as e:
            log.error(f"Webcam capture failed: {e}")
