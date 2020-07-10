
# pop limit = POP_BASE + log(1 + territories * POP_HEIGHT) * POP_WIDTH
POP_BASE = 1
POP_HEIGHT = .001  # The smaller the number, the faster pop limit goes up
POP_WIDTH = 30  # The bigger the number, the longer it takes to hit maximum of possible pop limit
POP_GROWTH = .002  # Growth per territory
POP_REDUCTION = .000000005  # Exponential reduction per territory
BATTLE_MAX_ROLL = 100
SUCCESS_COLONIZING_CHANCE = .9
