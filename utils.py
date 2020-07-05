import noise
import numpy as np

from const import COLORS, STRAIT, DESERT, LAND, PASSABLE, OCCUPIABLE, IMPASSABLE


def mix_colors(rgb1, rgb2, amount):
    return tuple(v1 * amount + v2 * (1-amount) for v1, v2 in zip(rgb1, rgb2))


def territories_from_map(img_px, size):
    territories = np.zeros((*size, 2), dtype=np.int16)
    for x in range(territories.shape[0]):
        for y in range(territories.shape[1]):
            if img_px[x, y] in (STRAIT, DESERT):
                territories[x, y] = (PASSABLE, -1)
            elif img_px[x, y] == LAND:
                territories[x, y] = (OCCUPIABLE, -1)
            else:
                territories[x, y] = (IMPASSABLE, -1)
    return territories


def prettify_map(img, img_px):
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            v = img_px[x, y]
            n = noise.snoise2(x * .01, y * .01, octaves=8, persistence=.7, lacunarity=2.) + 1
            try:
                r, g, b = mix_colors(COLORS[v][0], COLORS[v][1], n)
            except KeyError:
                print('No colors found for', v)
                continue
            img_px[x, y] = int(r), int(g), int(b)
