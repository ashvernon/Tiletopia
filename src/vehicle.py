# src/vehicle.py

import pygame
from pathfinding import a_star
from config import TILE_SIZE

class Vehicle:
    def __init__(self, x, y, path, vehicle_type="car", on_arrival=None):
        self.x = x
        self.y = y
        self.path = path  # list of (row, col)
        self.type = vehicle_type
        self.speed = 1.0
        self.current_tile = 0
        self.alive = True  # will despawn after finishing
        self.on_arrival = on_arrival  # callback to re-spawn sim etc.

    def update(self):
        if not self.path or self.current_tile >= len(self.path):
            self.alive = False
            return

        tile = self.path[self.current_tile]
        if not isinstance(tile, tuple) or len(tile) != 2:
            print("🚨 Invalid tile in path:", tile)
            self.alive = False
            return

        row, col = tile
        target_x = col * TILE_SIZE
        target_y = row * TILE_SIZE

        dx = target_x - self.x
        dy = target_y - self.y

        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < self.speed:
            self.x = target_x
            self.y = target_y
            self.current_tile += 1

            if self.current_tile >= len(self.path):
                self.alive = False
                if self.on_arrival:
                    self.on_arrival(self)  # trigger callback if defined
        else:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def draw(self, screen, camera):
        if not self.alive:
            return
        screen_x, screen_y = camera.apply((self.x, self.y))
        color = (255, 0, 0) if self.type == "car" else (255, 165, 0)
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), 5)
