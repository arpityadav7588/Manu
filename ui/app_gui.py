import tkinter as tk
from tkinter import scrolledtext
import threading
import datetime
import psutil
import config

# Dark theme colors (Upgrade 8)
BG = "#0f1117"
SURFACE = "#1a1d27"
ACCENT = "#6c63ff"
ACCENT2 = "#22d3ee"
TEXT = "#e2e8f0"
MUTED = "#64748b"
SUCCESS = "#34d399"

class ManuGUI:
    def __init__(self, on_command_submit, on_login_submit):
        self.on_command_submit = on_command_submit
        self.on_login_submit = on_login_submit
        self.root = tk.Tk()
        self.root.title("Manu — AI Assistant")
        self.root.geometry("480x700")
        self.root.minsize(400, 500)
        self.root.configure(bg=BG)
        
        self.is_locked = True
        
        # UI Components
        self.header = None
        self.chat_area = None
        self.input_field = None
        self.status_lbl = None
        self.emoji_lbl = None
        self.batt_lbl = None
        
        self._build_ui()

    def _build_ui(self):
        # 1. HEADER (Upgrade 8)
        self.header = tk.Frame(self.root, bg=BG, pady=15)
        self.header.pack(fill="x", padx=20)
        
        # Emoji on left
        self.emoji_lbl = tk.Label(self.header, text="🙂", font=("Inter", 36), bg=BG, fg=TEXT)
        self.emoji_lbl.pack(side="left", padx=(0, 15))
        
        # Title and Status in middle
        mid_frame = tk.Frame(self.header, bg=BG)
        mid_frame.pack(side="left", fill="y")
        
        tk.Label(mid_frame, text="Manu", font=("Inter", 18, "bold"), fg=ACCENT, bg=BG).pack(anchor="w")
        self.status_lbl = tk.Label(mid_frame, text="System Ready", font=("Inter", 9), fg=MUTED, bg=BG)
        self.status_lbl.pack(anchor="w")
        
        # Battery on right
        self.batt_lbl = tk.Label(self.header, text="🔋 100%", font=("Inter", 10), fg=SUCCESS, bg=BG)
        self.batt_lbl.pack(side="right", anchor="n")

        # 2. CHAT LOG (Upgrade 8)
        self.chat_area = scrolledtext.ScrolledText(
            self.root, bg=SURFACE, fg=TEXT, font=("Inter", 11),
            padx=10, pady=10, borderwidth=0, highlightthickness=0
        )
        self.chat_area.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tag styling
        self.chat_area.tag_configure("user", foreground=ACCENT2, font=("Inter", 11, "bold"))
        self.chat_area.tag_configure("manu", foreground=SUCCESS, font=("Inter", 11, "bold"))
        self.chat_area.tag_configure("system", foreground=MUTED, font=("Inter", 10, "italic"))
        self.chat_area.tag_configure("body", foreground=TEXT, spacing3=10)

        # 3. QUICK ACTIONS (Upgrade 8)
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(fill="x", padx=20, pady=5)
        
        actions = [("🕐 Time", "what time is it"), ("🔋 Battery", "charge level"), ("😂 Joke", "tell me a joke"), ("📊 System", "system info")]
        for label, cmd in actions:
            btn = tk.Button(
                btn_frame, text=label, bg=SURFACE, fg=TEXT, font=("Inter", 9),
                padx=8, pady=4, borderwidth=0, cursor="hand2",
                command=lambda c=cmd: self._send_internal(c)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")

        # 4. INPUT BAR (Upgrade 8)
        input_frame = tk.Frame(self.root, bg=SURFACE, pady=5)
        input_frame.pack(fill="x", side="bottom", padx=20, pady=(10, 20))
        
        self.input_field = tk.Entry(
            input_frame, bg=SURFACE, fg=TEXT, font=("Inter", 12),
            insertbackground=TEXT, borderwidth=0, relief="flat"
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=10)
        self.input_field.insert(0, "Type a command or question...")
        self.input_field.bind("<FocusIn>", self._clear_placeholder)
        self.input_field.bind("<Return>", lambda e: self._on_submit())
        
        send_btn = tk.Button(
            input_frame, text="SEND", font=("Inter", 10, "bold"),
            bg=ACCENT, fg="white", borderwidth=0, padx=15, cursor="hand2",
            command=self._on_submit
        )
        send_btn.pack(side="right", padx=5)

        # 5. FOOTER (Upgrade 8)
        footer = tk.Label(
            self.root, text=f"Manu v1.0 • LLM: {config.LLM_MODEL} • STT: whisper",
            font=("Inter", 7), fg=MUTED, bg=BG
        )
        footer.pack(side="bottom", pady=(0, 5))

    def _send_internal(self, text):
        self.add_message("Arpit", text)
        threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()

    def _on_submit(self):
        text = self.input_field.get().strip()
        if text and text != "Type a command or question...":
            self.input_field.delete(0, tk.END)
            self.add_message("Arpit", text)
            threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()

    def _clear_placeholder(self, event):
        if self.input_field.get() == "Type a command or question...":
            self.input_field.delete(0, tk.END)

    # Thread-safe methods (Upgrade 8)
    def update_emotion(self, emoji):
        self.root.after(0, lambda: self.emoji_lbl.config(text=emoji))

    def update_status(self, text):
        self.root.after(0, lambda: self.status_lbl.config(text=text))

    def add_message(self, sender, text):
        self.root.after(0, self._safe_add_msg, sender, text)

    def add_system_message(self, text):
        self.root.after(0, self._safe_add_sys_msg, text)

    def _safe_add_msg(self, sender, text):
        self.chat_area.config(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M")
        is_user = (sender.lower() == "arpit" or sender.lower() == "you")
        tag = "user" if is_user else "manu"
        
        self.chat_area.insert(tk.END, f"[{sender}] {ts}\n", tag)
        self.chat_area.insert(tk.END, f"{text}\n", "body")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def _safe_add_sys_msg(self, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"[*] {text}\n", "system")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def show_lock_screen(self):
        self.is_locked = True
        # Simplified: clear screen or show overlay
        self.chat_area.config(state="normal")
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.insert(tk.END, "\n\n\n\n\n     [ SYSTEM LOCKED ]\n     Please provide credentials in console.", "user")
        self.chat_area.config(state="disabled")

    def show_main_ui(self):
        self.is_locked = False
        self.chat_area.config(state="normal")
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state="disabled")
        self.add_system_message("Session Started.")

    def update_battery_gui(self, pct, state_color):
        self.root.after(0, lambda: self.batt_lbl.config(text=f"🔋 {pct}%", fg=state_color))

    def mainloop(self):
        self.root.mainloop()
