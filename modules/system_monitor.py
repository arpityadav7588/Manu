"""
modules/system_monitor.py
Background daemon: monitors battery and internet,
fires callback(event, detail) on state changes.
"""

import logging
import socket
import threading
import time

import psutil

log = logging.getLogger("Manu.Monitor")

POLL_INTERVAL  = 30   # seconds between checks
LOW_BATTERY    = 20   # % threshold for battery_low event
FULL_BATTERY   = 95   # % threshold for battery_full event


class SystemMonitor:

    def __init__(self, callback):
        """
        callback(event: str, detail: int) is called on state changes.
        Events: battery_low, charging, battery_full,
                internet_lost, internet_restored
        detail: battery percentage (for battery events) or 0
        """
        self._callback = callback
        self._thread   = None

        # Previous state tracking (only fire on changes)
        self._prev_plugged   = None
        self._prev_pct       = None
        self._prev_internet  = None
        self._low_alerted    = False
        self._full_alerted   = False

    def start(self):
        """Start the background monitoring daemon thread."""
        self._thread = threading.Thread(
            target=self._loop,
            name="ManuMonitor",
            daemon=True,
        )
        self._thread.start()
        log.info("System monitor started (battery + internet).")

    def _loop(self):
        time.sleep(5)   # Give Manu time to finish greeting before first check
        while True:
            try:
                self._check_battery()
                self._check_internet()
            except Exception as e:
                log.error(f"Monitor loop error: {e}")
            time.sleep(POLL_INTERVAL)

    def _check_battery(self):
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return   # Desktop — no battery

            pct     = bat.percent
            plugged = bat.power_plugged

            # Just plugged in (was unplugged → now plugged)
            if plugged and self._prev_plugged is False:
                self._low_alerted  = False
                self._full_alerted = False
                self._callback("charging", int(pct))

            # Just unplugged
            elif not plugged and self._prev_plugged is True:
                self._callback("unplugged", int(pct))

            # Battery low (and not already alerted)
            elif not plugged and pct <= LOW_BATTERY and not self._low_alerted:
                self._low_alerted = True
                self._callback("battery_low", int(pct))

            # Battery full (and plugged in, not already alerted)
            elif plugged and pct >= FULL_BATTERY and not self._full_alerted:
                self._full_alerted = True
                self._callback("battery_full", int(pct))

            # Reset low alert when battery recovers
            if pct > LOW_BATTERY + 10:
                self._low_alerted = False

            self._prev_plugged = plugged
            self._prev_pct     = pct

        except Exception as e:
            log.debug(f"Battery check error: {e}")

    def _check_internet(self):
        connected = self._ping()
        if connected != self._prev_internet:
            if self._prev_internet is not None:
                event = "internet_restored" if connected else "internet_lost"
                self._callback(event, 0)
                log.info(f"Internet: {event}")
            self._prev_internet = connected

    def _ping(self) -> bool:
        """Fast connectivity check — DNS socket to Google."""
        try:
            socket.setdefaulttimeout(2.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                ("8.8.8.8", 53)
            )
            return True
        except (socket.error, OSError):
            return False
