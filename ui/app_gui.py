import tkinter as tk
from tkinter import scrolledtext
import threading
from modules.security_manager import SecurityManager

BG       = "#0f1117"
SURFACE  = "#1a1d27"
SURFACE2 = "#242736"
ACCENT   = "#6c63ff"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
SUCCESS  = "#34d399"
WARNING  = "#fbbf24"

class ManuGUI:
    def __init__(self, on_command_submit, on_login_submit):
        try:
            self.on_command_submit = on_command_submit
            self.on_login_submit = on_login_submit
            self.is_locked = True
            self._root = tk.Tk()
            self._root.title("Manu — AI Assistant")
            self._root.geometry("500x720")
            self._root.configure(bg=BG)
            self._root.resizable(True, True)
            self._update_queue = []
            self._lock = threading.Lock()
            self._build_main_ui()
            self._root.after(300, self._drain_queue)
        except Exception as e:
            print(f"GUI init error: {e}")

    def _build_main_ui(self):
        try:
            header_frame = tk.Frame(self._root, bg=SURFACE, pady=10)
            header_frame.pack(fill=tk.X)
            
            self._emotion_lbl = tk.Label(header_frame, text="🤖", font=("Segoe UI", 32), bg=SURFACE)
            self._emotion_lbl.pack(side=tk.LEFT, padx=10)
            
            title_frame = tk.Frame(header_frame, bg=SURFACE)
            title_frame.pack(side=tk.LEFT, padx=10)
            tk.Label(title_frame, text="Manu", fg=ACCENT, bg=SURFACE, font=("Segoe UI", 18, "bold")).pack(anchor=tk.W)
            self._status_lbl = tk.Label(title_frame, text="Initializing...", fg=MUTED, bg=SURFACE, font=("Segoe UI", 10))
            self._status_lbl.pack(anchor=tk.W)
            
            self._battery_lbl = tk.Label(header_frame, text="🔋", fg=TEXT, bg=SURFACE, font=("Segoe UI", 14))
            self._battery_lbl.pack(side=tk.RIGHT, padx=20)
            
            self.chat_log = scrolledtext.ScrolledText(self._root, bg=SURFACE, fg=TEXT, font=("Segoe UI", 11), relief=tk.FLAT, state=tk.DISABLED)
            self.chat_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.chat_log.tag_config("user", foreground=ACCENT, font=("Segoe UI", 11, "bold"))
            self.chat_log.tag_config("manu", foreground=SUCCESS, font=("Segoe UI", 11, "bold"))
            self.chat_log.tag_config("system", foreground=WARNING, font=("Segoe UI", 9, "italic"))
            self.chat_log.tag_config("body", foreground=TEXT)
            
            btns_frame = tk.Frame(self._root, bg=BG)
            btns_frame.pack(fill=tk.X, padx=10)
            
            def make_btn(text, cmd):
                b = tk.Button(btns_frame, text=text, bg=SURFACE2, fg=TEXT, relief=tk.FLAT, cursor="hand2", command=lambda: self._trigger_cmd(cmd))
                b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
                
            make_btn("🕐 Time", "what time is it")
            make_btn("🔋 Battery", "check battery status")
            make_btn("😂 Joke", "tell me a joke")
            make_btn("💻 System", "system info")
            
            input_frame = tk.Frame(self._root, bg=SURFACE, pady=10, padx=10)
            input_frame.pack(fill=tk.X, side=tk.BOTTOM)
            
            footer_lbl = tk.Label(self._root, text="Manu v1.0  •  Gemma 3 4B  •  Whisper STT", fg=MUTED, bg=SURFACE)
            footer_lbl.pack(side=tk.BOTTOM, fill=tk.X)
            
            self.entry = tk.Entry(input_frame, bg=SURFACE, fg=TEXT, font=("Segoe UI", 12), relief=tk.FLAT, insertbackground=TEXT)
            self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entry.insert(0, "Type a command...")
            
            def on_focus_in(e):
                if self.entry.get() == "Type a command...":
                    self.entry.delete(0, tk.END)
            def on_focus_out(e):
                if not self.entry.get():
                    self.entry.insert(0, "Type a command...")
                    
            self.entry.bind("<FocusIn>", on_focus_in)
            self.entry.bind("<FocusOut>", on_focus_out)
            self.entry.bind("<Return>", lambda e: self._on_send())
            
            send_btn = tk.Button(input_frame, text="Send ➤", bg=ACCENT, fg="white", relief=tk.FLAT, command=self._on_send)
            send_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
        except Exception as e:
            print(f"Build UI error: {e}")

    def _trigger_cmd(self, text):
        try:
            self.update_chat("You", text)
            threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()
        except:
            pass

    def show_lock_screen(self):
        try:
            self.lock_win = tk.Toplevel(self._root)
            self.lock_win.configure(bg=BG)
            self.lock_win.title("Manu is Locked")
            self.lock_win.geometry("400x300")
            self.lock_win.transient(self._root)
            self.lock_win.grab_set()
            
            tk.Label(self.lock_win, text="🔒", font=("Segoe UI", 48), bg=BG, fg=TEXT).pack(pady=20)
            
            sm = SecurityManager()
            
            if not sm.has_password():
                tk.Label(self.lock_win, text="Set Password", bg=BG, fg=TEXT).pack()
                e1 = tk.Entry(self.lock_win, show="•", font=("Segoe UI", 12))
                e1.pack(pady=5)
                e2 = tk.Entry(self.lock_win, show="•", font=("Segoe UI", 12))
                e2.pack(pady=5)
                def set_pw():
                    if e1.get() and e1.get() == e2.get():
                        sm.set_password(e1.get())
                        self.on_login_submit(e1.get())
                        self.is_locked = False
                        self.lock_win.destroy()
                        self.add_system_message("Session unlocked. Welcome back!")
                tk.Button(self.lock_win, text="Set Password", bg=ACCENT, fg="white", command=set_pw).pack()
            else:
                tk.Label(self.lock_win, text="Enter Password", bg=BG, fg=TEXT).pack()
                pw_entry = tk.Entry(self.lock_win, show="•", font=("Segoe UI", 12))
                pw_entry.pack(pady=10)
                def unlock():
                    if pw_entry.get():
                        if sm.verify_password(pw_entry.get()):
                            self.on_login_submit(pw_entry.get())
                            self.is_locked = False
                            self.lock_win.destroy()
                            self.add_system_message("Session unlocked. Welcome back!")
                        else:
                            self._shake_window(self.lock_win)
                tk.Button(self.lock_win, text="Unlock", bg=ACCENT, fg="white", command=unlock).pack()
        except Exception as e:
            pass

    def _shake_window(self, win):
        try:
            x = win.winfo_x()
            y = win.winfo_y()
            for i in range(3):
                self._root.after(i * 100, lambda: win.geometry(f"+{x-10}+{y}"))
                self._root.after(i * 100 + 50, lambda: win.geometry(f"+{x+10}+{y}"))
            self._root.after(300, lambda: win.geometry(f"+{x}+{y}"))
        except:
            pass

    def update_status(self, mood_emoji: str = None, battery: int = None, text: str = None):
        try:
            with self._lock:
                self._update_queue.append(("status", mood_emoji, battery, text))
        except:
            pass

    def update_chat(self, sender: str, message: str):
        try:
            with self._lock:
                self._update_queue.append(("chat", sender, message))
        except:
            pass

    def add_system_message(self, message: str):
        try:
            with self._lock:
                self._update_queue.append(("system", message))
        except:
            pass

    def _drain_queue(self):
        try:
            with self._lock:
                items = self._update_queue[:]
                self._update_queue.clear()
            
            for item in items:
                if item[0] == "status":
                    _, emoji, bat, txt = item
                    if emoji: self._emotion_lbl.config(text=emoji)
                    if bat is not None: self._battery_lbl.config(text=f"🔋 {bat}%")
                    if txt: self._status_lbl.config(text=txt)
                elif item[0] == "chat":
                    _, sender, msg = item
                    self.chat_log.config(state=tk.NORMAL)
                    tag = "user" if sender == "You" else "manu"
                    self.chat_log.insert(tk.END, f"{sender}: ", tag)
                    self.chat_log.insert(tk.END, f"{msg}\n", "body")
                    self.chat_log.see(tk.END)
                    self.chat_log.config(state=tk.DISABLED)
                elif item[0] == "system":
                    _, msg = item
                    self.chat_log.config(state=tk.NORMAL)
                    self.chat_log.insert(tk.END, f"{msg}\n", "system")
                    self.chat_log.see(tk.END)
                    self.chat_log.config(state=tk.DISABLED)
                    
            self._root.after(300, self._drain_queue)
        except Exception as e:
            pass

    def _on_send(self):
        try:
            text = self.entry.get().strip()
            if not text or text == "Type a command...":
                return
            self.entry.delete(0, tk.END)
            self.update_chat("You", text)
            threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()
        except:
            pass

    def mainloop(self):
        try:
            self._root.mainloop()
        except:
            pass
