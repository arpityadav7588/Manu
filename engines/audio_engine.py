import speech_recognition as sr
import whisper
import os
import torch

class AudioEngine:
    def __init__(self, wake_word="manu", model="base"):
        self.wake_word = wake_word.lower()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Load local Whisper model
        # Models: 'tiny', 'base', 'small', 'medium', 'turbo'
        print(f"Loading Whisper model: {model}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.whisper_model = whisper.load_model(model, device=self.device)
        print(f"Model loaded on {self.device}.")

    def listen_and_recognize(self):
        """
        Listens to the microphone and uses Whisper to convert audio to text.
        """
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            audio_data = self.recognizer.listen(source)
            
            # Save audio to a temp file for Whisper to process
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_data.get_wav_data())
                
            # Perform Whisper recognition
            result = self.whisper_model.transcribe("temp_audio.wav")
            text = result['text'].strip().lower()
            
            # Cleanup temp file
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
                
            print(f"Recognized: {text}")
            return text

    def wait_for_wake_word(self):
        """
        Actively listens for the wake word in the background (simplified version).
        """
        while True:
            text = self.listen_and_recognize()
            if self.wake_word in text:
                print("Wake word detected!")
                return True
            else:
                print("Checking...")

if __name__ == "__main__":
    audio = AudioEngine()
    if audio.wait_for_wake_word():
        print("Success!")
