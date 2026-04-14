"""
modules/events/monitor.py
Bridge for SystemMonitor to match EventMonitor interface.
Wires battery/internet events to EmotionalStateManager + TTS.
"""
import logging
from modules.system_monitor import SystemMonitor

log = logging.getLogger("Manu.EventMonitor")


class EventMonitor(SystemMonitor):
    """
    Extends SystemMonitor with emotional + TTS integration.
    main.py instantiates as: EventMonitor(emotional, tts, memory)
    and calls monitor.start().
    """

    def __init__(self, emotional, tts, memory):
        self.emotional = emotional
        self.tts       = tts
        self.memory    = memory
        # SystemMonitor.__init__(callback) — takes exactly one arg
        super().__init__(callback=self._handle_event)
        log.info("EventMonitor (Bridge) initialized.")

    def _handle_event(self, event: str, detail: int):
        """
        Unified event handler called by SystemMonitor background loop.
        Routes events to emotional state + TTS.
        """
        log.info(f"System event: {event} | detail={detail}")

        # 1. Update emotional state
        if self.emotional:
            try:
                self.emotional.update_mood_on_event(event, detail)
            except Exception as e:
                log.debug(f"Emotion update error: {e}")

        # 2. Generate JARVIS-style spoken response
        try:
            from engines.brain_engine import BrainEngine
            # Use the static event responses directly
            from engines.brain_engine import EVENT_RESPONSES
            import random

            event_lines = EVENT_RESPONSES.get(event)
            if event_lines and self.tts:
                line = random.choice(event_lines)
                try:
                    spoken = line.format(pct=detail)
                except (KeyError, IndexError):
                    spoken = line
                self.tts.speak_async(spoken)
        except Exception as e:
            log.debug(f"Event speech error: {e}")

        # 3. Log security-relevant events
        if self.memory and event in ("battery_low", "internet_lost"):
            try:
                self.memory.log_security_event(f"system_{event}_{detail}")
            except Exception:
                pass
