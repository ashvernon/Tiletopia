# src/sim.py

import pygame
from config import TILE_SIZE
from pathfinding import a_star

class Sim:
    def __init__(self, tile_x, tile_y, game):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.game = game
        self.size = 4

        # state machine
        self.state = "seeking_home"
        self.home = None
        self.job = None
        self.path = []
        self.progress = 0
        self.speed = 0.05
        self.state_timer = 0

        self.vehicle = None
        self.in_vehicle = False

    def update(self):
        # 1) Movement along path
        if self.path and self.progress >= 1.0:
            next_tile = self.path.pop(0)
            self.tile_y, self.tile_x = next_tile
            self.progress = 0
        elif self.path:
            self.progress += self.speed
            return  # still walking

        # 2) Perform state transitions
        grid = self.game.map_mgr.grid  # use MapManager's grid

        if self.state == "seeking_home":
            # find nearest unclaimed house
            self.home = self.game.find_nearest_tile(
                "house", self.tile_x, self.tile_y, occupied_check=True
            )
            if self.home:
                # path on roads + houses
                self.path = a_star(grid,
                                   (self.tile_y, self.tile_x),
                                   self.home,
                                   valid_tiles=["road","house"])
                self.state = "moving_in"

        elif self.state == "moving_in":
            if (self.tile_y, self.tile_x) == self.home:
                self.game.claimed_homes.add(self.home)
                self.state = "seeking_job"

        elif self.state == "seeking_job":
            self.job = self.game.find_nearest_tile(
                "factory", self.tile_x, self.tile_y, occupied_check=True
            )
            if self.job:
                self.game.claimed_jobs.add(self.job)
                self.path = self._path_to(self.job)
                self.state = "going_to_work"

        elif self.state == "going_to_work":
            if (self.tile_y, self.tile_x) == self.job:
                self.state = "working"
                self.state_timer = 0

        elif self.state == "working":
            self.state_timer += 1
            if self.state_timer >= 480:
                self.path = self._path_to(self.home)
                self.state = "going_home"

        elif self.state == "going_home":
            if (self.tile_y, self.tile_x) == self.home:
                self.state = "idle"
                self.state_timer = 0

        elif self.state == "idle":
            self.state_timer += 1
            if self.state_timer >= 240:
                self.path = self._path_to(self.job)
                self.state = "going_to_work"

    def _path_to(self, target):
        """
        Decide walk vs. drive based on Manhattan distance.
        If driving, spawn a Vehicle; otherwise return a walk path.
        """
        dist = abs(self.tile_x - target[1]) + abs(self.tile_y - target[0])
        grid = self.game.map_mgr.grid

        if dist > 15:
            # spawn vehicle on road path
            self.vehicle = self.game.spawn_vehicle(self.tile_x, self.tile_y, target)
            if self.vehicle:
                self.in_vehicle = True
            return []
        else:
            return a_star(grid,
                          (self.tile_y, self.tile_x),
                          target,
                          valid_tiles=["road","house","factory"])

    def draw(self, screen, camera):
        # If in vehicle, the vehicle draws them instead
        if self.in_vehicle:
            return

        x = self.tile_x * TILE_SIZE + TILE_SIZE // 2
        y = self.tile_y * TILE_SIZE + TILE_SIZE // 2
        screen_x, screen_y = camera.apply((x, y))
        pygame.draw.circle(screen, (0, 0, 255), (int(screen_x), int(screen_y)), self.size)
