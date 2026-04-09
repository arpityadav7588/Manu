import threading
import time
import psutil
import socket
import config

class SystemMonitor:
    def __init__(self, event_callback, memory_manager):
        self.callback = event_callback
        self.memory = memory_manager
        self._running = False
        self._last_battery = (100, True)
        self._last_internet = True
        self._cpu_high_count = 0
        self._thread = None
        self.interval = config.MONITOR_INTERVAL_SEC

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"[*] SystemMonitor: Background loop active ({self.interval}s interval).")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            print("[*] SystemMonitor: Stopped.")

    def _monitor_loop(self):
        while self._running:
            try:
                self._check_battery()
                self._check_internet()
                self._check_reminders()
                self._check_cpu()
                
                # Sleep for the configured interval (45s)
                time.sleep(self.interval)
            except Exception as e:
                print(f"[!] SystemMonitor Error: {e}")
                time.sleep(10) # Wait a bit before retry if error

    def _check_battery(self):
        battery = psutil.sensors_battery()
        if not battery: return
        
        pct = battery.percent
        plugged = battery.power_plugged
        
        # State change detection (Upgrade 6)
        if (pct, plugged) != self._last_battery:
            if pct <= config.BATTERY_LOW_THRESHOLD and not plugged:
                self.callback("battery_low", pct)
            elif pct >= config.BATTERY_FULL_THRESHOLD and plugged:
                self.callback("battery_full", pct)
            elif plugged and not self._last_battery[1]:
                self.callback("charging", pct)
            elif not plugged and self._last_battery[1]:
                self.callback("unplugged", pct)
            
            self._last_battery = (pct, plugged)

    def _check_internet(self):
        """Task 6: Socket check for connectivity."""
        try:
            # Use 8.8.8.8 (Google DNS) as a reliable target
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            connected = True
        except (OSError, socket.timeout):
            connected = False

        if connected != self._last_internet:
            event = "internet_connected" if connected else "internet_disconnected"
            self.callback(event, None)
            self._last_internet = connected

    def _check_reminders(self):
        """Task 6: Poll for due reminders and emit."""
        due = self.memory.get_due_reminders()
        for reminder in due:
            self.callback("reminder", reminder['title'])
            self.memory.mark_reminder_done(reminder['id'])

    def _check_cpu(self):
        """Task 6: Check for sustained high CPU usage."""
        cpu = psutil.cpu_percent()
        if cpu > 90:
            self._cpu_high_count += 1
            if self._cpu_high_count >= 2:
                self.callback("high_cpu", cpu)
                self._cpu_high_count = 0 # Reset alert
        else:
            self._cpu_high_count = 0
