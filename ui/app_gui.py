import customtkinter as ctk
from PIL import Image
import threading
import time

class ManuGUI(ctk.CTk):
    def __init__(self, on_command_submit, on_login_submit):
        super().__init__()

        self.title("Manu AI Assistant")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.on_command_submit = on_command_submit
        self.on_login_submit = on_login_submit
        self.is_locked = True

        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar (Status)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="MANU AI", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(pady=20)

        self.mood_label = ctk.CTkLabel(self.sidebar, text="😊", font=ctk.CTkFont(size=60))
        self.mood_label.pack(pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Online", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=5)

        self.battery_label = ctk.CTkLabel(self.sidebar, text="Battery: 100%", font=ctk.CTkFont(size=14))
        self.battery_label.pack(pady=5)

        # Main Chat Area
        self.chat_frame = ctk.CTkFrame(self, corner_radius=10)
        self.chat_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(self.chat_frame, font=ctk.CTkFont(size=15))
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_display.configure(state="disabled")

        self.input_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Type a command or speak...")
        self.input_entry.grid(row=1, column=0, padx=(10, 100), pady=10, sticky="ew")
        self.input_entry.bind("<Return>", lambda e: self._submit_text_command())

        self.send_button = ctk.CTkButton(self.chat_frame, text="Send", width=80, command=self._submit_text_command)
        self.send_button.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="e")

        # Security Overlay (Unlocked by default for testing, but we'll show it later)
        self.overlay = None

    def show_lock_screen(self):
        self.is_locked = True
        self.overlay = ctk.CTkToplevel(self)
        self.overlay.geometry("400x300")
        self.overlay.title("Security Lock")
        self.overlay.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(self.overlay, text="Enter Password to Access Manu", font=ctk.CTkFont(size=16))
        lbl.pack(pady=20)
        
        self.pass_entry = ctk.CTkEntry(self.overlay, show="*", placeholder_text="Password...")
        self.pass_entry.pack(pady=10)
        self.pass_entry.bind("<Return>", lambda e: self._submit_login())
        
        btn = ctk.CTkButton(self.overlay, text="Unlock", command=self._submit_login)
        btn.pack(pady=20)

    def _submit_login(self):
        pwd = self.pass_entry.get()
        if self.on_login_submit(pwd):
            self.overlay.destroy()
            self.is_locked = False
            self.update_chat("Manu", "Welcome back! How can I help you today?")
        else:
            self.update_chat("System", "Incorrect password. Security protocol triggered.")

    def _submit_text_command(self):
        text = self.input_entry.get()
        if text:
            self.input_entry.delete(0, 'end')
            self.update_chat("You", text)
            threading.Thread(target=self.on_command_submit, args=(text,), daemon=True).start()

    def update_chat(self, sender, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def update_status(self, mood_emoji=None, battery=None, status=None):
        if mood_emoji:
            self.mood_label.configure(text=mood_emoji)
        if battery:
            self.battery_label.configure(text=f"Battery: {battery}%")
        if status:
            self.status_label.configure(text=f"Status: {status}")

if __name__ == "__main__":
    def dummy_cmd(t): print(f"Command: {t}")
    def dummy_login(p): return p == "manu"
    
    app = ManuGUI(dummy_cmd, dummy_login)
    app.show_lock_screen()
    app.mainloop()
