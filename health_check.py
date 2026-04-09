import sys

def run_health_check():
    checks_passed = 0
    total_checks = 6

    # 1. Python version
    try:
        ver = sys.version_info
        if ver.major >= 3 and ver.minor >= 10:
            print("✅ Python version >= 3.10")
            checks_passed += 1
        else:
            print("❌ Python version < 3.10")
    except Exception as e:
        print(f"❌ Python version check failed: {e}")

    # 2. Imports
    modules_to_check = [
        "pyttsx3", "speech_recognition", "faster_whisper", "soundfile",
        "psutil", "requests", "sqlite3", "tkinter", "cv2", "pyperclip"
    ]
    missing = []
    print("Checking imports...")
    for mod in modules_to_check:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
            print(f"❌ {mod} MISSING")
    
    if not missing:
        print("✅ All imports successful")
        checks_passed += 1
    else:
        print("⚠ Some imports missing.")

    # 3. Ollama connectivity & 4. Gemma4 model
    try:
        import requests
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        if res.status_code == 200:
            print("✅ Ollama running")
            checks_passed += 1
            data = res.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            if any("gemma4" in m for m in models):
                print("✅ Gemma4 model found")
                checks_passed += 1
            else:
                print("⚠ Ollama running but gemma4 not found — run: ollama pull gemma4")
        else:
            print("❌ Ollama check failed: Not 200 OK")
    except ImportError:
        print("❌ Cannot check Ollama: requests missing")
    except Exception as e:
        print("❌ Ollama connectivity failed")

    # 5. Microphone
    try:
        import speech_recognition as sr
        with sr.Microphone() as source:
            pass
        print("✅ Microphone works")
        checks_passed += 1
    except ImportError:
        print("❌ Cannot check microphone: speech_recognition missing")
    except Exception as e:
        print(f"❌ Microphone check failed: {e}")

    # 6. Data dir
    try:
        from pathlib import Path
        import os
        d = Path("./data")
        d.mkdir(parents=True, exist_ok=True)
        test_file = d / ".test_write"
        test_file.write_text("ok")
        test_file.unlink()
        print("✅ ./data/ directory writable")
        checks_passed += 1
    except Exception as e:
        print(f"❌ ./data/ directory check failed: {e}")

    print(f"\n{checks_passed}/{total_checks} checks passed")
    if checks_passed == total_checks:
        print("🚀 Manu is ready to launch! Run: python main.py")

if __name__ == "__main__":
    run_health_check()
