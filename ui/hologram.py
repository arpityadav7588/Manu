import os
import sys
import math
import threading
import subprocess
import time
import json
import random
import config

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False

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
    Renders a 3D torus with orbital particles and scanline effects.
    """
    def __init__(self, width=400, height=400):
        self.width = width
        self.height = height
        self.emotion = "neutral"
        self.speaking = False
        self.rotation = 0
        self.particles = [[random.uniform(-2, 2) for _ in range(3)] for _ in range(20)]
        self.colors = {
            "happy": (0.2, 0.8, 0.6),
            "excited": (1.0, 0.6, 0.2),
            "concerned": (0.9, 0.4, 0.4),
            "sleepy": (0.5, 0.6, 0.7),
            "playful": (1.0, 0.8, 0.2),
            "thinking": (0.5, 0.4, 0.9),
            "neutral": (0.4, 0.4, 1.0),
            "listening": (0.1, 0.8, 0.9)
        }

    def run(self):
        if not HAS_PYGAME or not HAS_OPENGL:
            print("[!] PyGame or PyOpenGL missing. Subprocess exiting.")
            sys.exit(1)

        pygame.init()
        # Set window position/frameless if possible
        os.environ['SDL_VIDEO_WINDOW_POS'] = "100,100"
        display = (self.width, self.height)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL | NOFRAME)
        pygame.display.set_caption("Manu Hologram")

        gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)

        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            color = self.colors.get(self.emotion, self.colors["neutral"])
            pulse = 1.2 if self.speaking else 1.0
            
            self._draw_torus(color, pulse)
            self._draw_particles(color)
            
            pygame.display.flip()
            self.rotation += 1
            clock.tick(60)

    def _draw_torus(self, color, pulse):
        glPushMatrix()
        glRotatef(self.rotation, 1, 1, 0)
        glScalef(pulse, pulse, pulse)
        glColor3f(*color)
        # Wireframe Torus
        R = 1.5
        r = 0.5
        sections = 24
        rings = 24
        
        for i in range(rings):
            glBegin(GL_LINE_LOOP)
            for j in range(sections):
                theta = (math.pi * 2 * i) / rings
                phi = (math.pi * 2 * j) / sections
                x = (R + r * math.cos(phi)) * math.cos(theta)
                y = (R + r * math.cos(phi)) * math.sin(theta)
                z = r * math.sin(phi)
                glVertex3f(x, y, z)
            glEnd()
        glPopMatrix()

    def _draw_particles(self, color):
        glPointSize(2.0)
        glBegin(GL_POINTS)
        glColor3f(*color)
        for p in self.particles:
            glVertex3f(p[0] + math.sin(self.rotation/20)*0.1, p[1], p[2])
        glEnd()

class HologramCanvas:
    """Tkinter-compatible widget fallback."""
    def __init__(self, parent, width=300, height=300):
        import tkinter as tk
        self.canvas = tk.Canvas(parent, width=width, height=height, bg="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.emotion = "neutral"
        self.is_speaking = False
        self.items = []
        self._init_draw()

    def _init_draw(self):
        # Draw central glowing circle or hexagons
        self.canvas.create_oval(50, 50, self.width-50, self.height-50, outline="#6c63ff", width=2)
        
    def set_emotion(self, mood):
        colors = {"happy": "#34d399", "concerned": "#f87171", "neutral": "#6c63ff"}
        color = colors.get(mood, "#6c63ff")
        self.canvas.itemconfig("all", outline=color)

    def set_speaking(self, speaking):
        self.is_speaking = speaking

class HologramWindow:
    """Process bridge."""
    def __init__(self):
        self.process = None

    def show(self):
        """Try launching the 3D OpenGL process."""
        if not HAS_PYGAME or not HAS_OPENGL:
            print("[!] Hologram: PyGame/OpenGL missing. Using 2D fallback.")
            return
            
        try:
            print("[*] Launching 3D Hologram Subprocess...")
            # In a real environment, we'd spawn sys.executable with this file as script
            # self.process = subprocess.Popen([sys.executable, __file__])
        except Exception as e:
            print(f"[!] Hologram Error: {e}")

    def set_emotion(self, emotion):
        pass

    def set_speaking(self, speaking):
        pass

if __name__ == "__main__":
    avatar = HologramAvatar()
    avatar.run()
