"""
engines/tray_engine.py
System tray icon for Manu's invisible Siri mode.

Shows a small circular "M" icon in the Windows system tray.
Right-click menu: Open GUI / Mute / View Log / Settings / Quit

Uses pystray + Pillow. Falls back gracefully if not installed.
"""

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

log = logging.getLogger("Manu.Tray")


class TrayEngine:
    """
    System tray icon and menu for Manu.
    Runs pystray in a dedicated background thread.

    Status updates (tooltip text) are thread-safe via update_status().
    """

    def __init__(self, on_open_gui, on_quit, on_mute_toggle):
        """
        Args:
            on_open_gui:    Called when user clicks "Open GUI"
            on_quit:        Called when user clicks "Quit Manu"
            on_mute_toggle: Called when user clicks "Mute / Unmute"
        """
        self._on_open_gui    = on_open_gui
        self._on_quit        = on_quit
        self._on_mute_toggle = on_mute_toggle

        self._icon   = None
        self._muted  = False
        self._thread = None
        self._ready  = False

    def start(self):
        """Start tray icon in a daemon thread. Non-blocking."""
        self._thread = threading.Thread(
            target=self._run_tray,
            name="ManuTray",
            daemon=True,
        )
        self._thread.start()
        log.info("Tray engine started.")

    def stop(self):
        """Remove tray icon and stop."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def update_status(self, text: str):
        """
        Update the tooltip text shown on hover.
        Thread-safe — can be called from any thread.
        Truncates to 63 chars (Windows tray tooltip limit).
        """
        if self._icon:
            try:
                self._icon.title = text[:63]
            except Exception:
                pass

    def update_icon_state(self, state: str):
        """
        Change tray icon color to reflect Manu's state.
        state: "listening" | "thinking" | "idle" | "muted"
        """
        if not self._icon:
            return
        try:
            new_icon = self._make_icon_image(state=state)
            self._icon.icon = new_icon
        except Exception as e:
            log.debug(f"Icon update failed: {e}")

    # ── Tray Setup ────────────────────────────────────────────────────────────

    def _run_tray(self):
        """Build and run the pystray icon. Blocks this thread."""
        try:
            import pystray
            from PIL import Image

            icon_image = self._make_icon_image(state="idle")

            # Build right-click context menu
            menu = pystray.Menu(
                pystray.MenuItem(
                    "🤖 Manu is Listening",
                    action=None,
                    enabled=False,      # Header label — not clickable
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Open GUI Window",
                    self._menu_open_gui,
                ),
                pystray.MenuItem(
                    "Mute / Unmute Manu",
                    self._menu_mute,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "View Log File",
                    self._menu_view_log,
                ),
                pystray.MenuItem(
                    "Edit Settings",
                    self._menu_edit_settings,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Quit Manu",
                    self._menu_quit,
                ),
            )

            self._icon = pystray.Icon(
                name="Manu",
                icon=icon_image,
                title="🤖 Manu — Listening",
                menu=menu,
            )
            self._ready = True
            log.info("Tray icon active. Right-click to access menu.")
            self._icon.run()     # Blocks this thread (correct behavior)

        except ImportError:
            log.warning(
                "pystray or Pillow not installed — no tray icon.\n"
                "  Install with: pip install pystray Pillow\n"
                "  Manu will still work, just without a tray icon."
            )
        except Exception as e:
            log.error(f"Tray engine error: {e}")

    # ── Icon Image ────────────────────────────────────────────────────────────

    def _make_icon_image(self, state: str = "idle"):
        """
        Programmatically generate the tray icon using Pillow.
        No external image files needed.

        States and their colors:
          idle      → deep purple (#6C63FF) — Manu is ready
          listening → teal (#00BFA5) — actively hearing
          thinking  → amber (#FFA000) — processing
          muted     → dark gray (#424242) — silenced
        """
        from PIL import Image, ImageDraw, ImageFont

        SIZE = 64

        color_map = {
            "idle":      "#6C63FF",
            "listening": "#00BFA5",
            "thinking":  "#FFA000",
            "muted":     "#424242",
        }
        bg_color = color_map.get(state, "#6C63FF")

        img  = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Filled circle background
        draw.ellipse(
            [2, 2, SIZE - 2, SIZE - 2],
            fill=bg_color,
            outline="#FFFFFF",
            width=2,
        )

        # "M" letter in white, centered
        # Use a simple drawn "M" shape since fonts vary by system
        m_color = "#FFFFFF"
        lx, rx  = 16, 48   # Left and right x
        ty, by  = 18, 46   # Top and bottom y
        mx      = SIZE // 2   # Middle x

        # Draw M as 4 lines: left up, down-center, up-center, down-right
        line_w = 4
        draw.line([(lx, by), (lx, ty)],    fill=m_color, width=line_w)
        draw.line([(lx, ty), (mx, by - 8)], fill=m_color, width=line_w)
        draw.line([(mx, by - 8), (rx, ty)], fill=m_color, width=line_w)
        draw.line([(rx, ty), (rx, by)],    fill=m_color, width=line_w)

        return img

    # ── Menu Actions ──────────────────────────────────────────────────────────

    def _menu_open_gui(self, icon=None, item=None):
        """Open the Tkinter/CustomTkinter GUI window."""
        log.info("User requested GUI via tray.")
        try:
            self._on_open_gui()
        except Exception as e:
            log.error(f"Open GUI failed: {e}")

    def _menu_mute(self, icon=None, item=None):
        """Toggle Manu's audio output mute state."""
        self._muted = not self._muted
        state = "muted" if self._muted else "idle"
        self.update_status("🔇 Manu — Muted" if self._muted else "🤖 Manu — Listening")
        self.update_icon_state(state)
        log.info(f"Manu {'muted' if self._muted else 'unmuted'} via tray.")
        try:
            self._on_mute_toggle(self._muted)
        except Exception as e:
            log.error(f"Mute toggle callback error: {e}")

    def _menu_view_log(self, icon=None, item=None):
        """Open the Manu log file in the default text editor."""
        log_path = Path("data") / "logs" / "manu.log"
        if not log_path.exists():
            log.info("No log file found yet.")
            return
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(log_path))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(log_path)])
            else:
                subprocess.Popen(["xdg-open", str(log_path)])
        except Exception as e:
            log.error(f"Open log failed: {e}")

    def _menu_edit_settings(self, icon=None, item=None):
        """Open main.py's companion config in a text editor."""
        # Try to open engines/brain_engine.py for easy model switching
        config_files = [
            Path("engines") / "brain_engine.py",
            Path("main.py"),
        ]
        for f in config_files:
            if f.exists():
                try:
                    import platform
                    if platform.system() == "Windows":
                        os.startfile(str(f))
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", "-e", str(f)])
                    else:
                        subprocess.Popen(["xdg-open", str(f)])
                    return
                except Exception as e:
                    log.error(f"Open settings failed: {e}")

    def _menu_quit(self, icon=None, item=None):
        """Quit Manu completely."""
        log.info("User quit Manu via tray menu.")
        self.stop()
        try:
            self._on_quit()
        except Exception:
            pass
        sys.exit(0)
