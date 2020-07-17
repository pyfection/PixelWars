from array import array

import noise
import numpy as np

from const import MAP, TERRAIN_COLORS, BORDER, BORDER_ALPHA, OCCUPIED_ALPHA


def mix_colors(rgb1, rgb2, amount):
    return tuple(int(v1 * amount) + int(v2 * (1-amount)) for v1, v2 in zip(rgb1, rgb2))


def territories_from_map(img_px, size):
    territories = np.zeros((*size, 2), dtype=np.int16)
    for x in range(territories.shape[0]):
        for y in range(territories.shape[1]):
            territories[x, y] = (MAP[img_px[x, y]], -1)
    return territories


def prettify_map(img, img_px):
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            v = img_px[x, y]
            n = noise.snoise2(x * .01, y * .01, octaves=8, persistence=.7, lacunarity=2.) + 1
            try:
                t = MAP[v]
            except KeyError:
                print('No colors found for', v)
                continue
            r, g, b = mix_colors(TERRAIN_COLORS[t][0], TERRAIN_COLORS[t][1], n)
            img_px[x, y] = int(r), int(g), int(b)


def territories_colors_from_updates(updates, players, territories, armies):
    clear_color = (0, 0, 0, 0)

    for pid, aid, origin, target in updates:
        if not origin:
            continue
        x, y = origin
        if territories[x, y, 1] == pid:
            # Newly occupied territory
            if has_not_self_neighbours(x, y, pid, territories):
                # Is Border
                # Actual color assignment
                yield origin, players[pid].color + (int(BORDER_ALPHA * 255),)
            else:
                yield origin, players[pid].color + (int(OCCUPIED_ALPHA * 255),)

            # Check neighbours if need updating
            for ox, oy in BORDER:
                rx, ry = x + ox, y + oy
                if not (0 <= rx < territories.shape[0] and 0 <= ry < territories.shape[1]):
                    continue
                pid_ = territories[rx, ry, 1]
                if pid_ == -1:
                    continue
                if has_not_self_neighbours(rx, ry, pid_, territories):
                    yield (rx, ry), players[pid_].color + (int(BORDER_ALPHA * 255),)
                else:
                    yield (rx, ry), players[pid_].color + (int(OCCUPIED_ALPHA * 255),)
        else:
            # Passable but not occupiable
            yield origin, clear_color

    for pid, player in enumerate(players):
        color = players[pid].unit_color + (255,)
        for x, y in armies[pid].values():
            yield (x, y), color


def has_not_self_neighbours(x, y, pid, territories):
    for ox, oy in BORDER:
        rx, ry = x + ox, y + oy
        if not (0 <= rx < territories.shape[0] and 0 <= ry < territories.shape[1]):
            continue
        if territories[rx, ry, 1] != pid:
            return True
    return False
