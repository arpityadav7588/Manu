"""
modules/security/auth.py
Bridge for SecurityManager to match AuthManager interface.
"""
import logging
import sys
import config
from modules.security_manager import SecurityManager

log = logging.getLogger("Manu.Auth")


class AuthManager(SecurityManager):
    """
    Extends SecurityManager (no-arg __init__) with:
      - authenticate() → interactive console auth flow
      - verify_password() → delegates to SecurityManager
    main.py instantiates as: AuthManager(tts, memory)
    """

    def __init__(self, tts=None, memory=None):
        super().__init__()          # SecurityManager takes no args
        self.tts    = tts
        self.memory = memory

        # Load password hash from config if the base class has empty hash
        if not self.get_stored_hash() and hasattr(config, "PASSWORD_HASH"):
            stored = getattr(config, "PASSWORD_HASH", "")
            if stored:
                self._stored_hash = stored

        log.info("AuthManager (Bridge) initialized.")

    def authenticate(self) -> bool:
        """Interactive console authentication. Returns True on success."""
        if not self._stored_hash:
            log.info("No password set — running in open mode.")
            return True

        max_attempts = getattr(config, "MAX_AUTH_ATTEMPTS", 3)

        if self.tts:
            self.tts.speak("Security check. Please enter your password.")

        for attempt in range(1, max_attempts + 1):
            print(f"\n[SECURITY] Manu is locked. Attempt {attempt}/{max_attempts}")
            try:
                password = input("Enter Password: ")
            except (EOFError, KeyboardInterrupt):
                return False

            if self.verify_password(password):
                log.info("Authentication successful.")
                if self.memory:
                    try:
                        self.memory.log_security_event("auth_success")
                    except Exception:
                        pass
                return True
            else:
                log.warning(f"Authentication failed (attempt {attempt}).")
                remaining = max_attempts - attempt
                if remaining > 0:
                    print(f"  Incorrect. {remaining} attempt(s) remaining.")
                if self.memory:
                    try:
                        self.memory.log_security_event(f"auth_failed_attempt_{attempt}")
                    except Exception:
                        pass

        log.warning("All authentication attempts exhausted.")
        self.capture_webcam("auth_exhausted")
        return False
