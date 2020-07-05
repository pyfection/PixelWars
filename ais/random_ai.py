import random

from scipy.spatial import distance

from const import IMPASSABLE
from ais.base_c import MOVES, AI as BaseAI


TARGET_RANGE = 100


class AI(BaseAI):
    NAME = "RandomAI"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.targets = {}

    def update(self, army_updates):
        super().update(army_updates)
        for pid, aid, origin, target in army_updates:
            if pid == self.pid and target is None:  # Army got destroyed or settled
                try:
                    self.targets.pop(aid)
                except KeyError:
                    pass

        own_armies = self.armies[self.pid]
        for aid, (ax, ay) in own_armies.items():
            try:
                target = self.targets[aid]
            except KeyError:
                target = ax + random.randint(-TARGET_RANGE, TARGET_RANGE), ay + random.randint(-TARGET_RANGE, TARGET_RANGE)
                self.targets[aid] = target

            target_d = distance.euclidean((ax, ay), target)
            closest = None
            closest_d = None
            closest_empty = False

            tiles = []
            for ox, oy in MOVES:
                x, y = ax + ox, ay + oy
                if not (0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1]):
                    continue
                if self.territories[x, y, 0] == IMPASSABLE:
                    continue
                if closest_empty and not self.territories[x, y, 1] != self.pid:
                    # If it already had found a territory which is not occupied by self,
                    # then ignore this one if it is occupied by self
                    continue

                if not closest_empty and self.territories[x, y, 1] != self.pid:  # Prefer not occupied by self
                    closest = (x, y)
                else:  # current and closest territory are either both empty or neither of them
                    d = distance.euclidean((x, y), target)
                    if d_ < d:
                        tiles.append((d_, (x, y)))
            if tiles:
                tiles.sort()
                x, y = tiles[0][1]
            else:
                self.targets.pop(aid)
                continue
            yield aid, x, y  # Move army to x, y
