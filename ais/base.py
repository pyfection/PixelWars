from const import OCCUPIABLE

MOVES = ((-1, 0), (0, 1), (1, 0), (0, -1))
ADJC = ((-1, -1), (1, 1), (1, -1), (-1, 1))
BORDER_CHECKS = MOVES + ((0, 2), (1, 1), (2, 0), (1, -1), (0, -2), (-1, -1), (-2, 0), (-1, 1), (0, 0))


class AI:
    NAME = "BaseAI"

    def __init__(self, pid, color, territories):
        self.pid = pid  # Player ID
        self.color = color
        self.unit_color = tuple(int(c * .5) for c in color)
        self.territories = territories
        self.land = {}
        self.armies = {}  # {player_id: {army_id: coords}}
        self.center = (0, 0)

    def update(self, army_updates):
        for pid, aid, origin, target in army_updates:
            if pid not in self.armies:
                self.armies[pid] = {}

            if target is None:  # Army got destroyed
                self.armies[pid].pop(aid)
            else:
                self.armies[pid][aid] = target

            if target and self.territories[target[0], target[1], 0] == OCCUPIABLE:
                ppid = self.territories[target[0], target[1], 1]
                self.territories[target[0], target[1], 1] = pid
                try:
                    self.land[ppid].remove(target)
                except KeyError:
                    pass
                try:
                    self.land[pid].add(target)
                except KeyError:
                    self.land[pid] = {target}
