import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import datetime
import psutil
import config

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
        
        self.root = tk.Tk()
        self.root.title(f"{config.MANU_NAME} Assistant")
        self.root.geometry(f"{config.GUI_WIDTH}x{config.GUI_HEIGHT}")
        self.root.configure(bg=BG)
        
        # Frames
        self.main_frame = tk.Frame(self.root, bg=BG)
        self.lock_frame = tk.Frame(self.root, bg=BG)
        
        self._build_main_ui()
        self._build_lock_screen()
        
    @property
    def is_locked(self):
        return self._is_locked

    def _build_main_ui(self):
        # 1. HEADER
        header = tk.Frame(self.main_frame, bg=BG, pady=15)
        header.pack(fill="x", padx=20)
        
        self.holo_icon = tk.Label(header, text="🔮", font=("Inter", 24), bg=BG, fg=ACCENT)
        self.holo_icon.pack(side="left")
        
        title_lbl = tk.Label(header, text="MANU", font=("Inter", 18, "bold"), bg=BG, fg=ACCENT)
        title_lbl.pack(side="left", padx=15)
        
        self.battery_lbl = tk.Label(header, text="--%", font=("Inter", 10), bg=BG, fg=MUTED)
        self.battery_lbl.pack(side="right")

        # 2. CHAT LOG
        self.chat_log = scrolledtext.ScrolledText(
            self.main_frame, bg=SURFACE, fg=TEXT, font=("Inter", 11),
            padx=15, pady=15, borderwidth=0, highlightthickness=0, state="disabled"
        )
        self.chat_log.pack(fill="both", expand=True, padx=20, pady=10)
        self.chat_log.tag_configure("user", foreground=ACCENT, font=("Inter", 11, "bold"))
        self.chat_log.tag_configure("manu", foreground=SUCCESS, font=("Inter", 11, "bold"))
        self.chat_log.tag_configure("msg", foreground=TEXT, font=("Inter", 11))

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

    def _safe_update_chat(self, sender, message):
        self.chat_log.config(state="normal")
        tag = "manu" if sender.lower() == "manu" else "user"
        prefix = f"{sender}: "
        self.chat_log.insert(tk.END, prefix, tag)
        self.chat_log.insert(tk.END, f"{message}\n\n", "msg")
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
