"""
modules/memory/store.py
Bridge for MemoryManager to match Siri-mode MemoryStore interface.
main.py calls: MemoryStore(config.DB_PATH)
"""
import uuid
import logging
from modules.memory_manager import MemoryManager

log = logging.getLogger("Manu.MemoryStore")


class MemoryStore(MemoryManager):
    """
    Extends MemoryManager (no-arg __init__) with session tracking
    and the interface main.py expects.
    """

    def __init__(self, db_path=None):
        super().__init__()          # MemoryManager creates DB at data/manu.db
        log.info("MemoryStore (Bridge) initialized.")

    def start_session(self) -> str:
        """Record a new session and return its ID."""
        session_id = str(uuid.uuid4())
        try:
            from datetime import datetime
            ts = datetime.now().isoformat()
            with self._conn() as c:
                c.execute(
                    "INSERT INTO sessions (started_at) VALUES (?)", (ts,)
                )
        except Exception as e:
            log.debug(f"Session start logging error: {e}")
        return session_id

    def end_session(self, session_id: str):
        """Mark the most recent session as ended."""
        try:
            from datetime import datetime
            ts = datetime.now().isoformat()
            with self._conn() as c:
                c.execute(
                    "UPDATE sessions SET ended_at=? WHERE ended_at IS NULL",
                    (ts,)
                )
        except Exception as e:
            log.debug(f"Session end logging error: {e}")

    def log_interaction(self, role_or_user: str, text: str):
        """
        Overloaded to handle both calling conventions:
          - Siri-mode:  memory.log_interaction("user", command_text)
          - Phase-1:    memory.log_interaction(user_text, manu_text)
        """
        if role_or_user in ("user", "assistant"):
            # Siri-mode calling convention: log as half of a turn
            # Store with role marker so we can reconstruct later
            super().log_interaction(
                user_text=text if role_or_user == "user" else "",
                manu_text=text if role_or_user == "assistant" else "",
            )
        else:
            # Phase-1 calling convention: both texts at once
            super().log_interaction(user_text=role_or_user, manu_text=text)
