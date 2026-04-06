import asyncio
import threading
import json
import webbrowser
from pathlib import Path

try:
    import webview
except ImportError:
    webview = None

try:
    import websockets
except ImportError:
    websockets = None

import config

class HologramWindow:
    def __init__(self):
        self.window = None
        self.loop = None
        self.server = None
        self.clients = set()
        self.current_emotion = "neutral"
        self.is_speaking = False
        self.thread = None
        self.html_path = Path(__file__).parent / "hologram.html"

    def _start_ws_server(self):
        """Run the WebSocket server in a dedicated event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def handler(websocket, path):
            self.clients.add(websocket)
            try:
                # Send current state on connect
                await websocket.send(json.dumps({"type": "emotion", "value": self.current_emotion}))
                await websocket.send(json.dumps({"type": "speaking", "value": self.is_speaking}))
                async for message in websocket:
                    pass # We only send for now
            finally:
                self.clients.remove(websocket)

            # Keep the loop running
        start_server = websockets.serve(handler, "localhost", 7788)
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    def show(self):
        if webview is None:
            print("⚠️ Hologram: pywebview not installed. Skipping window.")
            return

        self.thread = threading.Thread(target=self._run_window, daemon=True)
        self.thread.start()
        
        if websockets:
            threading.Thread(target=self._start_ws_server, daemon=True).start()

    def _run_window(self):
        self.window = webview.create_window(
            "Manu Hologram",
            url=str(self.html_path.absolute()),
            width=400,
            height=400,
            frameless=True,
            on_top=True,
            transparent=True,
            background_color="#000000"
        )
        webview.start()

    def set_emotion(self, emotion: str):
        self.current_emotion = emotion
        self._broadcast({"type": "emotion", "value": emotion})

    def set_speaking(self, speaking: bool):
        self.is_speaking = speaking
        self._broadcast({"type": "speaking", "value": speaking})

    def _broadcast(self, data):
        if self.loop and self.clients:
            future = asyncio.run_coroutine_threadsafe(
                self._send_to_all(data), self.loop
            )

    async def _send_to_all(self, data):
        if self.clients:
            msg = json.dumps(data)
            await asyncio.gather(*[client.send(msg) for client in self.clients])

    def close(self):
        if self.window:
            self.window.destroy()
        if self.loop:
            self.loop.stop()
