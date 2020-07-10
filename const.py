LAND = 0
SEA = 1
RIVER = 2
STRAIT = 3
MOUNTAIN = 4
DESERT = 5

SPEED = 0
POP_VAL = 1

MAP = {
    (0, 255, 0): LAND,
    (0, 0, 255): SEA,
    (0, 255, 255): RIVER,
    (255, 255, 255): STRAIT,
    (0, 0, 0): MOUNTAIN,
    (255, 255, 0): DESERT
}

TERRAIN = {
    LAND: {
        SPEED: 1.0,
        POP_VAL: 1.0
    },
    SEA: {
        SPEED: 0.0,
        POP_VAL: 0.0
    },
    RIVER: {
        SPEED: 0.0,
        POP_VAL: 0.0
    },
    STRAIT: {
        SPEED: 1.0,
        POP_VAL: 0.0
    },
    MOUNTAIN: {
        SPEED: 0.0,
        POP_VAL: 0.0
    },
    DESERT: {
        SPEED: 0.3,
        POP_VAL: 0.0
    },
}

TERRAIN_COLORS = {
    LAND: ((100, 170, 70), (102, 108, 35)),
    SEA: ((105, 120, 220), (70, 70, 200)),
    RIVER: ((105, 120, 220), (40, 150, 110)),
    STRAIT: ((200, 200, 200), (255, 255, 255)),
    MOUNTAIN: ((100, 120, 100), (20, 20, 20)),
    DESERT: ((255, 245, 153), (207, 197, 101)),
}
DRAW_ALPHA = 150
