import pygame, json, random
from config      import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, ROWS, COLS, COLORS
from camera      import Camera
from sim         import Sim
from vehicle     import Vehicle
from pathfinding import a_star
from map         import MapManager
from economy     import Economy

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Casual City Builder")
        self.clock   = pygame.time.Clock()
        self.running = True

        # ——— Core Systems ——————————————————————————————————————————————————
        self.map_mgr = MapManager()                  # handles grid + outside road
        self.econ    = Economy(tax_rate=0.10)        # handles pop/jobs/income
        self.camera  = Camera()                      # pan & zoom

        # ——— State ———————————————————————————————————————————————————————
        self.claimed_homes = set()
        self.claimed_jobs  = set()

        self.money            = 1000
        self.last_income_tick = pygame.time.get_ticks()
        self.income_interval  = 3000  # payout every 3s

        self.sims     = [ Sim(0,0,self) ]
        self.vehicles = []

        # ——— Input / UI ————————————————————————————————————————————————————
        self.selected_tool   = "road"
        self.dragging        = False
        self.last_mouse_pos  = (0,0)

        self.font           = pygame.font.SysFont(None,24)
        self.toolbar_height = 70
        self.toolbar_buttons = {
            "road":             pygame.Rect( 10, SCREEN_HEIGHT-self.toolbar_height+5,  70,30),
            "house":            pygame.Rect( 90, SCREEN_HEIGHT-self.toolbar_height+5,  70,30),
            "factory":          pygame.Rect(170, SCREEN_HEIGHT-self.toolbar_height+5,  70,30),
            "zone_residential": pygame.Rect(250, SCREEN_HEIGHT-self.toolbar_height+5, 130,30),
            "zone_industrial":  pygame.Rect(390, SCREEN_HEIGHT-self.toolbar_height+5, 130,30),
            "bulldozer":        pygame.Rect(530, SCREEN_HEIGHT-self.toolbar_height+5,  90,30),
        }

    def find_nearest_tile(self, tile_type, start_x, start_y, occupied_check=False):
        """
        Delegate to MapManager.find_nearest, honoring claimed homes/jobs
        so Sims don’t re-take the same house or factory.
        """
        claimed = set()
        if occupied_check:
            if tile_type == "house":
                claimed = self.claimed_homes
            elif tile_type == "factory":
                claimed = self.claimed_jobs
        # MapManager.find_nearest signature: (tile_type, start_x, start_y, claimed_set)
        return self.map_mgr.find_nearest(tile_type, start_x, start_y, claimed)


    # ——— Vehicle spawning —————————————————————————————————————————————
    def spawn_vehicle(self, tx, ty, target):
        if not (isinstance(target, tuple) and len(target)==2):
            print("🚨 Invalid vehicle target:", target)
            return None

        path = a_star(self.map_mgr.grid, (ty,tx), target, valid_tiles=["road"])
        if path and all(isinstance(p,tuple) and len(p)==2 for p in path):
            # world coords in pixels
            start_x = tx * TILE_SIZE
            start_y = ty * TILE_SIZE
            v = Vehicle(start_x, start_y, path, vehicle_type="car",
                        on_arrival=lambda v:self.on_vehicle_arrival(v))
            self.vehicles.append(v)
            return v
        else:
            print("🚨 Invalid vehicle path:", path)
        return None

    def on_vehicle_arrival(self, vehicle):
        # when a vehicle finishes, free the Sim and despawn
        for sim in self.sims:
            if sim.vehicle is vehicle:
                sim.in_vehicle = False
                sim.vehicle    = None
                # place sim at tile of last path step
                if vehicle.path:
                    y,x = vehicle.path[-1]
                    sim.tile_y, sim.tile_x = y,x
        # vehicle.alive will be False → cleaned up in update()

     # ——— Input Handling —————————————————————————————————————————————
    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        col, row = self.camera.world_to_tile(mx, my, TILE_SIZE)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False

            elif ev.type == pygame.MOUSEWHEEL:
                self.camera.adjust_zoom(ev.y)

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 2:
                    self.dragging = True
                    self.last_mouse_pos = (mx, my)

                elif my >= SCREEN_HEIGHT - self.toolbar_height:
                    for tool, rect in self.toolbar_buttons.items():
                        if rect.collidepoint(mx, my):
                            self.selected_tool = tool

                elif 0 <= row < ROWS and 0 <= col < COLS:
                    t = self.map_mgr.get(row, col)

                    # road
                    if self.selected_tool == "road" and t == "grass" and self.money >= 10:
                        self.map_mgr.set_tile(row, col, "road")
                        self.money -= 10

                    # house
                    elif self.selected_tool == "house" and t == "grass":
                        if any(
                            0 <= row + dr < ROWS and 0 <= col + dc < COLS and self.map_mgr.get(row + dr, col + dc) == "road"
                            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]
                        ) and self.money >= 25:
                            self.map_mgr.set_tile(row, col, "house")
                            self.money -= 25

                    # factory
                    elif self.selected_tool == "factory" and t == "grass":
                        if any(
                            0 <= row + dr < ROWS and 0 <= col + dc < COLS and self.map_mgr.get(row + dr, col + dc) == "road"
                            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]
                        ) and self.money >= 40:
                            self.map_mgr.set_tile(row, col, "factory")
                            self.money -= 40

                    # zoning
                    elif self.selected_tool == "zone_residential" and t == "grass":
                        self.map_mgr.set_tile(row, col, "zone_residential")
                    elif self.selected_tool == "zone_industrial" and t == "grass":
                        self.map_mgr.set_tile(row, col, "zone_industrial")

                    # bulldozer
                    elif self.selected_tool == "bulldozer" and t != "grass":
                        self.map_mgr.set_tile(row, col, "grass")

            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 2:
                    self.dragging = False

            elif ev.type == pygame.MOUSEMOTION and self.dragging:
                cx, cy = pygame.mouse.get_pos()
                dx = (self.last_mouse_pos[0] - cx) / self.camera.zoom
                dy = (self.last_mouse_pos[1] - cy) / self.camera.zoom
                self.camera.x += dx
                self.camera.y += dy
                self.last_mouse_pos = (cx, cy)

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_s:
                    self.save_map()
                elif ev.key == pygame.K_l:
                    self.load_map()
                elif ev.key == pygame.K_w:
                    self.camera.y -= 20 / self.camera.zoom
                elif ev.key == pygame.K_s:
                    self.camera.y += 20 / self.camera.zoom
                elif ev.key == pygame.K_a:
                    self.camera.x -= 20 / self.camera.zoom
                elif ev.key == pygame.K_d:
                    self.camera.x += 20 / self.camera.zoom


    # ——— Save / Load —————————————————————————————————————————————————
    def save_map(self, fn="map.json"):
        with open(fn,"w") as f:
            json.dump(self.map_mgr.grid,f)
    def load_map(self,fn="map.json"):
        try:
            with open(fn,"r") as f:
                self.map_mgr.grid=json.load(f)
        except FileNotFoundError:
            print("No saved map.")

    # ——— Main update loop —————————————————————————————————————————————
    def update(self):
        now = pygame.time.get_ticks()

        # economy & zoning
        self.econ.update(self.map_mgr.grid)
        self.map_mgr.grow_zones(self.econ.residential_demand,
                                self.econ.industrial_demand)

        # payout
        if now-self.last_income_tick>self.income_interval:
            self.money   += self.econ.income
            self.econ.income=0
            self.last_income_tick=now

        # Sims & Vehicles
        for sim in self.sims:       sim.update()
        for v in self.vehicles[:]:
            v.update()
            if not v.alive:        self.vehicles.remove(v)

        # spawn new Sim every ~5s
        if now%5000<50:
            self.spawn_sim()

    # ——— Edge‐road Sim spawning —————————————————————————————————————
    def spawn_sim(self):
        edges=[]
        # top/bottom
        for c in range(COLS):
            if self.map_mgr.get(0,c)=="road":      edges.append((c,0))
            if self.map_mgr.get(ROWS-1,c)=="road": edges.append((c,ROWS-1))
        # left/right
        for r in range(ROWS):
            if self.map_mgr.get(r,0)=="road":      edges.append((0,r))
            if self.map_mgr.get(r,COLS-1)=="road": edges.append((COLS-1,r))
        if edges:
            tx,ty = random.choice(edges)
            self.sims.append(Sim(tx,ty,self))

    # ——— Render everything —————————————————————————————————————————————
    def draw(self):
        self.screen.fill((0,0,0))
        # tiles
        for r in range(ROWS):
            for c in range(COLS):
                t = self.map_mgr.get(r,c)
                col = COLORS.get(t,(255,0,255))
                sx,sy = self.camera.apply((c*TILE_SIZE,r*TILE_SIZE))
                s = round(TILE_SIZE*self.camera.zoom)
                pygame.draw.rect(self.screen,col,(round(sx),round(sy),s,s))

        # agents
        for sim in self.sims:       sim.draw(self.screen,self.camera)
        for v   in self.vehicles:   v.draw(self.screen,self.camera)

        # hover highlight
        mx,my = pygame.mouse.get_pos()
        tx,ty = self.camera.world_to_tile(mx,my,TILE_SIZE)
        if 0<=ty<ROWS and 0<=tx<COLS:
            sx,sy = self.camera.apply((tx*TILE_SIZE,ty*TILE_SIZE))
            s = round(TILE_SIZE*self.camera.zoom)
            pygame.draw.rect(self.screen,(255,255,0),(round(sx),round(sy),s,s),2)

        # toolbar
        pygame.draw.rect(self.screen,(50,50,50),(0,SCREEN_HEIGHT-self.toolbar_height,SCREEN_WIDTH,self.toolbar_height))
        for tool,rect in self.toolbar_buttons.items():
            pygame.draw.rect(self.screen,(100,100,100),rect)
            txt = self.font.render(tool.replace("_"," ").capitalize(),True,(255,255,255))
            self.screen.blit(txt,(rect.x+5,rect.y+5))

        # status + econ
        zx = f"Zoom: {self.camera.zoom:.2f}x"
        st = self.font.render(f"Money:${self.money} | Tool:{self.selected_tool} | {zx}",True,(255,255,255))
        self.screen.blit(st,(10,SCREEN_HEIGHT-self.toolbar_height+35))
        eco = self.font.render(
            f"Pop:{self.econ.population} Jobs:{self.econ.jobs} Inc:${self.econ.income} "
            f"Tax:{int(self.econ.tax_rate*100)}% R-D:{self.econ.residential_demand} "
            f"I-D:{self.econ.industrial_demand}",
            True, (255,255,255)
)
        self.screen.blit(eco,(10,SCREEN_HEIGHT-self.toolbar_height-25))

        pygame.display.flip()

    # ——— Main loop ————————————————————————————————————————————————————
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    Game().run()
