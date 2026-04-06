import subprocess
import platform
import logging
import base64
import io

class ScreenReader:
    """Reads active window title and optionally describes screen content."""
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.log = logging.getLogger("Manu.ScreenReader")

    def get_active_window_title(self) -> str:
        """Return the title of the currently focused window."""
        os_name = platform.system()
        try:
            if os_name == "Windows":
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                return buf.value or "Unknown window"
            elif os_name == "Darwin":
                result = subprocess.run(
                    ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
                    capture_output=True, text=True, timeout=3
                )
                return result.stdout.strip()
            else: # Linux
                result = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=3)
                return result.stdout.strip()
        except: return "Unknown"

    def describe_screen(self) -> str:
        """Take screenshot and return LLM description."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img_small = img.resize((800, 450))
            buf = io.BytesIO()
            img_small.save(buf, format="JPEG", quality=50)
            b64 = base64.b64encode(buf.getvalue()).decode()
            
            prompt = "In 2-3 sentences, describe what the user is currently doing based on this screenshot."
            # vision model support if LLM_MODEL supports it, else text prompt
            return self.llm.chat(prompt)
        except ImportError:
            title = self.get_active_window_title()
            return f"You're currently in {title}."
        except Exception as e:
            return f"Screen error: {e}"
