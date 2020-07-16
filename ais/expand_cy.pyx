from collections import namedtuple
from random import shuffle

import numpy as np

from const import TERRAIN, SPEED, POP_VAL
from ais.base_c import MOVES, ADJC, AI as BaseAI


MOVES = list(MOVES)

Node = namedtuple('Node', ('pos', 'parent', 'children'))
cdef tuple BIN = (1, 2, 4, 8)


class AI(BaseAI):
    NAME = "ExpandAI"

    def __init__(self, pid, name, color, territories):
        super().__init__(pid, name, color, territories)
        self.paths = {}

    def update(self, army_updates):
        super().update(army_updates)

        own_armies = self.armies[self.pid]
        cdef list target_moves

        for aid, (ax, ay) in own_armies.items():
            shuffle(MOVES)

            if self.territories[ax, ay, 1] == -1 and TERRAIN[self.territories[ax, ay, 0]][POP_VAL] > 0:
                # Colonize
                yield aid, None
            else:
                target_moves = []
                for i, (ox, oy) in enumerate(MOVES):
                    rx, ry = ax + ox, ay + oy
                    if self.is_impassable(rx, ry):
                        continue
                    if TERRAIN[self.territories[rx, ry, 0]][POP_VAL] <= 0:
                        continue
                    if self.territories[rx, ry, 1] != self.pid:
                        a = sum(1 for ox_, oy_ in ADJC if not self.is_impassable(rx+ox_, ry+oy_) and self.territories[rx+ox_, ry+oy_, 1] == self.pid)
                        target_moves.append((a, i))
                if target_moves:
                    ox, oy = MOVES[sorted(target_moves, reverse=True)[0][1]]
                    x, y = ax + ox, ay + oy
                    self.paths.pop(aid, None)
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
                    x, y = path[0]
                    if not self.paths[aid]:
                        self.paths.pop(aid)
                yield aid, (x, y)

    def find_path(self, int x, int y):
        cdef int ox
        cdef int oy
        cdef int rx
        cdef int ry
        cdef int b
        cdef bint has_valid_node
        start_node = Node(pos=(x, y), parent=None, children=[])
        nodes = [start_node]
        node = start_node
        checked_nodes = {(x, y)}

        while self.territories[x, y, 1] == self.pid or TERRAIN[self.territories[x, y, 0]][POP_VAL] <= 0:
            node = nodes.pop(0)
            x, y = node.pos
            has_valid_node = False
            for i, (ox, oy) in enumerate(MOVES):
                rx, ry = x + ox, y + oy
                if self.is_impassable(rx, ry):
                    continue
                if (rx, ry) in checked_nodes:
                    has_valid_node = True
                    continue
                nodes.append(Node(pos=(rx, ry), parent=node, children=[]))
                has_valid_node = True
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

    def is_impassable(self, int x, int y):
        return (
            (not (0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1])) or
            (TERRAIN[self.territories[x, y, 0]][SPEED] <= 0)
        )