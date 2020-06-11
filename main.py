import random
from copy import deepcopy
from time import time
from collections import deque
from uuid import uuid4

import numpy as np
from PIL import Image
import noise
from kivy.app import App
from kivy.config import Config
from kivy.clock import Clock
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from const import *
import utils


class GameApp(App):
    title = "PixelWars"

    def __init__(self, map_path, players):
        super().__init__()
        self.army_updates = []
        base_map = Image.open(map_path).convert('RGB')
        self.map = Image.new('RGBA', base_map.size, (0, 0, 0, 0))
        base_map_px = base_map.load()
        self.map_px = self.map.load()

        free_spawns = []
        # territories: terrain type, occupant
        self.territories = np.zeros((base_map.height, base_map.width, 2), dtype=np.int16)
        for x in range(self.territories.shape[0]):
            for y in range(self.territories.shape[1]):
                if base_map_px[y, x] in (STRAIT, DESERT):
                    self.territories[x, y] = (PASSABLE, -1)
                elif base_map_px[y, x] == LAND:
                    self.territories[x, y] = (OCCUPIABLE, -1)
                    free_spawns.append((x, y))
                else:
                    self.territories[x, y] = (IMPASSABLE, -1)
        for x in range(base_map.size[0]):
            for y in range(base_map.size[1]):
                v = base_map_px[x, y]
                n = noise.snoise2(x*.01, y*.01, octaves=8, persistence=.7, lacunarity=2.) + 1
                try:
                    r, g, b = utils.mix_colors(COLORS[v][0], COLORS[v][1], n)
                except KeyError:
                    print('No colors found for', v)
                    continue
                base_map_px[x, y] = int(r), int(g), int(b)

        self.armies = [{} for _ in players]
        self.land = [set() for _ in players]

        self.players_scores = [0 for _ in players]
        self.players = tuple(AI(i, color, deepcopy(self.territories)) for i, (AI, color) in enumerate(players))
        for i, player in enumerate(self.players):
            x, y = random.choice(free_spawns)
            free_spawns.remove((x, y))
            self.spawn_army(i, x, y)

        self.tps = deque(maxlen=50)
        self.eps = [deque(maxlen=50) for _ in players]  # AI executions per second

        base_map.save('temp/base_map.png')
        self.map.save('temp/map.png')

    def build(self):
        super().build()
        self.root.ids.base_map.source = 'temp/base_map.png'
        self.root.ids.map.source = 'temp/map.png'
        for player in self.players:
            name = player.NAME
            self.root.ids.ai_names.text += f"[color=%02x%02x%02x]{name}[/color]\n" % player.color
        Clock.schedule_interval(app.tick, 0)

    def tick(self, dt):
        print('########################')
        _start_t = time()
        self.root.ids.eps.text = ''
        self.root.ids.territories.text = ''
        self.root.ids.units.text = ''

        # Update Map
        _s = time()
        for pid, aid, origin, target in self.army_updates:
            if not origin:
                continue
            x, y = origin
            if self.territories[x, y, 1] == pid:
                color = self.players[pid].color + (200,)
            else:
                color = (0, 0, 0, 0)
            self.map_px[y, x] = color
        for pid, player in enumerate(self.players):
            color = self.players[pid].unit_color + (200,)
            for x, y in self.armies[pid].values():
                self.map_px[y, x] = color

        self.map.save('temp/map.png')
        self.root.ids.map.reload()
        print("Update map took:", time()-_s, "for", len(self.army_updates), "updates and", sum(len(armies) for armies in self.armies))

        # Spawn player armies
        _s = time()
        for pid, player in enumerate(self.players):
            for x, y in self.land[pid]:
                if len(self.armies[pid]) >= HARD_ARMY_LIMIT:
                    break  # ToDo: replace with inverse exponential for spawning chance over time
                if pid < 0:
                    continue
                if random.random() <= ARMY_SPAWN_CHANCE:
                    self.spawn_army(pid, x, y)
        print("Spawn player armies took:", time()-_s)

        _s = time()
        # Update players and get their movement orders
        army_updates = deepcopy(self.army_updates)
        self.army_updates.clear()
        total_moves = []

        for pid, player in enumerate(self.players):
            updates = deepcopy(army_updates)
            _start_p = time()
            moves = player.update(updates)
            for aid, x, y in moves:
                total_moves.append((pid, aid, x, y))
            eps = time() - _start_p
            self.eps[pid].append(1. / eps)
            eps = round(sum(self.eps[pid]) / len(self.eps[pid]))
            self.root.ids.territories.text += f"[color=%02x%02x%02x]{self.players_scores[pid]}[/color]\n" % player.color
            self.root.ids.units.text += f"[color=%02x%02x%02x]{len(self.armies[pid])}[/color]\n" % player.color
            self.root.ids.eps.text += f"[color=%02x%02x%02x]{eps}[/color]\n" % player.color
            # self.root.ids.units.text += f"[color=%02x%02x%02x]{}[/color]\n" % player.color
        print("Update players took:", time()-_s)

        _s = time()
        # Process player movement orders
        random.shuffle(total_moves)
        while total_moves:
            pid, aid, x, y = total_moves.pop(0)
            # Check if move is valid
            if self.territories[x, y, 0] not in (OCCUPIABLE, PASSABLE):
                raise ValueError(f"Player {pid} cannot move army {aid} to {x}, {y} (Not passable)")
            # ToDo: add check so armies can only walk one tile
            owner = self.territories[x, y, 1]
            allied_coord = self.armies[pid][aid]
            if owner == -1:  # Territory without owner
                self.move_army(pid, aid, allied_coord, (x, y))
            elif owner == pid:  # Own territory, simply move army
                self.move_army(pid, aid, allied_coord, (x, y))
            else:  # Occupied by enemy
                enemy_pid = owner
                allied_armies = [aid]
                for pid_, aid_, x_, y_ in total_moves:
                    if pid_ != pid or (x_, y_) != (x, y):
                        continue
                    allied_armies.append(aid_)
                enemy_armies = [uid for coord, uid in self.armies[enemy_pid].items() if coord == (x, y)]
                attacker_roll = sum(random.randint(0, BATTLE_MAX_ROLL) for _ in allied_armies)
                defender_roll = (sum(random.randint(0, BATTLE_MAX_ROLL) for _ in enemy_armies) +
                                 random.randint(0, LOCALS_MAX_ROLL))
                if attacker_roll > defender_roll:  # Win for attacker
                    if enemy_armies:
                        enemy_aid = enemy_armies[0]
                        self.army_updates.append((enemy_pid, enemy_aid, (x, y), None))
                        if len(enemy_armies) == 1:  # Last army was defeated
                            self.armies[pid].pop(aid)
                            for aid_ in allied_armies:
                                self.move_army(pid, aid_, allied_coord, (x, y))
                        self.armies[enemy_pid].pop(enemy_aid)
                            # self.army_updates.append((pid, aid, allied_coord, None))
                            # for aid_ in allied_armies[1:]:
                            #     self.army_updates.append((pid, aid_, allied_coord, (x, y)))
                            # self.change_owner(x, y, pid)
                else:  # Win for defender (even if attacker and defender roll are the same)
                    self.army_updates.append((pid, aid, allied_coord, None))
        print("Process player moves took:", time()-_s)

        self.tps.append(1. / (time() - _start_t))
        self.root.ids.tps.text = str(round(sum(self.tps) / len(self.tps), 1))

    def change_owner(self, x, y, pid):
        assert self.territories[x, y, 0] == OCCUPIABLE
        previous_owner = self.territories[x, y, 1]
        if previous_owner == pid:
            return previous_owner
        self.land[pid].add((x, y))
        if previous_owner >= 0:
            self.players_scores[previous_owner] -= 1
            self.land[previous_owner].remove((x, y))
        self.territories[x, y, 1] = pid

        self.players_scores[pid] += 1
        return previous_owner

    def spawn_army(self, pid, x, y):
        assert self.territories[x, y, 0] in (OCCUPIABLE, PASSABLE)
        uid = uuid4()
        self.army_updates.append((pid, uid, None, (x, y)))
        if self.territories[x, y, 1] != pid:
            self.change_owner(x, y, pid)
            self.army_updates.append((pid, uid, (x, y), None))
        else:
            self.armies[pid][uid] = (x, y)

    def move_army(self, pid, aid, origin, target):
        assert target is not None
        assert self.territories[target[0], target[1], 0] in (OCCUPIABLE, PASSABLE)
        self.army_updates.append((pid, aid, origin, target))
        self.armies[pid][aid] = target

        if self.territories[target[0], target[1], 0] == OCCUPIABLE and self.territories[target[0], target[1], 1] != pid:
            self.change_owner(*target, pid)
            self.army_updates.append((pid, aid, target, None))
            self.armies[pid].pop(aid)


if __name__ == '__main__':
    from ais.random import AI as RandomAI
    from ais.expand import AI as ExpandAI
    app = GameApp(
        map_path='assets/maps/europe1.png',
        players=(
            (RandomAI, (255, 0, 0)),
            (RandomAI, (255, 255, 0)),
            (RandomAI, (255, 0, 255)),
            (RandomAI, (0, 150, 0)),
            (RandomAI, (158, 66, 255)),
            (RandomAI, (150, 0, 0)),
        )
    )
    app.run()
