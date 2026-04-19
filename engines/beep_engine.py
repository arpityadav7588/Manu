"""
engines/beep_engine.py
Generates and plays short beep tones for Manu's Siri-style feedback.
Uses only Python stdlib (wave, math, struct) — zero extra dependencies.

Two tones:
  ACTIVATE  (880Hz, 150ms) — "I heard you, tell me what you need"
  DEACTIVATE (440Hz, 100ms) — "Got it, processing done"
"""

import io
import logging
import math
import struct
import threading
import wave
from pathlib import Path

log = logging.getLogger("Manu.Beep")

ASSETS_DIR = Path("assets")

# Beep file paths
BEEP_ON_PATH  = ASSETS_DIR / "beep_on.wav"
BEEP_OFF_PATH = ASSETS_DIR / "beep_off.wav"


class BeepEngine:
    """
    Plays short WAV beep tones.
    Auto-generates the WAV files on first run using only stdlib.
    Uses pygame for playback if available, falls back to winsound (Windows)
    or subprocess (Linux/Mac).
    """

    def __init__(self):
        ASSETS_DIR.mkdir(exist_ok=True)
        self._generate_all_beeps()
        self._pygame_ready = self._init_pygame()
        log.info("BeepEngine ready.")

    # ── Pygame Init ───────────────────────────────────────────────────────────

    def _init_pygame(self) -> bool:
        """Try to initialize pygame mixer for high-quality playback."""
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            return True
        except ImportError:
            log.debug("pygame not installed — using OS fallback for beeps.")
            return False
        except Exception as e:
            log.debug(f"pygame mixer init failed: {e}")
            return False

    # ── WAV Generation ────────────────────────────────────────────────────────

    def _generate_all_beeps(self):
        """Generate beep WAV files if they don't already exist."""
        if not BEEP_ON_PATH.exists():
            self._generate_wav(BEEP_ON_PATH,  freq=880, duration_ms=150, volume=0.6)
            log.debug(f"Generated {BEEP_ON_PATH}")

        if not BEEP_OFF_PATH.exists():
            self._generate_wav(BEEP_OFF_PATH, freq=440, duration_ms=100, volume=0.4)
            log.debug(f"Generated {BEEP_OFF_PATH}")

    def _generate_wav(
        self,
        path: Path,
        freq: int,
        duration_ms: int,
        volume: float = 0.5
    ):
        """
        Generate a pure sine wave WAV file using only stdlib.
        Adds fade-in and fade-out envelope to avoid clicks.

        Args:
            path:        Output file path
            freq:        Frequency in Hz (e.g. 880 for high A)
            duration_ms: Duration in milliseconds
            volume:      Peak amplitude 0.0–1.0
        """
        sample_rate = 44100
        n_samples   = int(sample_rate * duration_ms / 1000)
        amplitude   = int(32767 * volume)
        fade_len    = min(200, n_samples // 4)   # Fade in/out length in samples

        frames = []
        for i in range(n_samples):
            # Sine wave
            t       = i / sample_rate
            sample  = math.sin(2 * math.pi * freq * t)

            # Fade-in envelope
            if i < fade_len:
                envelope = i / fade_len
            # Fade-out envelope
            elif i > n_samples - fade_len:
                envelope = (n_samples - i) / fade_len
            else:
                envelope = 1.0

            value = int(amplitude * sample * envelope)
            # Pack as 16-bit signed little-endian
            frames.append(struct.pack("<h", value))

        raw_frames = b"".join(frames)

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)          # Mono
            wf.setsampwidth(2)          # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(raw_frames)

    # ── Playback ──────────────────────────────────────────────────────────────

    def play_activate(self):
        """Play the high activation beep (non-blocking)."""
        self._play_async(BEEP_ON_PATH)

    def play_deactivate(self):
        """Play the low deactivation beep (non-blocking)."""
        self._play_async(BEEP_OFF_PATH)

    def _play_async(self, wav_path: Path):
        """Play a WAV file in a daemon thread so it never blocks."""
        thread = threading.Thread(
            target=self._play_sync,
            args=(wav_path,),
            daemon=True,
            name="ManuBeep",
        )
        thread.start()

    def _play_sync(self, wav_path: Path):
        """Play a WAV file synchronously (runs inside thread)."""
        if not wav_path.exists():
            log.warning(f"Beep file missing: {wav_path}")
            return

        # Try pygame first (best quality + volume control)
        if self._pygame_ready:
            try:
                import pygame
                sound = pygame.mixer.Sound(str(wav_path))
                sound.play()
                # Wait for beep to finish (non-blocking for thread, fine here)
                pygame.time.wait(int(sound.get_length() * 1000) + 50)
                return
            except Exception as e:
                log.debug(f"pygame play failed: {e}")

        # Windows fallback: winsound
        import platform
        if platform.system() == "Windows":
            try:
                import winsound
                winsound.PlaySound(str(wav_path), winsound.SND_FILENAME)
                return
            except Exception as e:
                log.debug(f"winsound failed: {e}")

        # Linux/Mac fallback: aplay / afplay
        import subprocess
        import platform as _plat
        try:
            if _plat.system() == "Darwin":
                subprocess.run(["afplay", str(wav_path)],
                               capture_output=True, timeout=2)
            else:
                subprocess.run(["aplay", str(wav_path)],
                               capture_output=True, timeout=2)
        except Exception as e:
            log.debug(f"OS beep fallback failed: {e}")
