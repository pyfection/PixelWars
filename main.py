from math import modf, log
import random
from array import array
from copy import deepcopy
from time import time
from collections import deque
from uuid import uuid4

import numpy as np
from PIL import Image
from kivy.app import App
from kivy.config import Config
from kivy.clock import Clock
from kivy.graphics.texture import Texture
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'window_state', 'maximized')

from const import *
import utils


class GameApp(App):
    title = "PixelWars"

    def __init__(self, map_path, players):
        super().__init__()
        self.map_path = map_path
        self.army_updates = []

        base_map = Image.open(self.map_path).convert('RGB')
        self.map_size = base_map.width, base_map.height
        base_map_px = base_map.load()
        # territories: terrain type, occupant
        self.territories = utils.territories_from_map(base_map_px, self.map_size)
        free_spawns = [
            (x, y)
            for x in range(self.map_size[0])
            for y in range(self.map_size[1])
            if self.territories[x, y, 0] == OCCUPIABLE
        ]
        utils.prettify_map(base_map, base_map_px)

        self.armies = [{} for _ in players]
        self.land = [set() for _ in players]

        self.players_scores = [0 for _ in players]
        self.players_armies_excess = [0 for _ in players]
        self.players = tuple(AI(i, color, deepcopy(self.territories)) for i, (AI, color) in enumerate(players))
        for i, player in enumerate(self.players):
            x, y = random.choice(free_spawns)
            free_spawns.remove((x, y))
            for _ in range(20):
                self.spawn_army(i, x, y)

        self.history = {
            'map': self.map_path,
            'players': [{'color': p.color, 'unit_color': p.unit_color} for p in self.players],
            'history': []
        }

        self.tps = deque(maxlen=50)
        self.eps = [deque(maxlen=50) for _ in players]  # AI executions per second

        base_map.save('temp/base_map.png')

    def build(self):
        super().build()
        self.root.ids.base_map.source = 'temp/base_map.png'
        self.root.ids.map.size = self.root.ids.base_map.size
        self.map = Texture.create(size=self.root.ids.base_map.texture_size)
        size = self.map_size[0] * self.map_size[1] * 4
        self.map_px = [0 for _ in range(size)]
        self.map_px = array('B', self.map_px)
        self.map.blit_buffer(self.map_px, colorfmt='rgba', bufferfmt='ubyte')
        self.root.ids.map.texture = self.map
        self.root.ids.ai_names.text = 'AI Type\n'
        for player in self.players:
            name = player.NAME
            self.root.ids.ai_names.text += f"[color=%02x%02x%02x]{name}[/color]\n" % player.color
        Clock.schedule_interval(app.tick, 0)

    def tick(self, dt):
        # print('########################')
        _start_t = time()
        self.root.ids.eps.text = 'EPS\n'
        self.root.ids.territories.text = 'Territories\n'
        self.root.ids.units.text = 'Units\n'
        self.root.ids.max_pops.text = 'Max Pop\n'

        # Update Map
        _s = time()
        clear_color = array('B', (0, 0, 0, 0))

        for pid, aid, origin, target in self.army_updates:
            if not origin:
                continue
            x, y = origin
            if self.territories[x, y, 1] == pid:
                color = array('B', self.players[pid].color + (200,))
            else:
                # Passable but not occupiable
                color = clear_color
            i = (self.map_size[0] * (self.map_size[1]-y-1) + x) * 4
            self.map_px[i:i+4] = color
        for pid, player in enumerate(self.players):
            color = array('B', self.players[pid].unit_color + (200,))
            for x, y in self.armies[pid].values():
                i = (self.map_size[0] * (self.map_size[1]-y-1) + x) * 4
                self.map_px[i:i+4] = color
        self.map.blit_buffer(self.map_px, colorfmt='rgba', bufferfmt='ubyte')
        # print("Update map took:", time()-_s, "for", len(self.army_updates), "updates and", sum(len(armies) for armies in self.armies))

        # Spawn player armies
        _s = time()
        for pid, player in enumerate(self.players):
            if not self.land[pid]:
                self.root.ids.max_pops.text += f"[color=%02x%02x%02x]0[/color]\n" % player.color
                continue
            land = len(self.land[pid])
            armies = len(self.armies[pid])
            total = POP_BASE + log(1+land/1000)*30
            self.root.ids.max_pops.text += f"[color=%02x%02x%02x]{int(total)}[/color]\n" % player.color
            growth = max((total - armies) * POP_GROWTH, 0)
            excess, growth = modf(self.players_armies_excess[pid] + growth)
            # print(pid, land, land * POP_GROWTH - land ** 2 * POP_REDUCTION, growth, excess)
            self.players_armies_excess[pid] = excess
            for _ in range(int(growth)):
                x, y = random.choice(list(self.land[pid]))
                self.spawn_army(pid, x, y)
        # print("Spawn player armies took:", time()-_s)

        # Record History
        if self.army_updates:
            updates = [(int(pid), str(aid), origin, target) for pid, aid, origin, target in self.army_updates]
            self.history['history'].append(updates)

        _s = time()
        # Update players and get their movement orders
        army_updates = deepcopy(self.army_updates)
        self.army_updates.clear()
        total_moves = []

        for pid, player in enumerate(self.players):
            updates = deepcopy(army_updates)
            _start_p = time()
            moves = player.update(updates)
            for aid, target in moves:
                assert self.armies[pid][aid] != target
                total_moves.append((pid, aid, target))
            eps = time() - _start_p
            self.eps[pid].append(1. / eps)
            eps = round(sum(self.eps[pid]) / len(self.eps[pid]))
            self.root.ids.territories.text += f"[color=%02x%02x%02x]{self.players_scores[pid]}[/color]\n" % player.color
            self.root.ids.units.text += f"[color=%02x%02x%02x]{len(self.armies[pid])}[/color]\n" % player.color
            self.root.ids.eps.text += f"[color=%02x%02x%02x]{eps}[/color]\n" % player.color
        # print("Update players took:", time()-_s)

        _s = time()
        # Process player movement orders
        random.shuffle(total_moves)
        while total_moves:
            pid, aid, target = total_moves.pop(0)
            try:
                allied_coord = self.armies[pid][aid]
            except KeyError:
                continue  # Happens if army was defeated before its move could be executed or player tried to cheat

            # Check if colonizing
            if target is None:
                x, y = allied_coord
                if self.territories[x, y, 0] == OCCUPIABLE and self.territories[x, y, 1] == -1:
                    self.change_owner(x, y, pid)
                    self.armies[pid].pop(aid)
                    self.army_updates.append((pid, aid, allied_coord, None))
                continue

            x, y = target
            # Check if move is valid
            if self.territories[x, y, 0] not in (OCCUPIABLE, PASSABLE):
                raise ValueError(f"Player {pid} cannot move army {aid} to {x}, {y} (Not passable)")
            _move_distance = abs(x - allied_coord[0]) + abs(y - allied_coord[1])
            if _move_distance != 1:
                raise ValueError(f"Player {pid} can't move army {aid} {_move_distance} territories")
            owner = self.territories[x, y, 1]
            # Own territory -> simply move army
            if owner == pid:
                self.move_army(pid, aid, allied_coord, (x, y))
            # Desert or crossing
            elif self.territories[x, y, 0] == PASSABLE:
                self.move_army(pid, aid, allied_coord, (x, y))
            # Empty, occupied by enemy or stationed army
            else:
                # Stationed army player, owner or -1 (No owner)
                enemy_pid = next(
                    (
                        pid_
                        for pid_, armies_ in enumerate(self.armies)
                        for aid_, pos_ in armies_.items()
                        if aid_ != aid and pid_ != pid and pos_ == target
                    ),
                    owner
                )
                allied_armies = [aid]
                for pid_, aid_, target_ in total_moves:
                    if pid_ != pid or target_ != (x, y):
                        continue
                    allied_armies.append(aid_)
                if enemy_pid == -1:
                    enemy_armies = []
                else:
                    enemy_armies = [uid for uid, coord in self.armies[enemy_pid].items() if coord == (x, y)]
                attacker_roll = sum(random.randint(0, BATTLE_MAX_ROLL) for _ in allied_armies)
                defender_roll = (sum(random.randint(0, BATTLE_MAX_ROLL) for _ in enemy_armies))
                if attacker_roll > defender_roll:  # Win for attacker
                    if enemy_armies:
                        enemy_aid = enemy_armies.pop(0)
                        self.army_updates.append((enemy_pid, enemy_aid, (x, y), None))
                        self.armies[enemy_pid].pop(enemy_aid)
                    if not enemy_armies:  # Last army was defeated or none present
                        self.move_army(pid, aid, allied_coord, (x, y))
                else:  # Win for defender (even if attacker and defender roll are the same)
                    self.armies[pid].pop(aid)
                    self.army_updates.append((pid, aid, allied_coord, None))
        # print("Process player moves took:", time()-_s)

        self.tps.append(1. / (time() - _start_t))
        self.root.ids.tps.text = str(round(sum(self.tps) / len(self.tps), 1))
        self.root.ids.total_ticks.text = str(int(self.root.ids.total_ticks.text) + 1)

    def change_owner(self, x, y, pid):
        assert self.territories[x, y, 0] == OCCUPIABLE
        assert pid >= -1
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
        self.armies[pid][uid] = (x, y)

    def move_army(self, pid, aid, origin, target):
        assert target is not None
        assert self.territories[target[0], target[1], 0] in (OCCUPIABLE, PASSABLE)
        self.army_updates.append((pid, aid, origin, target))
        self.armies[pid][aid] = target

        if self.territories[target[0], target[1], 0] == OCCUPIABLE and self.territories[target[0], target[1], 1] not in (-1, pid):
            self.change_owner(*target, pid)


if __name__ == '__main__':
    from datetime import datetime

    import ujson

    from ais.random_ai import AI as RandomAI
    from ais.expand_c import AI as ExpandAI
    app = GameApp(
        map_path='assets/maps/europe1.png',
        players=(
            (ExpandAI, (105, 105, 105)),
            (ExpandAI, (220, 220, 220)),
            (ExpandAI, (25, 25, 112)),
            (ExpandAI, (139, 0, 0)),
            (ExpandAI, (128, 128, 0)),
            (ExpandAI, (16, 179, 113)),
            (ExpandAI, (255, 0, 0)),
            (ExpandAI, (255, 140, 0)),
            (ExpandAI, (255, 215, 0)),
            (ExpandAI, (199, 21, 133)),
            (ExpandAI, (0, 255, 127)),
            (ExpandAI, (0, 255, 255)),
            (ExpandAI, (0, 191, 255)),
            (ExpandAI, (0, 0, 255)),
            (ExpandAI, (173, 255, 47)),
            (ExpandAI, (255, 0, 255)),
            (ExpandAI, (240, 230, 140)),
            (ExpandAI, (221, 160, 221)),
            (ExpandAI, (123, 104, 238)),
            (ExpandAI, (255, 160, 122)),
        )
    )
    try:
        app.run()
    finally:
        history_path = f"history/{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(history_path, 'w') as f:
            f.write(ujson.dumps(app.history))
