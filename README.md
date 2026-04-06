# Manu AI: Hyper-Modular Desktop Assistant

Manu is a premium, locally-running AI assistant with 3D visualization, emotional intelligence, and advanced productivity skills.

## 🌟 Key Features

- **3D Hologram Avatar**: PyOpenGL-based wireframe torus that reacts to your voice and emotions.
- **Biometric Security**: Face ID enrollment and verification via `face_recognition`.
- **Emotional Intelligence**: Real-time mood analysis using `DeepFace` with modulated TTS responses.
- **Advanced Memory**: Persistence via SQLite with habit tracking and contextual recall.
- **Skill Plugin System**: Easy-to-expand architecture for custom skills (Motivation, Dice, Word of Day).
- **Productivity Suite**: Clipboard AI, screen reading, voice notes, and morning briefings.
- **Offline First**: Optimized for local LLMs via Ollama (`llama3:8b`).

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) (running `llama3:8b`)
- Webcam & Microphone

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/arpityadav7588/Manu
cd Manu

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Verification
Run the system health check to ensure everything is configured correctly:
```powershell
python health_check.py
```

### 4. Launch
```powershell
python main.py
```

## 🛠️ Project Structure
- `engines/`: Core logic (Brain, Speech, Audio, Command).
- `modules/`: Feature extensions (Face ID, Emotion, Memory, Security).
- `skills/`: Plugin directory for custom skills.
- `ui/`: GUI components and 3D Hologram logic.
- `data/`: Persistent storage (SQLite DB, captures, notes).

## 📄 License
MIT License. Created by Arpit Yadav.
