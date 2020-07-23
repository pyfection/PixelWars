GRASS = 0
SEA = 1
SEA_ROUTE = 2
BRIDGE = 3
MOUNTAIN = 4
DESERT = 5
FOREST = 6

SPEED = 0
POP_VAL = 1
ENTER_SPEED = 2
DEFENCE_MOD = 3
ATTACK_MOD = 4
HAZARD = 5

DEFAULT_HAZARD = 1/5000
DEFAULT_DEFENCE_MOD = 1.5
DEFAULT_ATTACK_MOD = 1

MAP = {
    (0, 255, 0): GRASS,
    (0, 0, 255): SEA,
    (0, 255, 255): SEA_ROUTE,
    (0, 100, 0): BRIDGE,
    (0, 0, 0): MOUNTAIN,
    (255, 255, 0): DESERT,
    (0, 100, 0): FOREST,
}

TERRAIN = {
    GRASS: {
        SPEED: 0.7,
        POP_VAL: 1.0
    },
    SEA: {
        SPEED: 0.0,
        POP_VAL: 0.0,
    },
    SEA_ROUTE: {
        SPEED: 1.0,
        POP_VAL: 0.0,
        ENTER_SPEED: 0.07,
        ATTACK_MOD: 0.5,
        DEFENCE_MOD: 1.0,
        HAZARD: 1/500
    },
    BRIDGE: {
        SPEED: 0.7,
        POP_VAL: 0.0,
        ATTACK_MOD: 0.5,
        DEFENCE_MOD: 2.0
    },
    MOUNTAIN: {
        SPEED: 0.0,
        POP_VAL: 0.0,
        ATTACK_MOD: 1.5,
        DEFENCE_MOD: 2.0
    },
    DESERT: {
        SPEED: 0.2,
        POP_VAL: 0.0,
        HAZARD: 1/500
    },
    FOREST: {
        SPEED: 0.2,
        POP_VAL: 0.5,
        ATTACK_MOD: 0.7,
        DEFENCE_MOD: 1.5
    },
}

TERRAIN_COLORS = {
    GRASS: ((100, 170, 70), (102, 108, 35)),
    SEA: ((60, 90, 175), (40, 55, 160)),
    SEA_ROUTE: ((70, 110, 210), (60, 80, 200)),
    BRIDGE: ((115, 74, 29), (89, 58, 23)),
    MOUNTAIN: ((100, 120, 100), (20, 20, 20)),
    DESERT: ((255, 245, 153), (207, 197, 101)),
    FOREST: ((25, 80, 0), (0, 35, 0)),
}
BORDER_ALPHA = 0.8  # Lower number makes color of occupied territories more seethrough
OCCUPIED_ALPHA = 0.3

MOVES = ((-1, 0), (0, 1), (1, 0), (0, -1))
ADJC = ((-1, -1), (1, 1), (1, -1), (-1, 1))
BORDER = MOVES + ADJC + ((0, 2), (2, 0), (0, -2), (-2, 0))
