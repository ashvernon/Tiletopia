# src/camera.py

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0

    def apply(self, pos):
        """Transform world coordinates to screen coordinates"""
        x, y = pos
        return (x - self.x) * self.zoom, (y - self.y) * self.zoom

    def world_to_tile(self, screen_x, screen_y, tile_size):
        """Convert screen coordinates to map tile indexes"""
        world_x = (screen_x / self.zoom) + self.x
        world_y = (screen_y / self.zoom) + self.y
        return int(world_x // tile_size), int(world_y // tile_size)

    def adjust_zoom(self, delta):
        self.zoom *= 1.1 if delta > 0 else 0.9
        self.zoom = max(0.5, min(2.0, self.zoom))
