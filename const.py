LAND = (0, 255, 0)
SEA = (0, 0, 255)
RIVER = (0, 255, 255)
STRAIT = (255, 255, 255)
MOUNTAIN = (0, 0, 0)
DESERT = (255, 255, 0)

IMPASSABLE = 0
PASSABLE = 1
OCCUPIABLE = 2


COLORS = {
    LAND: ((100, 170, 70), (102, 108, 35)),
    SEA: ((105, 120, 220), (70, 70, 200)),
    RIVER: ((105, 120, 220), (40, 150, 110)),
    STRAIT: ((200, 200, 200), (255, 255, 255)),
    MOUNTAIN: ((100, 120, 100), (20, 20, 20)),
    DESERT: ((255, 245, 153), (207, 197, 101)),
}


POP_BASE = 1
POP_GROWTH = .1  # Growth per territory
POP_REDUCTION = .000000005  # Exponential reduction per territory
BATTLE_MAX_ROLL = 10
LOCALS_MAX_ROLL = 4  # Max dice roll for local defenders
HARD_ARMY_LIMIT = 20  # Max armies per player  # ToDo: replace this with a spawn chance decrease over time (inverse exponential)
