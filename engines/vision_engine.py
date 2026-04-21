"""
engines/vision_engine.py
Phase 4 — Vision capabilities for Manu.

Two features:
  1. FACE EMOTION DETECTION (background, every 60s)
     Uses DeepFace to analyze your webcam feed.
     Maps detected emotion to Manu's mood system.
     Manu comments proactively on significant changes.

  2. SCREEN READER (on-demand via voice command)
     PIL screenshot → base64 → Ollama llava model.
     "Hey Manu, what's on my screen?" → accurate description.
     Falls back to OCR (pytesseract) if llava not available.

DeepFace emotions → Manu moods:
  happy    → playful
  sad      → concerned
  angry    → concerned
  fear     → concerned
  surprise → excited (maps to enthusiastic)
  disgust  → concerned
  neutral  → neutral
"""

import base64
import io
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

log = logging.getLogger("Manu.Vision")

# ── Configuration ─────────────────────────────────────────────────────────────
EMOTION_CHECK_INTERVAL = 60      # Seconds between face checks
EMOTION_CONFIDENCE_MIN = 0.55    # Minimum confidence to act on emotion
OLLAMA_HOST            = "http://localhost:11434"
VISION_MODEL           = "llava"  # Ollama multimodal model for screen reading
SCREEN_CAPTURE_DIR     = Path("data") / "captures"

# DeepFace → Manu mood mapping
FACE_TO_MOOD = {
    "happy":    ("playful",      "You seem to be in a good mood."),
    "sad":      ("concerned",    "You look a bit down. Everything okay?"),
    "angry":    ("concerned",    "You look frustrated. Want to talk about it?"),
    "fear":     ("concerned",    "You look worried. Is everything alright?"),
    "surprise": ("enthusiastic", "Something caught you off guard there."),
    "disgust":  ("concerned",    "Something bothering you?"),
    "neutral":  ("neutral",      None),   # Neutral → no comment needed
}


class VisionEngine:
    """
    Webcam emotion detection and screen reading for Manu.

    Usage:
        vision = VisionEngine(speech_engine, emotion_manager, memory_manager)
        vision.start()            # Starts background emotion loop
        vision.read_screen()      # Returns description of current screen
        vision.check_emotion_once()  # One-shot face check
    """

    def __init__(self, speech_engine, emotion_manager, memory_manager):
        self.speech   = speech_engine
        self.emotions = emotion_manager
        self.memory   = memory_manager

        self._running        = False
        self._thread         = None
        self._last_emotion   = "neutral"
        self._last_check_ts  = 0.0
        self._deepface_ok    = False
        self._llava_ok       = False
        self._camera_ok      = False

        # Check available capabilities silently at init
        self._probe_deepface()
        self._probe_llava()
        self._probe_camera()

        SCREEN_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        log.info(
            f"VisionEngine ready. "
            f"DeepFace: {'✅' if self._deepface_ok else '❌ (install deepface)'}  "
            f"LLaVA: {'✅' if self._llava_ok else '❌ (run ollama pull llava)'}  "
            f"Camera: {'✅' if self._camera_ok else '❌ (no webcam found)'}"
        )

    # ── Capability Probing ────────────────────────────────────────────────────

    def _probe_deepface(self):
        try:
            import deepface  # noqa
            self._deepface_ok = True
        except ImportError:
            log.info("DeepFace not installed. Run: pip install deepface")

    def _probe_llava(self):
        try:
            import requests
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                self._llava_ok = any("llava" in m.lower() for m in models)
                if not self._llava_ok:
                    log.info(
                        "LLaVA not in Ollama. For screen reading run: "
                        "ollama pull llava"
                    )
        except Exception:
            pass

    def _probe_camera(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self._camera_ok = True
                cap.release()
        except ImportError:
            log.info("opencv-python not installed. Run: pip install opencv-python")
        except Exception:
            pass

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """Start background emotion detection loop."""
        if not self._deepface_ok or not self._camera_ok:
            log.info(
                "Vision background loop not started "
                "(DeepFace or camera unavailable)."
            )
            return

        self._running = True
        self._thread  = threading.Thread(
            target=self._emotion_loop,
            name="ManuVision",
            daemon=True,
        )
        self._thread.start()
        log.info(
            f"Vision emotion loop started. "
            f"Checking every {EMOTION_CHECK_INTERVAL}s."
        )

    def stop(self):
        self._running = False

    # ── Emotion Detection Loop ────────────────────────────────────────────────

    def _emotion_loop(self):
        """Background thread: check face emotion every N seconds."""
        # Wait before first check to let Manu finish greeting
        time.sleep(15)

        while self._running:
            try:
                self.check_emotion_once()
            except Exception as e:
                log.debug(f"Emotion loop error: {e}")
            time.sleep(EMOTION_CHECK_INTERVAL)

    def check_emotion_once(self) -> str | None:
        """
        Capture webcam frame, detect emotion, update Manu's mood.
        Returns detected emotion string or None on failure.
        Speaks proactively if emotion changed significantly.
        """
        if not self._deepface_ok or not self._camera_ok:
            return None

        frame = self._capture_frame()
        if frame is None:
            return None

        emotion, confidence = self._analyze_emotion(frame)
        if emotion is None or confidence < EMOTION_CONFIDENCE_MIN:
            return None

        log.debug(f"Face emotion: {emotion} (confidence: {confidence:.2f})")

        # Only react if emotion changed from last check
        if emotion != self._last_emotion:
            mood, comment = FACE_TO_MOOD.get(emotion, ("neutral", None))

            # Update Manu's mood
            if hasattr(self.emotions, "transition_mood"):
                self.emotions.transition_mood(mood, self.speech)
            else:
                self.emotions.set_mood(mood)

            # Speak proactively about significant emotion changes
            if comment and self._is_significant_change(self._last_emotion, emotion):
                time.sleep(0.5)   # Brief pause before commenting
                self.speech.speak_async(comment)
                log.info(f"Proactive emotion comment: '{comment}'")

            self._last_emotion = emotion

            # Log to memory
            try:
                self.memory.log_interaction(
                    f"[vision] face emotion: {emotion}",
                    f"[system] mood updated to: {mood}"
                )
            except Exception:
                pass

        return emotion

    def _capture_frame(self):
        """Capture a single frame from the default webcam."""
        try:
            import cv2
            import numpy as np

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None

            # Warm up camera (first few frames are often dark)
            for _ in range(3):
                cap.read()

            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                return frame
            return None

        except Exception as e:
            log.debug(f"Camera capture error: {e}")
            return None

    def _analyze_emotion(self, frame) -> tuple[str | None, float]:
        """
        Run DeepFace emotion analysis on a frame.
        Returns (emotion_string, confidence_float) or (None, 0.0).
        """
        try:
            from deepface import DeepFace

            # analyze() returns list of face results
            results = DeepFace.analyze(
                img_path=frame,
                actions=["emotion"],
                enforce_detection=False,   # Don't crash if no face found
                silent=True,
            )

            if not results:
                return None, 0.0

            result = results[0] if isinstance(results, list) else results
            emotions     = result.get("emotion", {})
            dominant     = result.get("dominant_emotion", "neutral")
            confidence   = emotions.get(dominant, 0) / 100.0   # Normalize to 0-1

            return dominant.lower(), confidence

        except Exception as e:
            log.debug(f"DeepFace analysis error: {e}")
            return None, 0.0

    def _is_significant_change(self, prev: str, curr: str) -> bool:
        """
        Decide if emotion change is significant enough to comment on.
        Avoids commenting on minor fluctuations.
        """
        # Always comment on these transitions
        significant_pairs = {
            ("neutral", "sad"), ("neutral", "angry"), ("neutral", "fear"),
            ("happy", "sad"), ("happy", "angry"),
            ("sad", "happy"), ("angry", "neutral"),
        }
        return (prev, curr) in significant_pairs or curr in ("sad", "angry", "fear")

    # ── Screen Reading ────────────────────────────────────────────────────────

    def read_screen(self, question: str = "What is on this screen?") -> str:
        """
        Capture screenshot and describe it using LLaVA or OCR.
        Called when user says "Hey Manu, what's on my screen?"

        Args:
            question: What to ask about the screen content.

        Returns:
            Natural language description string.
        """
        log.info(f"Screen read requested: '{question}'")

        # Capture screenshot
        screenshot_b64 = self._capture_screenshot()
        if screenshot_b64 is None:
            return (
                "I couldn't capture a screenshot right now. "
                "Make sure Pillow is installed: pip install Pillow"
            )

        # Try LLaVA first (most accurate)
        if self._llava_ok:
            result = self._describe_with_llava(screenshot_b64, question)
            if result:
                return result

        # Try OCR fallback
        ocr_text = self._extract_text_ocr(screenshot_b64)
        if ocr_text:
            return f"I can read this text on your screen: {ocr_text[:300]}"

        return (
            "I captured your screen but couldn't interpret it. "
            "Install LLaVA for full screen reading: ollama pull llava"
        )

    def _capture_screenshot(self) -> str | None:
        """
        Capture full screen as base64 PNG string.
        Returns base64 string or None on failure.
        """
        try:
            from PIL import ImageGrab
            import io

            img = ImageGrab.grab()

            # Resize to 1280x720 max to keep API payload small
            img.thumbnail((1280, 720))

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            b64 = base64.b64encode(buf.read()).decode("utf-8")

            # Also save to disk for logging
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = SCREEN_CAPTURE_DIR / f"screen_{ts}.png"
            img.save(str(path))
            log.debug(f"Screenshot saved: {path.name}")

            return b64

        except ImportError:
            log.warning("Pillow not installed. Run: pip install Pillow")
            return None
        except Exception as e:
            log.error(f"Screenshot failed: {e}")
            return None

    def _describe_with_llava(self, image_b64: str, question: str) -> str | None:
        """
        Send screenshot to Ollama LLaVA model for description.
        Returns natural language description or None on failure.
        """
        try:
            import requests

            payload = {
                "model":  VISION_MODEL,
                "prompt": (
                    f"{question} "
                    "Be concise and practical. Focus on what's most relevant. "
                    "If you see code, describe what it does. "
                    "If you see a website, say which site and what's on it. "
                    "Keep the response under 3 sentences."
                ),
                "images": [image_b64],
                "stream": False,
            }

            resp = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json=payload,
                timeout=30,
            )

            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                log.info(f"LLaVA response: {text[:100]}")
                return text if text else None

            log.warning(f"LLaVA API returned {resp.status_code}")
            return None

        except Exception as e:
            log.error(f"LLaVA describe error: {e}")
            self._llava_ok = False   # Disable until restart
            return None

    def _extract_text_ocr(self, image_b64: str) -> str | None:
        """
        Fallback: extract visible text from screenshot using pytesseract OCR.
        Much less capable than LLaVA but works offline.
        """
        try:
            import pytesseract
            from PIL import Image
            import io

            img_bytes = base64.b64decode(image_b64)
            img       = Image.open(io.BytesIO(img_bytes))
            text      = pytesseract.image_to_string(img).strip()

            if len(text) < 10:
                return None

            # Clean up OCR output
            lines       = [l.strip() for l in text.split("\n") if l.strip()]
            clean_text  = " | ".join(lines[:8])   # First 8 non-empty lines
            return clean_text if clean_text else None

        except ImportError:
            log.debug("pytesseract not installed (optional OCR fallback).")
            return None
        except Exception as e:
            log.debug(f"OCR error: {e}")
            return None

    # ── Ambient Awareness ─────────────────────────────────────────────────────

    def get_ambient_comment(self) -> str | None:
        """
        Generate a proactive comment based on current visual state.
        Called occasionally to make Manu feel more aware.
        Returns comment string or None if nothing worth saying.
        """
        if not self._deepface_ok or not self._camera_ok:
            return None

        emotion, confidence = self._analyze_emotion(
            self._capture_frame()
        ) if self._capture_frame() is not None else (None, 0)

        if emotion is None or confidence < 0.7:
            return None

        ambient_comments = {
            "happy":    "You seem to be in a good mood today.",
            "sad":      "You look a bit tired. Want me to play some music?",
            "angry":    "Looks like something's frustrating you. "
                        "Take a breath. What can I fix?",
            "neutral":  None,
        }

        return ambient_comments.get(emotion)

    # ── Status ────────────────────────────────────────────────────────────────

    @property
    def capabilities(self) -> dict:
        return {
            "emotion_detection": self._deepface_ok and self._camera_ok,
            "screen_reading":    self._llava_ok,
            "ocr_fallback":      True,   # Always try pytesseract
            "camera_available":  self._camera_ok,
        }
