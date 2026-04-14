import sys
import os

print(f"Python: {sys.version}")

try:
    import pvporcupine
    print(f"pvporcupine: OK ({pvporcupine.__version__ if hasattr(pvporcupine, '__version__') else 'found'})")
except ImportError:
    print("pvporcupine: FAILED")

try:
    import pvrecorder
    print(f"pvrecorder: OK ({pvrecorder.__version__ if hasattr(pvrecorder, '__version__') else 'found'})")
except ImportError:
    print("pvrecorder: FAILED")

try:
    import faster_whisper
    print("faster_whisper: OK")
except ImportError:
    print("faster_whisper: FAILED")

try:
    import pyttsx3
    print("pyttsx3: OK")
except ImportError:
    print("pyttsx3: FAILED")

try:
    import pystray
    print("pystray: OK")
except ImportError:
    print("pystray: FAILED")

try:
    import playsound
    print("playsound: OK")
except ImportError:
    print("playsound: FAILED")

try:
    import pyaudio
    print("pyaudio: OK")
except ImportError:
    print("pyaudio: FAILED")
