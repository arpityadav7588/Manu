"""
engines/speech_engine.py
Phase 4 — Neural TTS for Manu using edge-tts.

Primary:  edge-tts with en-US-GuyNeural (Microsoft Neural, JARVIS-quality)
Fallback: pyttsx3 (offline, always available)

edge-tts uses Microsoft's Azure speech stack locally via the Edge browser
protocol. It requires internet on first use but the voice sounds genuinely
like JARVIS — deep, clear, confident, natural prosody.

Voice options (change NEURAL_VOICE to switch):
  en-US-GuyNeural       → Deep American male (JARVIS-closest)
  en-US-ChristopherNeural → Authoritative American male
  en-US-EricNeural      → Clear American male
  en-IN-PrabhatNeural   → Indian English male (matches your accent)
  en-GB-RyanNeural      → British male (classic butler tone)
"""

import asyncio
import logging
import os
import tempfile
import threading
import time
from pathlib import Path

log = logging.getLogger("Manu.Speech")

# ── Voice configuration ───────────────────────────────────────────────────────
NEURAL_VOICE  = "en-US-GuyNeural"    # Change this to switch voice
NEURAL_RATE   = "+5%"                # Slight speed boost over default
NEURAL_VOLUME = "+0%"                # Volume adjustment

# Mood → neural voice prosody adjustments
MOOD_PROSODY = {
    "enthusiastic": {"rate": "+18%", "volume": "+8%",  "pitch": "+3Hz"},
    "happy":        {"rate": "+10%", "volume": "+5%",  "pitch": "+1Hz"},
    "neutral":      {"rate": "+5%",  "volume": "+0%",  "pitch": "+0Hz"},
    "playful":      {"rate": "+15%", "volume": "+6%",  "pitch": "+2Hz"},
    "grateful":     {"rate": "+0%",  "volume": "-2%",  "pitch": "-1Hz"},
    "concerned":    {"rate": "-10%", "volume": "-8%",  "pitch": "-2Hz"},
    "sleepy":       {"rate": "-18%", "volume": "-15%", "pitch": "-3Hz"},
    "thinking":     {"rate": "+0%",  "volume": "+0%",  "pitch": "+0Hz"},
}

# pyttsx3 fallback mood parameters
PYTTSX3_MOOD = {
    "enthusiastic": {"rate": 195, "volume": 0.95},
    "happy":        {"rate": 185, "volume": 0.92},
    "neutral":      {"rate": 175, "volume": 0.90},
    "playful":      {"rate": 190, "volume": 0.93},
    "grateful":     {"rate": 168, "volume": 0.88},
    "concerned":    {"rate": 158, "volume": 0.82},
    "sleepy":       {"rate": 142, "volume": 0.75},
    "thinking":     {"rate": 175, "volume": 0.90},
}


class SpeechEngine:
    """
    Neural TTS engine for Manu.
    Automatically uses best available backend:
      1. edge-tts (neural, JARVIS-quality, needs internet)
      2. pyttsx3  (offline, always works, less natural)

    Thread-safe. All speak() calls serialize via lock.
    Emotion-aware: apply_mood() adjusts prosody/rate dynamically.
    """

    def __init__(self):
        self._lock          = threading.Lock()
        self._speaking      = False
        self._current_mood  = "neutral"

        # Rate/volume state for pyttsx3 fallback
        self._rate   = 175
        self._volume = 0.90

        # Backend state
        self._edge_available   = False
        self._pyttsx3_engine   = None
        self._pygame_available = False

        # Temp dir for audio files
        self._tmp_dir = Path(tempfile.gettempdir()) / "manu_tts"
        self._tmp_dir.mkdir(exist_ok=True)

        self._init_backends()

    # ── Initialization ────────────────────────────────────────────────────────

    def _init_backends(self):
        """Initialize available TTS backends. Never crashes."""
        # Try edge-tts
        try:
            import edge_tts  # noqa — just checking import
            self._edge_available = True
            log.info(f"Neural TTS ready: edge-tts ({NEURAL_VOICE}) ✅")
        except ImportError:
            log.warning(
                "edge-tts not installed — using pyttsx3 fallback.\n"
                "  Install for JARVIS voice: pip install edge-tts pygame"
            )

        # Try pygame for audio playback
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
            self._pygame_available = True
            log.debug("pygame mixer ready for audio playback.")
        except ImportError:
            log.debug("pygame not installed — will use playsound/winsound.")
        except Exception as e:
            log.debug(f"pygame init failed: {e}")

        # Always init pyttsx3 as fallback
        self._init_pyttsx3()

    def _init_pyttsx3(self):
        """Initialize pyttsx3 offline TTS."""
        try:
            import pyttsx3
            self._pyttsx3_engine = pyttsx3.init()
            self._pyttsx3_engine.setProperty("rate",   self._rate)
            self._pyttsx3_engine.setProperty("volume", self._volume)
            self._select_pyttsx3_voice()
            log.info("pyttsx3 fallback TTS ready ✅")
        except Exception as e:
            log.warning(f"pyttsx3 init failed: {e}. TTS will be console-only.")
            self._pyttsx3_engine = None

    def _select_pyttsx3_voice(self):
        """Auto-select best male English voice in pyttsx3."""
        if not self._pyttsx3_engine:
            return
        try:
            voices   = self._pyttsx3_engine.getProperty("voices")
            keywords = ["david", "mark", "george", "james", "daniel",
                        "male", "man", "guy"]
            for kw in keywords:
                for v in voices:
                    if kw in v.name.lower():
                        self._pyttsx3_engine.setProperty("voice", v.id)
                        log.info(f"pyttsx3 voice: {v.name}")
                        return
            if voices:
                self._pyttsx3_engine.setProperty("voice", voices[0].id)
        except Exception as e:
            log.debug(f"Voice selection error: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str, rate: int = None, volume: float = None):
        """
        Speak text aloud. Blocks until speech completes.
        Uses edge-tts neural voice if available, else pyttsx3.
        Also prints to console.
        """
        if not text or not text.strip():
            return

        # Clean text for speech (remove markdown, extra spaces)
        text = self._clean_for_speech(text)

        print(f"\n🔊 Manu: {text}\n")
        log.info(f"Speaking ({self._current_mood}): {text[:80]}")

        with self._lock:
            self._speaking = True
            try:
                if self._edge_available:
                    success = self._speak_edge(text)
                    if not success:
                        self._speak_pyttsx3(text, rate, volume)
                else:
                    self._speak_pyttsx3(text, rate, volume)
            except Exception as e:
                log.error(f"speak() error: {e}")
                print(f"[Manu - TTS error]: {text}")
            finally:
                self._speaking = False

    def speak_async(self, text: str, rate: int = None, volume: float = None):
        """Non-blocking speak. Returns immediately. Runs in daemon thread."""
        thread = threading.Thread(
            target=self.speak,
            args=(text,),
            kwargs={"rate": rate, "volume": volume},
            daemon=True,
            name="ManuSpeak",
        )
        thread.start()

    def set_rate(self, rate: int):
        """Set pyttsx3 fallback speech rate."""
        self._rate = max(100, min(400, rate))
        if self._pyttsx3_engine:
            try:
                self._pyttsx3_engine.setProperty("rate", self._rate)
            except Exception:
                pass

    def set_volume(self, volume: float):
        """Set pyttsx3 fallback volume."""
        self._volume = max(0.0, min(1.0, volume))
        if self._pyttsx3_engine:
            try:
                self._pyttsx3_engine.setProperty("volume", self._volume)
            except Exception:
                pass

    def apply_mood(self, mood: str):
        """
        Apply emotion-driven voice modulation.
        For edge-tts: adjusts SSML rate/pitch/volume.
        For pyttsx3: adjusts rate and volume.
        Called by EmotionManager on mood transitions.
        """
        self._current_mood = mood

        # Apply pyttsx3 params immediately for fallback
        params = PYTTSX3_MOOD.get(mood, PYTTSX3_MOOD["neutral"])
        self.set_rate(params["rate"])
        self.set_volume(params["volume"])
        log.debug(f"Voice mood applied: {mood}")

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    @property
    def is_available(self) -> bool:
        return self._edge_available or self._pyttsx3_engine is not None

    @property
    def backend_name(self) -> str:
        if self._edge_available:
            return f"edge-tts ({NEURAL_VOICE})"
        if self._pyttsx3_engine:
            return "pyttsx3 (offline)"
        return "none"

    # ── edge-tts Backend ──────────────────────────────────────────────────────

    def _speak_edge(self, text: str) -> bool:
        """
        Speak using edge-tts neural voice.
        Generates MP3 to temp file, plays via pygame or winsound.
        Returns True on success, False on failure.
        """
        try:
            # Build SSML with mood-adjusted prosody
            prosody = MOOD_PROSODY.get(self._current_mood, MOOD_PROSODY["neutral"])
            ssml_text = (
                f'<speak version="1.0" '
                f'xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
                f'<voice name="{NEURAL_VOICE}">'
                f'<prosody rate="{prosody["rate"]}" '
                f'volume="{prosody["volume"]}" '
                f'pitch="{prosody["pitch"]}">'
                f'{self._escape_ssml(text)}'
                f'</prosody></voice></speak>'
            )

            # Generate audio file
            audio_path = self._tmp_dir / "manu_speech.mp3"
            self._run_edge_tts(ssml_text, str(audio_path))

            if not audio_path.exists() or audio_path.stat().st_size < 100:
                log.warning("edge-tts produced empty audio file.")
                return False

            # Play the audio
            self._play_audio(str(audio_path))
            return True

        except Exception as e:
            log.warning(f"edge-tts failed: {e} — switching to pyttsx3.")
            self._edge_available = False
            return False

    def _run_edge_tts(self, ssml: str, output_path: str):
        """Run edge-tts async generation synchronously."""
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(
                text=ssml,
                voice=NEURAL_VOICE,
            )
            await communicate.save(output_path)

        # Run async in new event loop (avoids conflicts with existing loops)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_generate())
        finally:
            loop.close()

    def _play_audio(self, file_path: str):
        """Play a WAV or MP3 file using best available method."""
        if self._pygame_available:
            try:
                import pygame
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                return
            except Exception as e:
                log.debug(f"pygame playback failed: {e}")

        # Windows fallback: winsound
        import platform
        if platform.system() == "Windows":
            try:
                import winsound
                # winsound only plays WAV — convert if needed
                if file_path.endswith(".mp3"):
                    wav_path = file_path.replace(".mp3", ".wav")
                    self._mp3_to_wav(file_path, wav_path)
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                else:
                    winsound.PlaySound(file_path, winsound.SND_FILENAME)
                return
            except Exception as e:
                log.debug(f"winsound failed: {e}")

        # Cross-platform fallback: playsound
        try:
            import playsound
            playsound.playsound(file_path, block=True)
        except ImportError:
            log.warning("No audio playback library available. Install: pip install pygame")
        except Exception as e:
            log.debug(f"playsound failed: {e}")

    def _mp3_to_wav(self, mp3_path: str, wav_path: str):
        """Convert MP3 to WAV using pydub if available."""
        try:
            from pydub import AudioSegment
            sound = AudioSegment.from_mp3(mp3_path)
            sound.export(wav_path, format="wav")
        except ImportError:
            # Try ffmpeg directly
            import subprocess
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, wav_path],
                capture_output=True, timeout=10
            )

    # ── pyttsx3 Fallback ──────────────────────────────────────────────────────

    def _speak_pyttsx3(self, text: str, rate: int = None, volume: float = None):
        """Speak using pyttsx3 offline engine."""
        if not self._pyttsx3_engine:
            return

        try:
            if rate is not None:
                self._pyttsx3_engine.setProperty("rate", rate)
            if volume is not None:
                self._pyttsx3_engine.setProperty("volume", volume)

            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()

        except RuntimeError:
            # Engine crashed — reinit
            self._init_pyttsx3()
            if self._pyttsx3_engine:
                try:
                    self._pyttsx3_engine.say(text)
                    self._pyttsx3_engine.runAndWait()
                except Exception:
                    pass
        except Exception as e:
            log.error(f"pyttsx3 error: {e}")
        finally:
            # Restore permanent settings after temp override
            if rate is not None and self._pyttsx3_engine:
                try:
                    self._pyttsx3_engine.setProperty("rate", self._rate)
                except Exception:
                    pass
            if volume is not None and self._pyttsx3_engine:
                try:
                    self._pyttsx3_engine.setProperty("volume", self._volume)
                except Exception:
                    pass

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _clean_for_speech(self, text: str) -> str:
        """Remove markdown and special chars that sound bad when spoken."""
        import re
        # Remove markdown formatting
        text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)   # bold/italic
        text = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", text)      # code
        text = re.sub(r"#{1,6}\s+", "", text)                  # headers
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)        # links
        text = re.sub(r"[_~]", "", text)                       # underscores
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _escape_ssml(self, text: str) -> str:
        """Escape special XML characters for SSML."""
        return (text
                .replace("&",  "&amp;")
                .replace("<",  "&lt;")
                .replace(">",  "&gt;")
                .replace('"',  "&quot;")
                .replace("'",  "&apos;"))
