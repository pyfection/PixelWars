
from collections import namedtuple
from random import shuffle

import numpy as np

from const import TERRAIN, SPEED, ENTER_SPEED, POP_VAL, DEFENCE_MOD, ATTACK_MOD, HAZARD, DEFAULT_HAZARD, DEFAULT_DEFENCE_MOD, DEFAULT_ATTACK_MOD
from ais.base_c import MOVES, ADJC, AI as BaseAI


MOVES = list(MOVES)

Node = namedtuple('Node', ('pos', 'parent', 'children', 'dist'))


class AI(BaseAI):
    NAME = "HunterAI"
    DETECTION_RADIUS = 5
    MIN_RELATIVE_STRENGTH_ATTACK = 1.5  # times amount of own units stronger with attacker bonus compared to defender
    MIN_RELATIVE_STRENGTH_DEFEND = 1.5
    CAUTION = 20000  # Terrain hazardousness times CAUTION is added to path finding cost
    MIN_ALLIES_IN_RANGE = 2

    def __init__(self, pid, name, color, territories):
        super().__init__(pid, name, color, territories)
        self.paths = {}
        self.blocked_paths = np.zeros(self.territories.shape[:2])

    def update(self, army_updates):
        super().update(army_updates)

        own_armies = self.armies[self.pid]

        for aid, (ax, ay) in own_armies.items():
            shuffle(MOVES)

            # Tries colonizing
            if self.territories[ax, ay, 1] == -1 and TERRAIN[self.territories[ax, ay, 0]][POP_VAL] > 0:
                # Colonize
                self.paths.pop(aid, None)
                yield aid, None
                continue

            # Tries to stalk enemy
            enemies = sorted(
                (
                    (eaid, (ex, ey), abs(ex - ax) + abs(ey - ay))
                    for epid, enemy_army in self.armies.items()
                    for eaid, (ex, ey) in enemy_army.items()
                    if abs(ex - ax) + abs(ey - ay) <= self.DETECTION_RADIUS and epid != self.pid
                ),
                key=lambda k: k[-1]
            )
            try:
                enemy = enemies[0]
            except IndexError:
                enemy = None
            if enemy:
                eaid, (ex, ey), dist = enemy

                allies = tuple(
                    eaid
                    for eaid, (ex, ey) in self.armies[self.pid].items()
                    if abs(ex - ax) + abs(ey - ay) <= self.DETECTION_RADIUS
                )
                relative_attack_strength = len(allies) / self.MIN_RELATIVE_STRENGTH_ATTACK
                if relative_attack_strength * TERRAIN[self.territories[ax, ay, 0]].get(ATTACK_MOD, DEFAULT_ATTACK_MOD) >= len(enemies) * TERRAIN[self.territories[ex, ey, 0]].get(DEFENCE_MOD, DEFAULT_DEFENCE_MOD) or len(own_armies) >= self.max_pop * .8:
                    # If hunters are at least twice as many as detected enemies, then attack
                    pass
                elif dist <= 4 and (len(allies) * TERRAIN[self.territories[ax, ay, 0]].get(DEFENCE_MOD, DEFAULT_DEFENCE_MOD)) / self.MIN_RELATIVE_STRENGTH_DEFEND >= len(enemies) * TERRAIN[self.territories[ex, ey, 0]].get(ATTACK_MOD, DEFAULT_ATTACK_MOD):
                    # Army has good chance of winning a defensive battle, staying
                    self.paths.pop(aid, None)
                    continue
                else:
                    if dist <= 2:
                        # Run from enemy
                        x, y = sorted(
                            (
                                ((ox + ax, oy + ay), abs(ox + ax - ex) + abs(oy + ay - ey))
                                for ox, oy in MOVES
                                if self.is_passable(ox + ax, oy + ay)
                            ),
                            key=lambda k: k[-1],
                            reverse=True
                        )[0][0]
                        self.paths.pop(aid, None)
                        yield aid, (x, y)
                        continue
                    elif dist <= 4:
                        # Wait for reinforcements
                        self.paths.pop(aid, None)
                        continue
                    # else far enough away from enemy to move closer
                path = self.find_path(ax, ay, (ex, ey))
                try:
                    x, y = path[0]
                except IndexError:
                    raise IndexError(f"Path is empty for starting pos ({ax}, {ay})")
                self.paths.pop(aid, None)
                yield aid, (x, y)
                continue

            # Tries to find adjacent territory which is passable, occupiable and not occupied by self
            target_moves = []
            for i, (ox, oy) in enumerate(MOVES):
                rx, ry = ax + ox, ay + oy
                if not self.is_passable(rx, ry):
                    continue
                if TERRAIN[self.territories[rx, ry, 0]][POP_VAL] <= 0:
                    continue
                if self.territories[rx, ry, 1] == self.pid:
                    continue
                # Number of adjacent owned territories
                a = sum(1 for ox_, oy_ in ADJC if self.is_passable(rx+ox_, ry+oy_) and self.territories[rx+ox_, ry+oy_, 1] == self.pid)
                e = int(self.territories[rx, ry, 1] not in (self.pid, -1))
                s = TERRAIN[self.territories[rx, ry, 0]][SPEED]
                target_moves.append((a, e, s, i))
            if target_moves:
                # Check if there are enough nearby allies to keep pushing
                self.paths.pop(aid, None)
                ox, oy = MOVES[sorted(target_moves, reverse=True)[0][-1]]
                x, y = ax + ox, ay + oy
                if self.territories[x, y, 1] not in (self.pid, -1):
                    allies = tuple(
                        eaid
                        for eaid, (ex, ey) in self.armies[self.pid].items()
                        if abs(ex - ax) + abs(ey - ay) <= self.DETECTION_RADIUS
                    )
                    if len(allies) <= self.MIN_ALLIES_IN_RANGE:
                        continue
                yield aid, (x, y)
                continue

            # Tries to get saved path
            else:
                try:
                    path = self.paths[aid]
                    if path[0] == (ax, ay):
                        path.pop(0)
                        if not path:
                            self.paths.pop(aid)
                            raise KeyError
                    yield aid, path[0]
                    continue
                except KeyError:
                    pass

            # If everything else fails, find a path
            path = self.find_path(ax, ay)
            self.paths[aid] = path

            try:
                x, y = path[0]
            except IndexError:
                # Can't find territory to conquer
                raise IndexError(f"Path is empty for starting pos ({ax}, {ay})")
            yield aid, (x, y)

    def find_path(self, x, y, target=None):
        start_node = Node(pos=(x, y), parent=None, children=[], dist=0)
        nodes = [start_node]
        checked_nodes = np.zeros(self.territories.shape[:2])

        while True:
            node = nodes.pop(0)
            x, y = node.pos
            if self.territories[x, y, 1] != self.pid and TERRAIN[self.territories[x, y, 0]][POP_VAL] > 0:
                break

            walls_num = 0
            for i, (ox, oy) in enumerate(MOVES):
                rx, ry = x + ox, y + oy
                if node.parent and node.parent.pos == (rx, ry):
                    continue
                if not self.is_passable(rx, ry):
                    walls_num += 1
                    continue
                if self.blocked_paths[rx, ry] == 1:
                    walls_num += 1
                    continue
                if checked_nodes[rx, ry]:
                    # once all nodes around a node have been checked, current node could be removed from checked, right?
                    continue
                n_terrain = self.territories[x, y, 0]
                c_terrain = self.territories[rx, ry, 0]
                s = TERRAIN[c_terrain][SPEED]
                dist = node.dist
                dist += 1 / (s if n_terrain == c_terrain else TERRAIN[c_terrain].get(ENTER_SPEED, s))
                if self.territories[rx, ry, 1] in (self.pid, -1):
                    # Prefering enemy territory
                    dist += 100
                if self.territories[rx, ry, 1] != self.pid:
                    dist += self.CAUTION * TERRAIN[c_terrain].get(HAZARD, DEFAULT_HAZARD)
                if target:
                    dist += abs(target[0] - rx) + abs(target[1] - ry)
                nodes.append(Node(pos=(rx, ry), parent=node, children=[], dist=dist))
                checked_nodes[rx, ry] = 1
            nodes.sort(key=lambda n: n.dist)
            if walls_num >= 2 and TERRAIN[self.territories[x, y, 0]][POP_VAL] <= 0:
                self.blocked_paths[x, y] = 1

        path = []
        while node.parent:
            path.append(node.pos)
            node = node.parent
        if not path:
            x, y = start_node.pos
            raise ValueError(f"Path should never be empty. [({x}, {y}), {self.pid}]")
        path.reverse()
        return path

    def is_passable(self, x, y):
        return (
            0 <= x < self.territories.shape[0] and 0 <= y < self.territories.shape[1] and
            TERRAIN[self.territories[x, y, 0]][SPEED] > 0
        )