from collections import namedtuple

import numpy as np

from const import *
from ais.base import MOVES, AI as BaseAI


#cdef class Pos:
#    cdef public int x
#    cdef public int y
#
#    def __init__(self, x, y):
#        self.x = x
#        self.y = y
#
#
#cdef class Node:
#    cdef public Pos pos
#    cdef public Node parent
#    cdef public list children
#
#    def __init__(self, pos, parent, children):
#        self.pos = pos
#        self.parent = parent
#        self.children = children


Node = namedtuple('Node', ('pos', 'parent', 'children'))
cdef tuple BIN = (1, 2, 4, 8)


class AI(BaseAI):
    NAME = "ExpandAI"

    def __init__(self, pid, color, territories):
        super().__init__(pid, color, territories)
        self.borders = set()
        self.paths = {}
        self.search_buffer = np.zeros((*territories.shape[:2], 1), dtype=np.int16)

    def update(self, army_updates):
        super().update(army_updates)

        own_armies = self.armies[self.pid]
        for aid, (ax, ay) in own_armies.items():
            try:
                path = self.paths[aid]
            except KeyError:
                path = self.find_path(ax, ay)
                self.paths[aid] = path
            x, y = path.pop(0)
            if not self.paths[aid]:
                self.paths.pop(aid)
            yield aid, x, y

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

        while self.territories[x, y, 1] == self.pid or self.territories[x, y, 0] == PASSABLE:
            node = nodes.pop(0)
            x, y = node.pos
            has_valid_node = False
            for i, (ox, oy) in enumerate(MOVES):
                rx, ry = x + ox, y + oy
                if self.is_impassable(rx, ry):
                    continue
                b = self.search_buffer[rx, ry, 0]
                if BIN[i] | b == b:  # Means that path is closed
                    continue
                if (rx, ry) in checked_nodes:
                    has_valid_node = True
                    continue
                nodes.append(Node(pos=(rx, ry), parent=node, children=[]))
                has_valid_node = True
                checked_nodes.add((rx, ry))

            if not has_valid_node:
                # ToDo: If starting node has no possible ways to go, it will result in an error on the next line
                # ToDo: Keep an eye on this
                rx, ry = x - node.parent.pos[0], y - node.parent.pos[1]
                self.search_buffer[x, y, 0] |= BIN[MOVES.index((rx, ry))]  # Add blocking direction

        path = []
        while node.parent:
            path.append(node.pos)
            node = node.parent
        if not path:
            x, y = start_node.pos
            raise ValueError("Path should never be empty.")
        path.reverse()
        return path

    def is_impassable(self, int x, int y):
        return (
            (not (0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1])) or
            (self.territories[x, y, 0] == IMPASSABLE)
        )