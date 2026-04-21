# Manu Phase 4 — Neural Voice + Vision

## Install dependencies

### Step 1: Neural voice
pip install edge-tts pygame

### Step 2: Emotion detection
pip install deepface opencv-python
# Note: deepface downloads ~500MB of models on first run (face detector)
# This is a one-time download. Let it complete before testing.

### Step 3: Screen reading (optional but impressive)
ollama pull llava
# ~4GB download. The llava model reads images and describes them.
# Without it, Manu falls back to OCR which is much less capable.

## Test Phase 4

Run Manu then test these commands:

1. Voice quality:
   Say anything → Manu should sound noticeably better than pyttsx3.
   Clear, natural, deep voice. This is the JARVIS voice.

2. Screen reading:
   Open a website or document, then say:
   "Hey Manu, what's on my screen?"
   → Manu should describe what's visible.

3. Face emotion:
   Say: "Hey Manu, how do I look?"
   → Manu uses webcam and tells you your detected emotion.

4. Vision status:
   Say: "Hey Manu, what are your vision capabilities?"
   → Reports which features are online vs offline.

5. Proactive emotion:
   Make a clearly sad or frustrated expression at the camera.
   Wait 60 seconds. Manu should comment on it.

## Voice options
Edit NEURAL_VOICE in engines/speech_engine.py:
  en-US-GuyNeural        → Deep American (JARVIS)
  en-IN-PrabhatNeural    → Indian English (matches your accent)
  en-GB-RyanNeural       → British male
  en-US-ChristopherNeural → Authoritative American

## Troubleshooting
- "edge-tts failed" → You're offline. pyttsx3 takes over automatically.
- "DeepFace download" → Let it complete. First run downloads models.
- "llava not found" → Run: ollama pull llava (4GB, one-time)
- No sound with pygame → Run: pip install pygame --upgrade
