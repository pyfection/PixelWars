"""
AntAI is inspired by how ants work in real life, by using pheromones to guide them.
This AI works, but has been abandoned as it doesn't provide great amounts of speed improvement
and performs a lot worse than the basic ExpandAI, as it has to establish the pheromone trails first,
which costs a lot of time.
Thus this AI has been abandoned.
"""

from random import random

import numpy as np

from const import TERRAIN, SPEED, ENTER_SPEED, POP_VAL, HAZARD, DEFAULT_HAZARD
from ais.base_c import MOVES, ADJC, AI as BaseAI


class AI(BaseAI):
    NAME = "AntAI"
    PHEROMONE_DECAY = 0.99

    def __init__(self, pid, name, color, territories):
        super().__init__(pid, name, color, territories)
        self.targets = {}
        self.ticks = 0
        self.pheromones = np.zeros((*territories.shape[:2], 2))
        self._start_phase_over = False

    def update(self, army_updates):
        super().update(army_updates)

        self.ticks += 1
        own_armies = self.armies[self.pid]
        # if own_armies:
            # print("\n\nCurrent tick:", self.ticks)

        for aid, (ax, ay) in own_armies.items():
            # print(f"\n- Processing {aid} at ({ax}, {ay}) -")
            if self.territories[ax, ay, 1] == -1 and TERRAIN[self.territories[ax, ay, 0]][POP_VAL] > 0:
                # print("Colonizing")
                # Colonize
                yield aid, None
                continue

            try:
                x, y = self.targets[aid]
            except KeyError:
                pass
            else:
                if (ax, ay) == (x, y):
                    self.targets.pop(aid)
                else:
                    # print("Already had target saved as", x, y)
                    yield aid, (x, y)
                    continue

            ticks_passed = self.ticks - self.pheromones[ax, ay, 1]
            # print("Ticks passed on current field:", ticks_passed)
            self.pheromones[ax, ay, 1] = self.ticks
            decay = self.PHEROMONE_DECAY ** ticks_passed
            self.pheromones[ax, ay, 0] *= decay
            # print("Pheromones on current field:", self.pheromones[ax, ay, 0])
            moves = []
            for i, (ox, oy) in enumerate(MOVES):
                rx, ry = ax + ox, ay + oy
                if not self.is_passable(rx, ry):
                    continue
                pop_val = TERRAIN[self.territories[rx, ry, 0]][POP_VAL]
                if self.territories[rx, ry, 1] != self.pid and (pop_val > 0 or self.pheromones[rx, ry, 0] == 0):
                    a = sum(
                            1 for ox_, oy_ in ADJC
                            if self.is_passable(rx + ox_, ry + oy_) and
                            self.pheromones[rx, ry, 0] > 0
                            # self.territories[rx + ox_, ry + oy_, 1] == self.pid

                    )
                    pheromone = self.pheromones[rx, ry, 0] = 100
                else:
                    a = 0
                    ticks_passed = self.ticks - self.pheromones[rx, ry, 1]
                    decay = self.PHEROMONE_DECAY ** ticks_passed
                    self.pheromones[rx, ry, 0] *= decay
                    pheromone = self.pheromones[rx, ry, 0]

                self.pheromones[rx, ry, 1] = self.ticks
                moves.append((a, pheromone, pop_val, random(), (rx, ry)))
            moves.sort(reverse=True)
            # print("Possible moves:", moves)
            x, y = moves[0][-1]
            if self.pheromones[x, y, 0] <= self.pheromones[ax, ay, 0]:
                # Has reached a dead end and has to go back
                # print("Reached dead end")
                self.pheromones[ax, ay, 0] = -1
                self.pheromones[x, y, 0] = 100
            self.targets[aid] = (x, y)
            yield aid, (x, y)

    def is_passable(self, x, y):
        return (
            (0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1]) and
            TERRAIN[self.territories[x, y, 0]][SPEED] > 0
        )