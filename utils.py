import noise

from const import COLORS


def mix_colors(rgb1, rgb2, amount):
    return tuple(v1 * amount + v2 * (1-amount) for v1, v2 in zip(rgb1, rgb2))


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
