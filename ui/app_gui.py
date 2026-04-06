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
        self.root.geometry(f"1100x650") # Fixed size for layout
        self.root.configure(bg=BG)
        
        # Frames
        self.main_container = tk.Frame(self.root, bg=BG)
        self.main_frame = tk.Frame(self.main_container, bg=BG) # Main command area
        
        self.left_panel = tk.Frame(self.main_container, bg=BG)
        self.left_panel.pack(side="left", fill="both", expand=True)
        
        self.right_panel = tk.Frame(self.main_container, bg=SURFACE, width=320)
        self.right_panel.pack(side="right", fill="both")
        
        self.lock_frame = tk.Frame(self.root, bg=BG)
        
        self._build_main_ui()
        self._build_hologram_panel()
        self._build_lock_screen()
        self._setup_tray()
        self._start_status_loop()
        
    @property
    def is_locked(self):
        return self._is_locked

    def _build_main_ui(self):
        # 1. HEADER / STATUS BAR (Task 6b)
        self.status_bar = tk.Frame(self.left_panel, bg=SURFACE, height=35)
        self.status_bar.pack(fill="x", side="top")
        
        self.st_online = tk.Label(self.status_bar, text="🟢 ONLINE", fg=SUCCESS, bg=SURFACE, font=("Inter", 9, "bold"))
        self.st_online.pack(side="left", padx=15)
        
        self.st_mic = tk.Label(self.status_bar, text="🎤 Idle", fg=MUTED, bg=SURFACE, font=("Inter", 9))
        self.st_mic.pack(side="left", padx=15)
        
        self.st_time = tk.Label(self.status_bar, text="--:--", fg=TEXT, bg=SURFACE, font=("Inter", 9))
        self.st_time.pack(side="right", padx=15)
        
        self.st_batt = tk.Label(self.status_bar, text="🔋 100%", fg=SUCCESS, bg=SURFACE, font=("Inter", 9))
        self.st_batt.pack(side="right", padx=15)
        
        self.st_llm = tk.Label(self.status_bar, text=f"🤖 GPT: {config.LLM_MODEL}", fg=ACCENT, bg=SURFACE, font=("Inter", 9))
        self.st_llm.pack(side="right", padx=15)

        # 2. CHAT AREA (Task 6d)
        content_frame = tk.Frame(self.left_panel, bg=BG)
        content_frame.pack(fill="both", expand=True, padx=20)
        
        self.chat_log = scrolledtext.ScrolledText(
            content_frame, bg=BG, fg=TEXT, font=("Inter", 11),
            padx=10, pady=10, borderwidth=0, highlightthickness=0, state="disabled"
        )
        self.chat_log.pack(fill="both", expand=True, pady=(10, 0))
        
        # Tag styling for chat bubbles (Task 6d)
        self.chat_log.tag_configure("user_msg", foreground="white", background="#2563eb", spacing1=10, spacing3=10, lmargin1=150, lmargin2=150, rmargin=20)
        self.chat_log.tag_configure("manu_msg", foreground=TEXT, background=SURFACE, spacing1=10, spacing3=10, lmargin1=20, lmargin2=20, rmargin=150)
        self.chat_log.tag_configure("timestamp", foreground=MUTED, font=("Inter", 8))

        # 3. QUICK ACTIONS (Task 6c)
        actions = tk.Frame(self.left_panel, bg=BG)
        actions.pack(fill="x", padx=20, pady=10)
        
        btns = [
            ("🕐 Time", "what time is it"), 
            ("🔋 Battery", "system status"), 
            ("😂 Joke", "tell me a joke"), 
            ("📝 Note", "take a note "), 
            ("🔍 Search", "google "), 
            ("🌅 Briefing", "morning briefing")
        ]
        for text, cmd in btns:
            btn = tk.Button(
                actions, text=text, bg=SURFACE, fg=TEXT, borderwidth=0, 
                padx=10, pady=6, font=("Inter", 9), cursor="hand2",
                command=lambda c=cmd: self._quick_action(c)
            )
            btn.pack(side="left", padx=4, expand=True, fill="x")

        # 4. INPUT BAR
        input_frame = tk.Frame(self.left_panel, bg=SURFACE, pady=8)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.entry = tk.Entry(
            input_frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            font=("Inter", 12), borderwidth=0, relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=15)
        self.entry.bind("<Return>", lambda e: self._on_submit())
        
        send_btn = tk.Button(
            input_frame, text="SEND ➤", bg=ACCENT, fg="white", 
            padx=20, borderwidth=0, font=("Inter", 10, "bold"), cursor="hand2",
            command=self._on_submit
        )
        send_btn.pack(side="right", padx=5)

    def _quick_action(self, cmd):
        if cmd.endswith(" "):
            self.entry.delete(0, tk.END)
            self.entry.insert(0, cmd)
            self.entry.focus_set()
        else:
            self.update_chat("You", cmd)
            threading.Thread(target=self.on_command_submit, args=(cmd,), daemon=True).start()

    def _build_lock_screen(self):
        container = tk.Frame(self.lock_frame, bg=BG)
        container.place(relx=0.5, rely=0.4, anchor="center")
        
        tk.Label(container, text="👤", font=("Inter", 72), bg=BG, fg=ACCENT).pack()
        tk.Label(container, text="MANU SECURE LOGIN", font=("Inter", 16, "bold"), bg=BG, fg=TEXT).pack(pady=20)
        
        self.pwd_entry = tk.Entry(container, show="*", bg=SURFACE, fg=TEXT, font=("Inter", 16), justify="center", width=20, borderwidth=0)
        self.pwd_entry.pack(pady=10, ipady=8)
        self.pwd_entry.bind("<Return>", lambda e: self._on_login())
        
        tk.Button(container, text="UNLOCK SYSTEM", bg=ACCENT, fg="white", font=("Inter", 11, "bold"), 
                  command=self._on_login, padx=40, pady=10, borderwidth=0, cursor="hand2").pack(pady=20)

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
        self.main_container.pack_forget()
        self.lock_frame.pack(fill="both", expand=True)

    def show_main_ui(self):
        self._is_locked = False
        self.lock_frame.pack_forget()
        self.main_container.pack(fill="both", expand=True)

    def update_chat(self, sender, message):
        self.root.after(0, self._safe_update_chat, sender, message)

    def _build_hologram_panel(self):
        """Embed the HologramCanvas in the right panel."""
        tk.Label(self.right_panel, text="SYSTEM AVATAR", font=("Inter", 10, "bold"), bg=SURFACE, fg=ACCENT).pack(pady=30)
        self.holo_viz = HologramCanvas(self.right_panel, width=300, height=350)
        self.holo_viz.canvas.pack(pady=10)
        
        self.mood_lbl = tk.Label(self.right_panel, text="STATUS: NEUTRAL", font=("Inter", 9, "bold"), bg=SURFACE, fg=MUTED)
        self.mood_lbl.pack(pady=20)
        
        # System Overview Stats
        stats_frame = tk.Frame(self.right_panel, bg=SURFACE)
        stats_frame.pack(fill="x", padx=30, pady=20)
        
        self.cpu_lbl = tk.Label(stats_frame, text="CPU: --%", bg=SURFACE, fg=TEXT, font=("Inter", 9))
        self.cpu_lbl.pack(anchor="w", pady=2)
        self.mem_lbl = tk.Label(stats_frame, text="RAM: --%", bg=SURFACE, fg=TEXT, font=("Inter", 9))
        self.mem_lbl.pack(anchor="w", pady=2)

    def _setup_tray(self):
        if not HAS_TRAY: return
        
        def _on_show(icon, item):
            self.root.after(0, self.root.deiconify)
            
        def _on_exit(icon, item):
            icon.stop()
            self.root.after(0, self.destroy)

        try:
            # Create a simple colored square as icon if none exists
            img = Image.new('RGB', (64, 64), color=(108, 99, 255))
            menu = pystray.Menu(pystray.item('Open Manu', _on_show), pystray.item('Exit', _on_exit))
            self.tray = pystray.Icon("Manu", img, "Manu Assistant", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except: pass

    def _safe_update_chat(self, sender, message):
        self.chat_log.config(state="normal")
        is_manu = (sender.lower() == "manu")
        tag = "manu_msg" if is_manu else "user_msg"
        
        ts = datetime.datetime.now().strftime("%H:%M")
        prefix = "🤖 " if is_manu else ""
        
        self.chat_log.insert(tk.END, f"\n {prefix}{sender}  ", tag)
        self.chat_log.insert(tk.END, f"{ts}\n", "timestamp")
        self.chat_log.insert(tk.END, f" {message} \n\n", tag)
        
        self.chat_log.config(state="disabled")
        self.chat_log.see(tk.END)

    def _start_status_loop(self):
        def _update():
            now = datetime.datetime.now().strftime("%H:%M")
            self.st_time.config(text=f"⏱ {now}")
            
            # System stats
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            batt = psutil.sensors_battery()
            
            self.cpu_lbl.config(text=f"CPU usage: {cpu}%")
            self.mem_lbl.config(text=f"RAM usage: {mem}%")
            
            if batt:
                self.st_batt.config(text=f"🔋 {batt.percent}%", fg=SUCCESS if batt.percent > 20 else ERROR)
                
            self.root.after(5000, _update)
        _update()

    def update_listening(self, active):
        color = SUCCESS if active else MUTED
        text = "🎤 Listening" if active else "🎤 Idle"
        self.st_mic.config(text=text, fg=color)
        if self.holo_viz:
            self.holo_viz.set_emotion("listening" if active else "neutral")

    def update_hologram(self, emotion):
        if self.holo_viz:
            self.holo_viz.set_emotion(emotion)
        self.mood_lbl.config(text=f"STATUS: {emotion.upper()}")

    def mainloop(self):
        self.root.mainloop()

    def destroy(self):
        if self.tray: self.tray.stop()
        self.root.destroy()
