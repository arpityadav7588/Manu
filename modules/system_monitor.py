import psutil
import requests
import time
import threading

class SystemMonitor:
    def __init__(self, callback):
        self.callback = callback
        self.last_battery = psutil.sensors_battery().percent
        self.last_plugged = psutil.sensors_battery().power_plugged
        self.last_internet = self.check_internet()
        self.running = True

    def check_internet(self):
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except:
            return False

    def monitor_loop(self):
        """
        Background loop to check for changes in system status.
        """
        while self.running:
            # Check Battery
            battery = psutil.sensors_battery()
            if battery.percent != self.last_battery:
                if battery.percent <= 20 and not battery.power_plugged:
                    self.callback("battery_low", battery.percent)
                elif battery.percent == 100 and battery.power_plugged:
                     self.callback("battery_full", battery.percent)
                     
            if battery.power_plugged != self.last_plugged:
                if battery.power_plugged:
                    self.callback("charging", battery.percent)
                else:
                    self.callback("unplugged", battery.percent)
                    
            self.last_battery = battery.percent
            self.last_plugged = battery.power_plugged

            # Check Internet
            internet = self.check_internet()
            if internet != self.last_internet:
                if internet:
                    self.callback("internet_back", True)
                else:
                    self.callback("internet_lost", False)
            self.last_internet = internet

            time.sleep(10) # Check every 10 seconds

    def start(self):
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    def test_callback(event, detail):
        print(f"Event: {event}, Detail: {detail}")

    monitor = SystemMonitor(test_callback)
    monitor.start()
    print("Monitoring started. Unplug your charger to see trigger.")
    time.sleep(60)
