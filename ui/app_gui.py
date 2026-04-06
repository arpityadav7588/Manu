import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import datetime
import psutil
import config
from ui.hologram import HologramCanvas
try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# Dark theme constants
BG = "#0f1117"
SURFACE = "#1a1d27"
ACCENT = "#6c63ff"
TEXT = "#e2e8f0"
MUTED = "#64748b"
SUCCESS = "#34d399"
WARNING = "#fbbf24"
ERROR = "#f87171"

class ManuGUI:
    def __init__(self, on_command_submit, on_login_submit, hologram=None):
        self.on_command_submit = on_command_submit
        self.on_login_submit = on_login_submit
        self.hologram = hologram
        self._is_locked = True
        self.tray = None
        
        self.root = tk.Tk()
        self.root.title(f"{config.MANU_NAME} Assistant")
        self.root.geometry(f"{config.GUI_WIDTH + 300}x{config.GUI_HEIGHT}") # Widened for Hologram
        self.root.configure(bg=BG)
        
        # Frames
        self.main_container = tk.Frame(self.root, bg=BG)
        self.main_container.pack(fill="both", expand=True)
        
        self.left_panel = tk.Frame(self.main_container, bg=BG)
        self.left_panel.pack(side="left", fill="both", expand=True)
        
        self.right_panel = tk.Frame(self.main_container, bg=SURFACE, width=300)
        self.right_panel.pack(side="right", fill="both")
        
        self.lock_frame = tk.Frame(self.root, bg=BG)
        
        self._build_main_ui()
        self._build_hologram_panel()
        self._build_lock_screen()
        self._setup_tray()
        
    @property
    def is_locked(self):
        return self._is_locked

    def _build_main_ui(self):
        # 1. HEADER / STATUS BAR (Task 6)
        self.status_bar = tk.Frame(self.left_panel, bg=SURFACE, height=30)
        self.status_bar.pack(fill="x", side="top")
        
        self.st_online = tk.Label(self.status_bar, text="● Online", fg=SUCCESS, bg=SURFACE, font=("Inter", 8))
        self.st_online.pack(side="left", padx=10)
        
        self.st_mic = tk.Label(self.status_bar, text="🎤 Idle", fg=MUTED, bg=SURFACE, font=("Inter", 8))
        self.st_mic.pack(side="left", padx=10)
        
        self.st_time = tk.Label(self.status_bar, text="--:--", fg=TEXT, bg=SURFACE, font=("Inter", 8))
        self.st_time.pack(side="right", padx=10)
        
        self.st_batt = tk.Label(self.status_bar, text="100%", fg=SUCCESS, bg=SURFACE, font=("Inter", 8))
        self.st_batt.pack(side="right", padx=10)

        # 2. CHAT AREA
        content_frame = tk.Frame(self.left_panel, bg=BG)
        content_frame.pack(fill="both", expand=True, padx=20)
        
        self.chat_log = scrolledtext.ScrolledText(
            content_frame, bg=BG, fg=TEXT, font=("Inter", 11),
            padx=10, pady=10, borderwidth=0, highlightthickness=0, state="disabled"
        )
        self.chat_log.pack(fill="both", expand=True, pady=(10, 0))
        
        # Tag styling for chat bubbles (Task 6)
        self.chat_log.tag_configure("user_msg", foreground=BG, background=ACCENT, spacing1=5, spacing3=5, lmargin1=100, lmargin2=100, rmargin=10)
        self.chat_log.tag_configure("manu_msg", foreground=TEXT, background=SURFACE, spacing1=5, spacing3=5, lmargin1=10, lmargin2=10, rmargin=100)

        # 3. QUICK ACTIONS
        actions = tk.Frame(self.main_frame, bg=BG)
        actions.pack(fill="x", padx=20, pady=10)
        
        btns = [("🕐 Time", "what time is it"), ("🔋 Battery", "system info"), 
                ("😂 Joke", "tell me a joke"), ("📊 System", "how's the cpu"), ("🎯 Remind", "list reminders")]
        for text, cmd in btns:
            btn = tk.Button(
                actions, text=text, bg=SURFACE, fg=TEXT, borderwidth=0, 
                padx=8, pady=4, font=("Inter", 8),
                command=lambda c=cmd: threading.Thread(target=self.on_command_submit, args=(c,), daemon=True).start()
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")

        # 4. INPUT BAR
        input_frame = tk.Frame(self.main_frame, bg=SURFACE, pady=5)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.entry = tk.Entry(
            input_frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            font=("Inter", 11), borderwidth=0, relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=10)
        self.entry.bind("<Return>", lambda e: self._on_submit())
        
        send_btn = tk.Button(
            input_frame, text="Send ➤", bg=ACCENT, fg="white", 
            padx=15, borderwidth=0, font=("Inter", 10, "bold"),
            command=self._on_submit
        )
        send_btn.pack(side="right")

        # 5. FOOTER
        self.footer = tk.Label(
            self.main_frame, text="LLM: llama3.2 | STT: Whisper | Hologram: Active", 
            bg=BG, fg=MUTED, font=("Inter", 8)
        )
        self.footer.pack(fill="x", pady=5)

    def _build_lock_screen(self):
        container = tk.Frame(self.lock_frame, bg=BG)
        container.place(relx=0.5, rely=0.4, anchor="center")
        
        tk.Label(container, text="🔒", font=("Inter", 64), bg=BG).pack()
        tk.Label(container, text="Enter Password", font=("Inter", 14), bg=BG, fg=TEXT).pack(pady=10)
        
        self.pwd_entry = tk.Entry(container, show="*", bg=SURFACE, fg=TEXT, font=("Inter", 14), justify="center")
        self.pwd_entry.pack(pady=10)
        self.pwd_entry.bind("<Return>", lambda e: self._on_login())
        
        tk.Button(container, text="Login", bg=ACCENT, fg="white", command=self._on_login, padx=30).pack(pady=10)

    def _on_submit(self):
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, tk.END)
            self.update_chat("You", text)
            threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()

    def _on_login(self):
        pwd = self.pwd_entry.get()
        self.pwd_entry.delete(0, tk.END)
        if self.on_login_submit(pwd):
            self.show_main_ui()

    def show_lock_screen(self):
        self._is_locked = True
        self.main_frame.pack_forget()
        self.lock_frame.pack(fill="both", expand=True)

    def show_main_ui(self):
        self._is_locked = False
        self.lock_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def update_chat(self, sender, message):
        self.root.after(0, self._safe_update_chat, sender, message)

    def _build_hologram_panel(self):
        """Embed the HologramCanvas in the right panel."""
        tk.Label(self.right_panel, text="HYPERVISUAL", font=("Inter", 10, "bold"), bg=SURFACE, fg=ACCENT).pack(pady=20)
        self.holo_viz = HologramCanvas(self.right_panel, width=280, height=280)
        self.holo_viz.canvas.pack(pady=10)
        
        # Add tiny mood label
        self.mood_lbl = tk.Label(self.right_panel, text="MOOD: NEUTRAL", font=("Inter", 8), bg=SURFACE, fg=MUTED)
        self.mood_lbl.pack(pady=10)

    def _setup_tray(self):
        if not HAS_TRAY: return
        
        def _on_show(icon, item):
            self.root.deiconify()
            
        def _on_exit(icon, item):
            icon.stop()
            self.destroy()

        menu = pystray.Menu(pystray.item('Show', _on_show), pystray.item('Exit', _on_exit))
        # icon_img = Image.open(...) # User will need an icon.png
        # self.tray = pystray.Icon("Manu", icon_img, "Manu Assistant", menu)
        # threading.Thread(target=self.tray.run, daemon=True).start()

    def _safe_update_chat(self, sender, message):
        self.chat_log.config(state="normal")
        is_manu = (sender.lower() == "manu")
        tag = "manu_msg" if is_manu else "user_msg"
        
        self.chat_log.insert(tk.END, f"\n {sender} \n", tag)
        self.chat_log.insert(tk.END, f" {message} \n\n", tag)
        
        self.chat_log.config(state="disabled")
        self.chat_log.see(tk.END)

    def update_status(self, mood_emoji, battery=None):
        if battery:
            self.battery_lbl.config(text=f"{battery}% 🔋")
        if self.hologram:
            # Note: mood_emoji is expected to be an emotion string here
            # for the hologram logic. In main.py we'll pass the emotion name.
            pass

    def update_hologram(self, emotion):
        if self.hologram:
            self.hologram.set_emotion(emotion)

    def mainloop(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()
