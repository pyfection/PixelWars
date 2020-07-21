from time import time
from collections import namedtuple
from random import shuffle

from const import TERRAIN, SPEED, ENTER_SPEED, POP_VAL, HAZARD, DEFAULT_HAZARD
from ais.base_c import MOVES, ADJC, AI as BaseAI


MOVES = list(MOVES)

Node = namedtuple('Node', ('pos', 'parent', 'children', 'dist'))


class AI(BaseAI):
    NAME = "BurstAI"
    LOW_THRESHOLD = .3
    HIGH_THRESHOLD = .45
    CAUTION = 5000
    ADD_COLONIZE_PREFERENCE = 100

    def __init__(self, pid, name, color, territories):
        super().__init__(pid, name, color, territories)
        self.paths = {}
        self.border_armies = 0
        self.threshold_reached = False

    def update(self, army_updates):
        super().update(army_updates)

        own_armies = self.armies[self.pid]
        if self.max_pop:
            if self.threshold_reached and self.border_armies / self.max_pop < self.LOW_THRESHOLD:
                self.threshold_reached = False
            elif not self.threshold_reached and self.border_armies / self.max_pop >= self.HIGH_THRESHOLD:
                self.threshold_reached = True
        self.border_armies = 0

        for aid, (ax, ay) in own_armies.items():
            shuffle(MOVES)

            if self.territories[ax, ay, 1] == -1 and TERRAIN[self.territories[ax, ay, 0]][POP_VAL] > 0:
                # Colonize
                yield aid, None
            else:
                # Tries to find adjacent territory which is passable, occupiable and not occupied by self
                target_moves = []
                for i, (ox, oy) in enumerate(MOVES):
                    rx, ry = ax + ox, ay + oy
                    if self.is_impassable(rx, ry):
                        continue
                    if TERRAIN[self.territories[rx, ry, 0]][POP_VAL] <= 0:
                        continue
                    if self.territories[rx, ry, 1] == self.pid:
                        continue
                    if not self.threshold_reached and self.territories[ax, ay, 1] != -1 and self.territories[rx, ry, 1] != -1:
                        # Waiting at enemy border
                        self.border_armies += 1
                        break
                    # Number of adjacent owned territories
                    a = sum(1 for ox_, oy_ in ADJC if not self.is_impassable(rx+ox_, ry+oy_) and self.territories[rx+ox_, ry+oy_, 1] == self.pid)
                    e = int(self.territories[rx, ry, 1] not in (self.pid, -1))
                    s = TERRAIN[self.territories[rx, ry, 0]][SPEED]
                    target_moves.append((a, e, s, i))
                else:
                    if target_moves:
                        ox, oy = MOVES[sorted(target_moves, reverse=True)[0][-1]]
                        x, y = ax + ox, ay + oy
                        self.paths.pop(aid, None)
                    # Uses pathfinding to find target
                    else:
                        try:
                            path = self.paths[aid]
                            if path[0] == (ax, ay):
                                path.pop(0)
                                if not path:
                                    raise KeyError
                        except KeyError:
                            path = self.find_path(ax, ay)
                            self.paths[aid] = path
                        if not self.paths[aid]:
                            self.paths.pop(aid)
                        try:
                            x, y = path[0]
                        except IndexError:
                            # Can't find territory to conquer
                            print("IndexError, path is empty")
                            continue
                        else:
                            if not self.threshold_reached:
                                tx, ty = path[-1]
                                if self.territories[ax, ay, 1] != -1 and self.territories[x, y, 1] != self.pid and self.territories[tx, ty, 1] not in (self.pid, -1):
                                    # Army waiting at passable terrain
                                    self.border_armies += 1
                                    continue
                    if self.territories[x, y, 1] not in (self.pid, -1):
                        self.border_armies += 1
                    yield aid, (x, y)

    def find_path(self, x, y):
        start_node = Node(pos=(x, y), parent=None, children=[], dist=0)
        nodes = [start_node]
        checked_nodes = {(x, y)}

        while True:
            node = nodes.pop(0)
            x, y = node.pos
            if self.territories[x, y, 1] != self.pid and TERRAIN[self.territories[x, y, 0]][POP_VAL] > 0:
                break

            for i, (ox, oy) in enumerate(MOVES):
                rx, ry = x + ox, y + oy
                if self.is_impassable(rx, ry):
                    continue
                if (rx, ry) in checked_nodes:
                    # once all nodes around a node have been checked, current node could be removed from checked, right?
                    continue
                n_terrain = self.territories[x, y, 0]
                c_terrain = self.territories[rx, ry, 0]
                s = TERRAIN[c_terrain][SPEED]
                dist = 1 / (s if n_terrain == c_terrain else TERRAIN[c_terrain].get(ENTER_SPEED, s))
                if self.territories[rx, ry, 1] != self.pid:
                    dist += self.CAUTION * TERRAIN[c_terrain].get(HAZARD, DEFAULT_HAZARD) + 1
                dist += node.dist
                if not (self.territories[rx, ry, 1] == -1 and TERRAIN[c_terrain][POP_VAL] > 0):
                    dist += self.ADD_COLONIZE_PREFERENCE
                nodes.append(Node(pos=(rx, ry), parent=node, children=[], dist=dist))
                nodes.sort(key=lambda n: n.dist)
                checked_nodes.add((rx, ry))

        path = []
        while node.parent:
            path.append(node.pos)
            node = node.parent
        if not path:
            x, y = start_node.pos
            raise ValueError(f"Path should never be empty. [({x}, {y}), {self.pid}]")
        path.reverse()
        return path

    def is_impassable(self, x, y):
        return (
            (not (0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1])) or
            (TERRAIN[self.territories[x, y, 0]][SPEED] <= 0)
        )