

from PIL import Image
import numpy as np
import noise

from const import MAP, SEA, SEA_ROUTE, GRASS, DESERT, FOREST, MOUNTAIN


MAP = {value: key for key, value in MAP.items()}


BIOMES = {
    'rainforest': ((FOREST, 1, 1),),
    'desert': ((DESERT, 1, 1), (SEA_ROUTE, .4, 1)),
    'grassland': ((GRASS, 1, 1),),
    'temperate forest': ((GRASS, 1, 1), (FOREST, 1, 7)),
    'mediterranean': ((GRASS, 1, 1), (FOREST, .5, 7)),
    'taiga': ((GRASS, .5, 1), (FOREST, 1, 7))
}

class Generator:
    def __init__(self, seed=0, octaves=8, magnitude=.005):
        self.seed = seed
        self.octaves = octaves
        self.magnitude = magnitude
        self.mountain_level = 0.7
        self.deep_sea_level = 0.35
        self.nav_sea_level = 0.5

    def get_height(self, x, y):
        h = noise.snoise3(x * self.magnitude, y * self.magnitude, self.seed, octaves=self.octaves)
        return h * .5 + .5

    def get_biome(self, x, y):
        biomes = tuple(b for b in BIOMES.keys())
        values = []
        for i, b in enumerate(biomes, 1):
            magnitude = self.magnitude
            v = noise.snoise3(x * magnitude, y * magnitude, self.seed+i, octaves=self.octaves)
            values.append(v)
        i = values.index(max(values))
        return biomes[i]

    def get_terrain_type(self, x, y):
        biome = self.get_biome(x, y)
        terrains = tuple(t[0] for t in BIOMES[biome])
        biomes_mods = tuple(t[1] for t in BIOMES[biome])
        biomes_mags = tuple(t[2] for t in BIOMES[biome])
        values = []
        for i, b in enumerate(terrains):
            magnitude = self.magnitude * biomes_mags[i]
            v = noise.snoise3(x * magnitude, y * magnitude, self.seed+b+10, octaves=self.octaves)
            v = v * .5 + .5
            values.append(v * biomes_mods[i])
        i = values.index(max(values))
        return terrains[i]

    def get_map(self, width, height):
        img = Image.new('RGB', (width, height))
        img_px = img.load()

        for x in range(width):
            for y in range(height):
                h = self.get_height(x, y)
                if h > self.mountain_level:
                    color = MAP[MOUNTAIN]
                elif h > self.nav_sea_level:
                    color = MAP[self.get_terrain_type(x, y)]
                elif h > self.deep_sea_level:
                    color = MAP[SEA_ROUTE]
                else:
                    color = MAP[SEA]
                img_px[x, y] = color
        return img


if __name__ == "__main__":
    from random import randint
    g = Generator(randint(0, 100))
    m = g.get_map(480, 270)
    m.show()
