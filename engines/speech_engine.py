import pyttsx3
import subprocess
import os

class SpeechEngine:
    def __init__(self, use_piper=False, voice_model_path=None):
        self.use_piper = use_piper
        self.voice_model_path = voice_model_path
        
        # Initialize pyttsx3 fallback
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        # Try to find a male voice
        for voice in voices:
            if "david" in voice.name.lower() or "male" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.engine.setProperty('rate', 150) # WPM
        self.engine.setProperty('volume', 0.9)

    def speak(self, text):
        """
        Speaks text either via Piper (neural) or pyttsx3 (fallback).
        """
        if self.use_piper and self.voice_model_path and os.path.exists(self.voice_model_path):
            try:
                # Piper CLI usage: echo "Hello" | piper --model model.onnx --output_file - | play -t wav -
                # We'll use a simpler approach for the script
                # Note: This assumes piper.exe is in the path
                cmd = f'echo "{text}" | piper --model "{self.voice_model_path}" --output_file output.wav'
                subprocess.run(cmd, shell=True, check=True)
                # Play the generated wav (on Windows using 'start')
                subprocess.run("start output.wav", shell=True)
            except Exception as e:
                print(f"Piper error: {e}. Falling back to pyttsx3.")
                self._speak_fallback(text)
        else:
            self._speak_fallback(text)

    def _speak_fallback(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

if __name__ == "__main__":
    speech = SpeechEngine()
    speech.speak("Hello! I am Manu, your AI assistant. How can I help you today?")
