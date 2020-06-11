

def mix_colors(rgb1, rgb2, amount):
    return tuple(v1 * amount + v2 * (1-amount) for v1, v2 in zip(rgb1, rgb2))
