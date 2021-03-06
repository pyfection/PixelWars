MOVES = ((-1, 0), (0, 1), (1, 0), (0, -1))
ADJC = ((-1, -1), (1, 1), (1, -1), (-1, 1))
BORDER_CHECKS = MOVES + ((0, 2), (1, 1), (2, 0), (1, -1), (0, -2), (-1, -1), (-2, 0), (-1, 1), (0, 0))


class AI:
    NAME = "BaseAI"

    def __init__(self, int pid, str name, tuple color, territories):
        self.name = name
        self.pid = pid  # Player ID
        self.color = color
        self.unit_color = tuple(int(c * .5) for c in color)
        self.territories = territories
        self.land = {}
        self.armies = {}  # {player_id: {army_id: coords}}
        self.center = (0, 0)
        self.max_pop = 0  # gets updated directly by game

    def update(self, army_updates):
        for pid, aid, origin, target in army_updates:
            if pid not in self.armies:
                self.armies[pid] = {}

            if target is None:  # Army got destroyed or colonized
                self.armies[pid].pop(aid)
                self.on_army_death(pid, aid)
                if self.territories[origin[0], origin[1], 1] == -1:  # colonized
                    self.territories[origin[0], origin[1], 1] = pid
                    self.on_land_conquest(*origin, -1, pid)
                    try:
                        self.land[pid].add(origin)
                    except KeyError:
                        self.land[pid] = {origin}
                continue

            self.armies[pid][aid] = target
            ppid = self.territories[target[0], target[1], 1]
            if ppid not in (pid, -1):
                self.territories[target[0], target[1], 1] = pid
                self.on_land_conquest(*target, ppid, pid)
                try:
                    self.land[ppid].remove(target)
                except KeyError:
                    pass
                try:
                    self.land[pid].add(target)
                except KeyError:
                    self.land[pid] = {target}

    def on_army_death(self, pid, aid):
        pass

    def on_land_conquest(self, x, y, old_pid, new_pid):
        pass
