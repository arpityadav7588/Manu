import os
import sys
import math
import threading
import subprocess
import time
import json
import random
import config
from multiprocessing import Process, Queue

try:
    import pygame
    from pygame.locals import *
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False

class HologramAvatar:
    """
    Subprocess-ready 3D Hologram renderer using PyOpenGL and pygame.
    Renders a 3D torus with orbital particles, scanline effects, and additive blending.
    """
    def __init__(self, width=400, height=450):
        self.width = width
        self.height = height
        self.emotion = "neutral"
        self.speaking = False
        self.listening = False
        self.mood_text = "STATUS: ONLINE"
        self.rotation = 0
        self.tilt = 25 # X-axis tilt
        self.particles = [[random.uniform(-3, 3) for _ in range(3)] for _ in range(30)]
        self.colors = {
            "happy": (0.2, 0.8, 0.4),    # Green
            "excited": (1.0, 0.8, 0.0),  # Gold
            "concerned": (1.0, 0.5, 0.0),# Orange
            "sleepy": (0.5, 0.5, 0.8),   # Dim Blue
            "playful": (1.0, 0.4, 0.7),  # Pinkish
            "thinking": (0.6, 0.2, 0.9), # Purple
            "neutral": (0.0, 0.6, 1.0),  # Blue
            "listening": (0.0, 1.0, 1.0) # Cyan
        }
        self.queue = Queue()

    def start(self, w=None, h=None):
        """Launch the OpenGL renderer in a separate process."""
        if w: self.width = w
        if h: self.height = h
        self.process = Process(target=self._run_loop, args=(self.queue,), daemon=True)
        self.process.start()

    def stop(self):
        if self.process:
            self.queue.put({"type": "quit"})
            self.process.join(timeout=1)
            self.process.terminate()

    def set_emotion(self, mood):
        self.queue.put({"type": "emotion", "value": mood})

    def set_speaking(self, speaking):
        self.queue.put({"type": "speaking", "value": speaking})

    def set_listening(self, listening):
        self.queue.put({"type": "listening", "value": listening})

    def set_mood_text(self, text):
        self.queue.put({"type": "text", "value": text})

    def _run_loop(self, q):
        if not HAS_PYGAME or not HAS_OPENGL:
            return

        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "center"
        display = (self.width, self.height)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL | NOFRAME)
        pygame.display.set_caption("Manu Hologram")

        # Enable additive blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_LINE_SMOOTH)

        gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -8)

        clock = pygame.time.Clock()
        
        local_state = {
            "emotion": "neutral",
            "speaking": False,
            "listening": False,
            "text": "NEUTRAL",
            "rotation": 0
        }

        while True:
            # Check for messages
            while not q.empty():
                msg = q.get_nowait()
                if msg["type"] == "quit": return
                local_state[msg["type"]] = msg["value"]

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            color = self.colors.get(local_state["emotion"], self.colors["neutral"])
            pulse = 1.0 + math.sin(time.time() * 10) * 0.1 if local_state["speaking"] else 1.0
            if local_state["listening"]: pulse = 1.1 + math.sin(time.time() * 15) * 0.05

            self._draw_background_grid()
            self._draw_torus(color, pulse, local_state["rotation"])
            self._draw_particles(color, local_state["rotation"])
            self._draw_scanlines()
            
            # Note: HUD text in OpenGL requires font rendering which is heavy for a script.
            # We will use console logging as a logic proof or assume surface rendering.
            
            pygame.display.flip()
            local_state["rotation"] += 1.5
            clock.tick(60)

    def _draw_torus(self, color, pulse, rotation):
        glPushMatrix()
        glRotatef(self.tilt, 1, 0, 0)
        glRotatef(rotation, 0, 1, 0)
        glScalef(pulse, pulse, pulse)
        
        # Multiple rings for depth
        for offset in [0, 0.1, -0.1]:
            alpha = 0.8 if offset == 0 else 0.3
            glColor4f(color[0], color[1], color[2], alpha)
            
            R, r = 2.0, 0.6
            sections, rings = 30, 30
            for i in range(rings):
                glBegin(GL_LINE_LOOP)
                for j in range(sections):
                    theta = (math.pi * 2 * i) / rings
                    phi = (math.pi * 2 * j) / sections
                    x = (R + r * math.cos(phi)) * math.cos(theta)
                    y = (R + r * math.cos(phi)) * math.sin(theta)
                    z = (r * math.sin(phi)) + offset
                    glVertex3f(x, y, z)
                glEnd()
        glPopMatrix()

    def _draw_particles(self, color, rotation):
        glPushMatrix()
        glRotatef(rotation * 0.5, 0, 1, 0)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        glColor4f(color[0], color[1], color[2], 0.6)
        for i, p in enumerate(self.particles):
            # Orbiting motion
            offset = math.sin(time.time() + i) * 0.5
            glVertex3f(p[0] * (1+offset*0.1), p[1], p[2])
        glEnd()
        glPopMatrix()

    def _draw_background_grid(self):
        glColor4f(0.0, 0.3, 0.5, 0.1)
        glBegin(GL_LINES)
        for i in range(-10, 11):
            glVertex3f(i, -10, -5); glVertex3f(i, 10, -5)
            glVertex3f(-10, i, -5); glVertex3f(10, i, -5)
        glEnd()

    def _draw_scanlines(self):
        # Horizontal lines overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glColor4f(0, 0, 0, 0.2)
        glBegin(GL_LINES)
        for y in range(0, self.height, 4):
            glVertex2f(0, y); glVertex2f(self.width, y)
        glEnd()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

class HologramCanvas:
    """Tkinter-compatible widget fallback."""
    def __init__(self, parent, width=300, height=350):
        import tkinter as tk
        self.canvas = tk.Canvas(parent, width=width, height=height, bg="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.emotion = "neutral"
        self.is_speaking = False
        self.angle = 0
        self.scan_y = 0
        
        self.colors = {
            "happy": "#34d399", "excited": "#fbbf24", "concerned": "#fb923c",
            "sleepy": "#64748b", "playful": "#f472b6", "thinking": "#818cf8",
            "neutral": "#60a5fa", "listening": "#22d3ee"
        }
        self._animate()

    def set_emotion(self, mood):
        self.emotion = mood

    def set_speaking(self, speaking):
        self.is_speaking = speaking

    def _animate(self):
        self.canvas.delete("all")
        color = self.colors.get(self.emotion, self.colors["neutral"])
        cx, cy = self.width//2, self.height//2
        
        # 1. Floating Hexagons (Task 1)
        for i in range(3):
            s = 60 + i*30 + (math.sin(self.angle/10 + i)*10 if self.is_speaking else 0)
            self._draw_poly(cx, cy, 6, s, self.angle * (1 if i%2==0 else -1), color)
            
        # 2. Pulsing Rings
        r = 120 + math.sin(self.angle/5)*5
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=1, dash=(5,5))
        
        # 3. Moving Scanline
        self.scan_y = (self.scan_y + 2) % self.height
        self.canvas.create_line(0, self.scan_y, self.width, self.scan_y, fill=color, stipple="gray25")
        
        self.angle += 0.05
        self.canvas.after(33, self._animate)

    def _draw_poly(self, x, y, n, size, rotate, color):
        pts = []
        for i in range(n):
            phi = (i * 2 * math.pi / n) + rotate
            pts.append(x + size * math.cos(phi))
            pts.append(y + size * math.sin(phi))
        self.canvas.create_polygon(pts, outline=color, fill="", width=2)

class HologramWindow:
    """Bridge for HologramAvatar (multiprocessing)."""
    def __init__(self):
        self.avatar = HologramAvatar()

    def start(self, width=400, height=450):
        self.avatar.start(width, height)

    def set_emotion(self, mood):
        self.avatar.set_emotion(mood)

    def set_speaking(self, speaking):
        self.avatar.set_speaking(speaking)

    def set_listening(self, listening):
        self.avatar.set_listening(listening)

    def set_mood_text(self, text):
        self.avatar.set_mood_text(text)

    def stop(self):
        self.avatar.stop()

if __name__ == "__main__":
    # Test stub
    h = HologramAvatar()
    h._run_loop(Queue())
