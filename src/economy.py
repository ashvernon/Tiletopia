# src/economy.py
from config import TILE_SIZE

class Economy:
    def __init__(self, tax_rate=0.10):
        self.tax_rate = tax_rate
        self.population = 0
        self.jobs = 0
        self.income = 0
        self.residential_demand = 0
        self.industrial_demand = 0
        self.happiness = 1.0

    def update(self, grid):
        # count tiles
        houses = sum(row.count("house") for row in grid)
        factories = sum(row.count("factory") for row in grid)

        self.population = houses * 10
        self.jobs = factories * 5
        per_capita = 2
        self.income += int(self.population * per_capita * self.tax_rate)

        self.industrial_demand = 1 if self.jobs < self.population else 0
        self.residential_demand = 1 if houses < (self.jobs // 5) else 0

        if self.population>0:
            self.happiness = min(self.jobs/self.population,1.0)
        else:
            self.happiness = 1.0
