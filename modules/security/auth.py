"""
modules/security/auth.py
Bridge for SecurityManager to match AuthManager interface.
"""
import logging
import sys
from modules.security_manager import SecurityManager

log = logging.getLogger("Manu.Auth")

class AuthManager(SecurityManager):
    def __init__(self, tts=None, memory=None):
        super().__init__(speech=tts, memory=memory)
        log.info("AuthManager (Bridge) initialized.")

    def authenticate(self) -> bool:
        """New method expected by main.py."""
        if not self.has_password():
            log.info("No password set. This might be first run.")
            return True # Allow for now, or handle setup
        
        # If running in console mode or background, we might need a way to authenticate.
        # For now, if we are in Siri-mode, we'll assume the user will use --gui once to setup/login
        # or we'll print a message to console.
        
        print("\n[SECURITY] Manu is locked.")
        password = input("Enter Password to unlock Manu: ")
        if self.verify_password(password):
            log.info("Authentication successful.")
            return True
        else:
            log.warning("Authentication failed.")
            return False
