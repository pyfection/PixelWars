import noise
import numpy as np

from const import MAP, TERRAIN_COLORS


def mix_colors(rgb1, rgb2, amount):
    return tuple(v1 * amount + v2 * (1-amount) for v1, v2 in zip(rgb1, rgb2))


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
