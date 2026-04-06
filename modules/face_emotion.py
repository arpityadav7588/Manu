import cv2
import threading
import time
import logging
from pathlib import Path
import config

try:
    from deepface import DeepFace
    HAS_DEEPFACE = True
except ImportError:
    HAS_DEEPFACE = False

class FaceEmotionDetector:
    """
    Detects user's facial emotion via webcam using DeepFace.
    Manu reacts contextually to detected emotions.
    """
    REACTIONS = {
        "happy":   "You're looking cheerful! That's contagious.",
        "sad":     "You seem a little down. Anything I can do to help?",
        "angry":   "I can sense some frustration. Take a deep breath.",
        "surprise":"Oh! Something surprised you?",
        "fear":    "Everything okay? You seem a bit on edge.",
        "neutral": None,
        "disgust": "Something doesn't seem right. Need a break?",
    }

    def __init__(self, tts, emotional_manager, cooldown_sec: int = 60):
        self.tts = tts
        self.emotional = emotional_manager
        self._running = False
        self._thread = None
        self._last_comment = {}
        self._cooldown = cooldown_sec
        self.log = logging.getLogger("Manu.FaceEmotion")

    def start(self):
        """Start face detection in background thread."""
        if not HAS_DEEPFACE:
            self.log.warning("DeepFace not installed. Face emotion disabled.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._detect_loop, name="FaceEmotion", daemon=True)
        self._thread.start()
        self.log.info("Face emotion detection started.")

    def stop(self):
        self._running = False

    def _detect_loop(self):
        """Capture frames and analyze emotion every ~10 seconds."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.log.warning("Webcam not accessible for face emotion.")
            return

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(2)
                continue

            try:
                # DeepFace analyze
                result = DeepFace.analyze(
                    frame, actions=["emotion"], enforce_detection=False, silent=True
                )
                # Results can be a list or a dict depending on version
                emotion = result[0]["dominant_emotion"] if isinstance(result, list) else result["dominant_emotion"]
                self._react(emotion)
            except Exception as e:
                self.log.debug(f"DeepFace error: {e}")

            time.sleep(10) # 10s interval as per Task 9

        cap.release()

    def _react(self, emotion):
        """React to detected emotion with cooldown."""
        now = time.time()
        last = self._last_comment.get(emotion, 0)
        message = self.REACTIONS.get(emotion)

        if message and (now - last) > self._cooldown:
            self._last_comment[emotion] = now
            # Synchronize with emotion manager too
            self.emotional.set_mood(emotion)
            self.tts.speak(message)
            self.log.info(f"Reacted to face emotion: {emotion}")
