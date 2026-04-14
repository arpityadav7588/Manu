"""
modules/memory/store.py
Bridge/Wrapper for MemoryManager to match Siri-mode MemoryStore interface.
"""
import logging
from modules.memory_manager import MemoryManager

log = logging.getLogger("Manu.MemoryStore")

class MemoryStore(MemoryManager):
    def __init__(self, db_path=None):
        # MemoryManager has its own hardcoded path, but we'll try to respect the new one
        super().__init__()
        if db_path:
            self.db_path = db_path
            self._init_db()
        log.info("MemoryStore (Bridge) initialized.")

    def start_session(self):
        # Stub for new session logic
        import uuid
        return str(uuid.uuid4())

    def end_session(self, session_id):
        # Stub
        pass
