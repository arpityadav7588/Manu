import threading
import time
import psutil
import socket
import config

class SystemMonitor:
    def __init__(self, callback):
        self.callback = callback
        self._running = False
        self._last_battery = (100, True)
        self._last_internet = True
        self._thread = None
        self._memory = None # Passed on start

    def start(self, memory=None):
        if self._running: return
        self._memory = memory
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("🔍 System Monitor: Started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            print("System Monitor: Stopped.")

    def _monitor_loop(self):
        while self._running:
            self._check_battery()
            self._check_internet()
            if self._memory:
                self._check_reminders(self._memory)
            
            time.sleep(config.MONITOR_INTERVAL_SEC)

    def _check_battery(self):
        battery = psutil.sensors_battery()
        if not battery: return
        
        pct = battery.percent
        plugged = battery.power_plugged
        
        # State change detection
        if (pct, plugged) != self._last_battery:
            # Low battery alert
            if pct <= config.BATTERY_LOW_THRESHOLD and not plugged:
                self.callback("battery_low", pct)
            # Full battery alert
            elif pct >= config.BATTERY_FULL_THRESHOLD and plugged:
                self.callback("battery_full", pct)
            # Charging start alert
            elif plugged and not self._last_battery[1]:
                self.callback("charging", pct)
                
            self._last_battery = (pct, plugged)

    def _check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            connected = True
        except OSError:
            connected = False

        if connected != self._last_internet:
            if connected:
                self.callback("internet_connected", None)
            else:
                self.callback("internet_disconnected", None)
            self._last_internet = connected

    def _check_reminders(self, memory):
        due = memory.get_due_reminders()
        for reminder in due:
            self.callback("reminder", reminder['title'])
            memory.mark_reminder_notified(reminder['id'])
