from scipy.spatial import distance
from time import time

from const import *
from ais.base import MOVES, ADJC, AI as BaseAI
from search import astar


class AI(BaseAI):
    NAME = "ExpandAI"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paths = {}

    def update(self, army_updates):
        super().update(army_updates)
        for pid, aid, origin, target in army_updates:
            if pid != self.pid:
                continue

            if target is None:  # Army got destroyed or settled
                try:
                    self.paths.pop(aid)
                except KeyError:
                    pass

            if origin and target is None and self.territories[origin[0], origin[1], 1] == self.pid:  # Occupied new territory
                x, y = origin
                try:
                    self.borders.remove((x, y))
                except KeyError:
                    pass
                for mx, my in MOVES:  # Add all bordering territories to borders, as they are now valid
                    bx, by = mx + x, my + y
                    if not (0 <= bx < self.territories.shape[0] and 0 <= by < self.territories.shape[1]):
                        continue
                    if self.territories[bx, by, 1] != self.pid and self.territories[bx, by, 0] == OCCUPIABLE:
                        self.borders.add((bx, by))
        self.update_borders(army_updates)

        own_armies = self.armies[self.pid]
        for aid, (ax, ay) in own_armies.items():
            try:
                path = self.paths[aid]
            except KeyError:
                borders = sorted(
                    (
                        (
                            distance.euclidean((ax, ay), border),
                            distance.euclidean(self.center, border)
                        ),
                        self.territories[border[0], border[1], 1] == self.pid,
                        border
                    ) for border in self.borders
                )
                target = borders[0][2]
                # _start = time()
                path = astar((ax, ay), target, self.astar_wall_check)
                # _time = round(time()-_start, 4)
                # print("A* took", _time, "seconds")
                if not path:
                    raise ValueError(f"Could not generate path with start ({ax}, {ay}) and end ({target})!")
                self.paths[aid] = path
            x, y = path.pop(0)
            if not self.paths[aid]:
                self.paths.pop(aid)
            yield aid, x, y  # Move army with index "i" to x, y with size "n"

    def update_borders(self, army_updates):
        # if not self.borders:
        #     for x, y in self.land[self.pid]:
        #         for mx, my in MOVES:  # Add all bordering territories of current land
        #             bx, by = mx + x, my + y
        #             if not (0 <= bx < self.territories.shape[0] and 0 <= by < self.territories.shape[1]):
        #                 continue
        #             if self.territories[bx, by, 1] != self.pid and self.territories[bx, by, 0] == OCCUPIABLE:
        #                 self.borders.add((bx, by))
        # else:
        for x, y in self.borders.copy():
            # else:  # Not owned by me
            for mx, my in MOVES:  # Check if still valid border
                bx, by = mx + x, my + y
                if not (0 <= bx < self.territories.shape[0] and 0 <= by < self.territories.shape[1]):
                    continue
                if self.territories[bx, by, 1] == self.pid:
                    break  # Border still valid
            else:  # Border not valid anymore
                for mx, my in MOVES:
                    bx, by = mx + x, my + y
                    if self.is_valid_border(bx, by):
                        self.borders.add((bx, by))

    def is_valid_border(self, x, y):
        if self.territories[x, y, 0] != OCCUPIABLE:
            return False
        for mx, my in MOVES:
            bx, by = mx + x, my + y
            if not (0 <= bx < self.territories.shape[0] and 0 <= by < self.territories.shape[1]):
                continue
            if self.territories[bx, by, 1] == self.pid:
                return True
        return False

    def astar_wall_check(self, x, y):
        outside_map = not (0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1])
        return outside_map or self.territories[x, y, 0] == IMPASSABLE