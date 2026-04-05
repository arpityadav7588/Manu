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
    def __init__(self, on_command_submit, on_login_submit):
        self.on_command_submit = on_command_submit
        self.on_login_submit = on_login_submit
        self.is_locked = True
        
        self.root = tk.Tk()
        self.root.title(f"{config.MANU_NAME} Assistant")
        self.root.geometry(f"{config.GUI_WIDTH}x{config.GUI_HEIGHT}")
        self.root.configure(bg=BG)
        
        self.main_frame = tk.Frame(self.root, bg=BG)
        self.lock_frame = tk.Frame(self.root, bg=BG)
        
        self._build_main_ui()
        self._build_lock_screen()
        
        # Periodic battery update
        self._update_battery_loop()

    def _build_main_ui(self):
        # HEADER
        header = tk.Frame(self.main_frame, bg=BG, pady=20)
        header.pack(fill="x", padx=20)
        
        self.emoji_label = tk.Label(header, text="🙂", font=("Segoe UI Emoji", 36), bg=BG, fg=TEXT)
        self.emoji_label.pack(side="left")
        
        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left", padx=15)
        
        tk.Label(title_frame, text=config.MANU_NAME, font=("Inter", 20, "bold"), bg=BG, fg=ACCENT).pack(anchor="w")
        self.status_label = tk.Label(title_frame, text="🟢 Online & Listening", font=("Inter", 10), bg=BG, fg=MUTED)
        self.status_label.pack(anchor="w")
        
        self.battery_label = tk.Label(header, text="100% 🔋", font=("Inter", 10), bg=BG, fg=MUTED)
        self.battery_label.pack(side="right")
        
        # CHAT LOG
        self.chat_log = scrolledtext.ScrolledText(
            self.main_frame, bg=SURFACE, fg=TEXT, font=("Inter", 11),
            padx=15, pady=15, borderwidth=0, highlightthickness=0
        )
        self.chat_log.pack(fill="both", expand=True, padx=20, pady=10)
        self.chat_log.tag_configure("user", foreground="#818cf8", font=("Inter", 11, "bold"))
        self.chat_log.tag_configure("manu", foreground=SUCCESS, font=("Inter", 11, "bold"))
        self.chat_log.tag_configure("system", foreground=WARNING, font=("Inter", 10, "italic"))
        self.chat_log.tag_configure("body", foreground=TEXT)
        self.chat_log.tag_configure("time", foreground=MUTED, font=("Inter", 8))
        self.chat_log.config(state="disabled")
        
        # QUICK ACTIONS
        actions = tk.Frame(self.main_frame, bg=BG)
        actions.pack(fill="x", padx=20, pady=5)
        
        btns = [("🕐 Time", "what time is it"), ("🔋 Battery", "battery status"), 
                ("😂 Joke", "tell me a joke"), ("📊 System", "system status")]
        for text, cmd in btns:
            btn = tk.Button(
                actions, text=text, bg=SURFACE, fg=TEXT, borderwidth=0, 
                padx=10, pady=5, font=("Inter", 9),
                command=lambda c=cmd: self._handle_quick_action(c)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")
        
        # INPUT BAR
        input_frame = tk.Frame(self.main_frame, bg=BG, pady=20)
        input_frame.pack(fill="x", padx=20)
        
        self.entry = tk.Entry(
            input_frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            font=("Inter", 11), borderwidth=10, relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self._on_submit())
        
        send_btn = tk.Button(
            input_frame, text="Send ➤", bg=ACCENT, fg="white", 
            padx=20, pady=8, font=("Inter", 10, "bold"), borderwidth=0,
            command=self._on_submit
        )
        send_btn.pack(side="right", padx=(10, 0))
        
        # FOOTER
        footer = tk.Label(
            self.main_frame, text=f"Model: {config.LLM_MODEL} | STT: {config.STT_ENGINE}",
            font=("Inter", 8), bg=BG, fg=MUTED, pady=10
        )
        footer.pack(side="bottom")

    def _build_lock_screen(self):
        self.lock_frame.pack_forget()
        
        container = tk.Frame(self.lock_frame, bg=BG)
        container.place(relx=0.5, rely=0.4, anchor="center")
        
        tk.Label(container, text="🔒", font=("Segoe UI Emoji", 72), bg=BG).pack()
        tk.Label(container, text=config.MANU_NAME, font=("Inter", 24, "bold"), bg=BG, fg=ACCENT).pack(pady=(10, 0))
        tk.Label(container, text="Enter password to unlock", font=("Inter", 12), bg=BG, fg=MUTED).pack(pady=(0, 20))
        
        self.pwd_entry = tk.Entry(
            container, show="*", bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            font=("Inter", 14), justify="center", width=20, borderwidth=10, relief="flat"
        )
        self.pwd_entry.pack(pady=10)
        self.pwd_entry.bind("<Return>", lambda e: self._on_login())
        
        login_btn = tk.Button(
            container, text="Login", bg=ACCENT, fg="white", 
            padx=40, pady=10, font=("Inter", 11, "bold"), borderwidth=0,
            command=self._on_login
        )
        login_btn.pack(pady=20)
        
        self.error_label = tk.Label(container, text="", font=("Inter", 10), bg=BG, fg=ERROR)
        self.error_label.pack()

    def _on_submit(self, event=None):
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, tk.END)
            threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()

    def _handle_quick_action(self, cmd):
        threading.Thread(target=self.on_command_submit, args=(cmd,), daemon=True).start()

    def _on_login(self):
        pwd = self.pwd_entry.get()
        self.pwd_entry.delete(0, tk.END)
        result = self.on_login_submit(pwd)
        if result:
            self.show_main_ui()
        else:
            self.error_label.config(text="Incorrect password")
            self.pwd_entry.config(highlightbackground=ERROR, highlightthickness=2)
            self.root.after(2000, lambda: self.error_label.config(text=""))

    def show_lock_screen(self):
        self.is_locked = True
        self.main_frame.pack_forget()
        self.lock_frame.pack(fill="both", expand=True)
        self.pwd_entry.focus_set()

    def show_main_ui(self):
        self.is_locked = False
        self.lock_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.entry.focus_set()
        self.update_status("🟢 Online & Listening")

    def update_chat(self, sender, message):
        """Append styled bubble to chat log (Thread-safe)."""
        self.root.after(0, self._thread_safe_update_chat, sender, message)

    def _thread_safe_update_chat(self, sender, message):
        self.chat_log.config(state="normal")
        now = datetime.datetime.now().strftime("%H:%M")
        
        self.chat_log.insert(tk.END, f" {now} ", "time")
        tag = "manu" if sender.lower() == "manu" else "user"
        self.chat_log.insert(tk.END, f"{sender}: ", tag)
        self.chat_log.insert(tk.END, f"{message}\n\n", "body")
        
        self.chat_log.config(state="disabled")
        self.chat_log.see(tk.END)

    def update_status(self, status_text, mood_emoji=None, battery=None):
        """Update status labels (Thread-safe)."""
        self.root.after(0, self._thread_safe_update_status, status_text, mood_emoji, battery)

    def _thread_safe_update_status(self, status, emoji, battery):
        self.status_label.config(text=status)
        if emoji:
            self.emoji_label.config(text=emoji)
        if battery is not None:
            self.battery_label.config(text=f"{battery}% 🔋")

    def _update_battery_loop(self):
        battery = psutil.sensors_battery()
        if battery:
            self._thread_safe_update_status(self.status_label.cget("text"), None, battery.percent)
        self.root.after(30000, self._update_battery_loop)

    def mainloop(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()
