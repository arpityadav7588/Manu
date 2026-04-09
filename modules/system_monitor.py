import threading
import time
import psutil
import socket

class SystemMonitor:
    def __init__(self, callback):
        try:
            self.callback = callback
            self._thread = None
            self._running = False
            self._last_battery_pct = None
            self._last_plugged = None
            self._last_internet = None
            self._high_cpu_warned = False
        except Exception as e:
            print(f"Monitor init error: {e}")

    def start(self):
        try:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        except Exception as e:
            pass

    def stop(self):
        self._running = False

    def _loop(self):
        try:
            time.sleep(6)
            while self._running:
                self._check_battery()
                self._check_internet()
                self._check_cpu()
                
                for _ in range(45):
                    if not self._running:
                        break
                    time.sleep(1)
        except Exception as e:
            print(f"Monitor loop error: {e}")

    def _check_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return
                
            pct = battery.percent
            plugged = battery.power_plugged
            
            if self._last_plugged is not None:
                if plugged and not self._last_plugged:
                    self.callback("charging", int(pct))
                elif not plugged and self._last_plugged:
                    self.callback("unplugged", int(pct))
                elif pct <= 20 and not plugged and (self._last_battery_pct is None or self._last_battery_pct > 20):
                    self.callback("battery_low", int(pct))
                elif pct >= 95 and plugged and (self._last_battery_pct is None or self._last_battery_pct < 95):
                    self.callback("battery_full", int(pct))
                    
            self._last_battery_pct = pct
            self._last_plugged = plugged
        except Exception as e:
            pass

    def _check_internet(self):
        try:
            connected = False
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=2)
                connected = True
            except:
                connected = False
                
            if self._last_internet is not None and connected != self._last_internet:
                self.callback("internet_on" if connected else "internet_off", connected)
                
            self._last_internet = connected
        except Exception as e:
            pass

    def _check_cpu(self):
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            if cpu > 88 and not self._high_cpu_warned:
                self.callback("high_cpu", int(cpu))
                self._high_cpu_warned = True
            if cpu < 70:
                self._high_cpu_warned = False
        except Exception as e:
            pass
