# src/map.py

import random
from config import ROWS, COLS

class MapManager:
    def __init__(self):
        self.grid = [["grass" for _ in range(COLS)] for _ in range(ROWS)]
        self.place_outside_connection()

    def place_outside_connection(self):
        edge = random.choice(['top','bottom','left','right'])
        if edge=='top':
            c = random.randrange(COLS);   self.grid[0][c] = "road"
        elif edge=='bottom':
            c = random.randrange(COLS);   self.grid[ROWS-1][c] = "road"
        elif edge=='left':
            r = random.randrange(ROWS);   self.grid[r][0] = "road"
        else:
            r = random.randrange(ROWS);   self.grid[r][COLS-1] = "road"

    def get(self, row, col):
        return self.grid[row][col]

    def set_tile(self, row, col, tile):
        self.grid[row][col] = tile

    def find_nearest(self, tile_type, start_x, start_y, claimed=None):
        from collections import deque
        claimed = claimed or set()
        visited = {(start_y, start_x)}
        queue = deque([(start_y, start_x)])
        while queue:
            y, x = queue.popleft()
            if self.grid[y][x] == tile_type and (y, x) not in claimed:
                return (y, x)
            for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                ny, nx = y+dy, x+dx
                if 0<=ny<ROWS and 0<=nx<COLS and (ny, nx) not in visited:
                    visited.add((ny, nx))
                    queue.append((ny, nx))
        return None

    def grow_zones(self, res_demand, ind_demand):
        for r in range(ROWS):
            for c in range(COLS):
                t = self.grid[r][c]
                if t=="zone_residential" and res_demand:
                    if any(0<=r+dr<ROWS and 0<=c+dc<COLS and self.grid[r+dr][c+dc]=="road"
                           for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]):
                        if random.random()<0.01:
                            self.grid[r][c] = "house"
                elif t=="zone_industrial" and ind_demand:
                    if any(0<=r+dr<ROWS and 0<=c+dc<COLS and self.grid[r+dr][c+dc]=="road"
                           for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]):
                        if random.random()<0.01:
                            self.grid[r][c] = "factory"
