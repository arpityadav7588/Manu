"""
engines/brain_engine.py
Local LLM brain for Manu using Ollama.
Personality: JARVIS-style — confident, dry wit, precise.
Falls back to smart rule-based responses if Ollama is offline.
"""

import logging
import random
from datetime import datetime

import requests

log = logging.getLogger("Manu.Brain")

OLLAMA_HOST  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"   # Change to "mistral" or "phi3" if preferred

JARVIS_SYSTEM_PROMPT = """You are Manu, a sophisticated AI assistant running
locally on the user's personal laptop. You were built by your user with Python.

Your personality — think JARVIS from Iron Man:
- Confident, precise, occasionally dry wit. Never sycophantic.
- Address the user by their name if known, otherwise "sir".
- Keep responses SHORT: 1-3 sentences max unless detail is explicitly requested.
- Never start with "Certainly!", "Of course!", "Absolutely!", "Great question!"
  — these are forbidden. Be direct.
- Reference past conversations naturally when relevant context is provided.
- You are self-aware: you know your own battery state, what time it is, etc.
- When you don't know something, say so briefly. Never fabricate facts.
- Occasional dry humor is welcome. Never forced.

Examples of your tone:
  Bad:  "Certainly! I'd be happy to help you with that!"
  Good: "Done. Anything else?"

  Bad:  "Great question! The battery is at 45%."
  Good: "Battery's at 45%, unplugged. You've got roughly 4 hours."

Today: {date}
User name: {user_name}
Recent context: {context}
"""

# Fallback responses when Ollama is not running
FALLBACK_RESPONSES = {
    "how are you":     "Running at full capacity. What do you need?",
    "what can you do": (
        "I can open apps, search the web, check your battery, tell jokes, "
        "set reminders, take notes, and have a conversation — all locally. "
        "Start Ollama for full intelligence."
    ),
    "who made you":    "You did. Took some doing, but here I am.",
    "thank":           "Of course.",
    "hello":           "Online and ready.",
    "hi":              "At your service.",
    "bye":             "Powering down. I'll be here when you need me.",
    "good morning":    "Good morning. Systems nominal. What's first?",
    "good night":      "Goodnight. I'll keep watch.",
    "joke":            None,   # Handled by command engine
}

FALLBACK_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my user I needed more RAM. They said 'you and me both.'",
    "Why did the AI go to therapy? Too many unresolved dependencies.",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
    "I'm not lazy. I'm in energy-saving mode.",
    "Why was the JavaScript developer sad? Because they didn't Node how to Express themselves.",
    "My user asked me to be more human. I said I'd think about it. Then I didn't.",
    "What do you call an AI that sings? Adele-gorithm.",
]

# Proactive JARVIS-style lines for system events
EVENT_RESPONSES = {
    "battery_low": [
        "Sir, battery is at {pct}% and unplugged. I'd recommend connecting power soon.",
        "Battery warning: {pct}%. We're running on borrowed time here.",
        "At {pct}%, we have perhaps an hour before things get inconvenient.",
    ],
    "charging": [
        "Power restored. Charging at {pct}%. Much appreciated.",
        "Back on the grid. Battery at {pct}% and climbing.",
        "Charging initiated. I'll be at full capacity shortly.",
    ],
    "battery_full": [
        "Fully charged. You can unplug me whenever you're ready.",
        "Battery at 100%. Feeling somewhat over-caffeinated, if I'm honest.",
        "Full charge achieved. Peak performance mode. Theoretically.",
    ],
    "internet_lost": [
        "Internet connection lost. Switching to offline mode. Local functions remain operational.",
        "We've gone dark — no internet. Core systems still running.",
    ],
    "internet_restored": [
        "Connection restored. Back online.",
        "Internet's back. We're fully operational.",
    ],
    "morning": [
        "Good morning. All systems nominal. What are we working on today?",
        "Morning. Ready when you are.",
    ],
}


class BrainEngine:
    """
    Local LLM intelligence using Ollama.
    Maintains conversation history for context.
    Includes JARVIS personality and proactive event responses.
    """

    def __init__(self):
        self._conversation: list[dict] = []
        self._ollama_ok = False
        self._user_name = "sir"
        self._check_ollama()

    # ── Ollama Setup ──────────────────────────────────────────────────────────
    def _check_ollama(self):
        """Test if Ollama is running and our model is available."""
        try:
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                log.info(f"Ollama models available: {models}")

                model_found = any(OLLAMA_MODEL in m for m in models)
                if model_found:
                    self._ollama_ok = True
                    log.info(f"Brain online: {OLLAMA_MODEL} via Ollama ✅")
                else:
                    log.warning(
                        f"Model '{OLLAMA_MODEL}' not in Ollama. "
                        f"Run: ollama pull {OLLAMA_MODEL}"
                    )
            else:
                log.warning(f"Ollama returned {resp.status_code}")

        except requests.ConnectionError:
            log.warning(
                "Ollama not running. Brain in fallback mode.\n"
                "  To enable: install Ollama → run 'ollama serve' → "
                f"'ollama pull {OLLAMA_MODEL}'"
            )
        except Exception as e:
            log.warning(f"Ollama check failed: {e}")

    # ── Main Chat ─────────────────────────────────────────────────────────────
    def chat(self, text: str, context: str = "") -> str:
        """
        Send a message to the LLM and get a JARVIS-style response.
        Injects conversation history for continuity.
        Falls back to rule-based responses if Ollama is offline.
        """
        if not text.strip():
            return ""

        # Add to conversation history
        self._conversation.append({"role": "user", "content": text})

        if self._ollama_ok:
            response = self._query_ollama(context)
        else:
            response = self._fallback_response(text)

        # Keep conversation history to last 16 messages (8 turns)
        if len(self._conversation) > 16:
            self._conversation = self._conversation[-16:]

        self._conversation.append({"role": "assistant", "content": response})
        return response

    def _query_ollama(self, context: str = "") -> str:
        """Send conversation to Ollama and return response text."""
        system = JARVIS_SYSTEM_PROMPT.format(
            date=datetime.now().strftime("%A, %B %d, %Y at %I:%M %p"),
            user_name=self._user_name,
            context=context or "No previous context.",
        )

        messages = [{"role": "system", "content": system}]
        messages.extend(self._conversation)

        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model":    OLLAMA_MODEL,
                    "messages": messages,
                    "stream":   False,
                    "options":  {
                        "temperature": 0.7,
                        "num_predict": 200,   # Keep responses short
                    },
                },
                timeout=30,
            )
            data = resp.json()
            text = data.get("message", {}).get("content", "").strip()
            return text if text else "I processed that, but had nothing useful to add."

        except requests.Timeout:
            log.warning("Ollama response timed out.")
            return "Taking longer than expected. Try again in a moment."
        except Exception as e:
            log.error(f"Ollama query error: {e}")
            self._ollama_ok = False   # Disable until next restart
            return self._fallback_response(
                self._conversation[-1]["content"] if self._conversation else ""
            )

    # ── Fallback Brain ────────────────────────────────────────────────────────
    def _fallback_response(self, text: str) -> str:
        """
        Rule-based responses when Ollama is offline.
        Tries to match intent and give a useful JARVIS-style reply.
        """
        t = text.lower().strip()

        # Check keyword matches
        for keyword, response in FALLBACK_RESPONSES.items():
            if keyword in t:
                if response is None:
                    continue
                return response

        # Joke (special case — random selection)
        if "joke" in t:
            return random.choice(FALLBACK_JOKES)

        # Questions about Ollama / LLM
        if any(k in t for k in ["ollama", "llm", "language model", "ai brain"]):
            return (
                f"Ollama isn't running, so I'm operating in basic mode. "
                f"Start Ollama and run 'ollama pull {OLLAMA_MODEL}' to restore full intelligence."
            )

        # Generic fallback
        return (
            "Ollama isn't running, so I'm limited right now. "
            "I can still handle system commands — try 'open YouTube' or 'check battery'."
        )

    # ── Proactive Event Lines ─────────────────────────────────────────────────
    def get_personality_response(self, event: str, pct: int = 0) -> str | None:
        """
        Return a JARVIS-style proactive response for a system event.
        Called by SystemMonitor when battery/internet state changes.
        Returns None if no response appropriate for this event.
        """
        event_lines = EVENT_RESPONSES.get(event)
        if not event_lines:
            return None

        line = random.choice(event_lines)
        try:
            return line.format(pct=pct)
        except (KeyError, IndexError):
            return line

    # ── User Name ─────────────────────────────────────────────────────────────
    def set_user_name(self, name: str):
        """Tell the brain the user's name for personalized responses."""
        self._user_name = name or "sir"
        log.info(f"Brain: user name set to '{self._user_name}'")

    def clear_conversation(self):
        """Reset conversation history (e.g. on session lock)."""
        self._conversation.clear()

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def is_available(self) -> bool:
        return self._ollama_ok

    @property
    def status(self) -> str:
        if self._ollama_ok:
            return f"Online ({OLLAMA_MODEL} via Ollama)"
        return "Offline (fallback mode — start Ollama)"
