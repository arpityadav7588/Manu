"""
modules/events/monitor.py
Bridge for SystemMonitor to match EventMonitor interface.
Preserves battery, internet, and CPU monitoring logic.
"""
import logging
from modules.system_monitor import SystemMonitor

log = logging.getLogger("Manu.EventMonitor")

class EventMonitor(SystemMonitor):
    def __init__(self, emotional, tts, memory):
        self.emotional = emotional
        self.tts = tts
        self.memory = memory
        # Link existing callback system to our internal handler
        super().__init__(callback=self._handle_bridge_event, memory=memory)
        log.info("EventMonitor (Bridge) initialized.")

    def _handle_bridge_event(self, event, detail):
        """Unified event handling from SystemMonitor."""
        log.info(f"System Event: {event} | {detail}")
        
        # 1. Update Emotional State
        if self.emotional:
            react = self.emotional.react_to_battery(detail, True, event == "charging") if event.startswith("battery") or event == "charging" else None
            if not react and event.startswith("internet"):
                react = self.emotional.react_to_internet(event == "internet_on")
            
            if react:
                self.tts.speak(react)
        
        # 2. Special Logic Ported from old main.py
        if event == "high_cpu":
            self.tts.speak(f"Notice: CPU usage is quite high at {detail}%. I might be a bit slower.")
        
        if event == "reminder":
             self.tts.speak(f"Here is your reminder: {detail}")
