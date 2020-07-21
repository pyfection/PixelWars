import sys
from collections import namedtuple

import ujson
import numpy as np
from PIL import Image
import cv2

import utils
from const import TERRAIN, POP_VAL


Player = namedtuple('Player', ['color', 'unit_color'])


file_path = sys.argv[1]
try:
    ratio_x = float(sys.argv[2])
    ratio_y = float(sys.argv[3])
except IndexError:
    ratio_x = 1
    ratio_y = 1
try:
    fps = int(sys.argv[4])
except IndexError:
    fps = 60

file_name = file_path.rstrip('.json')
with open(file_path, 'r') as f:
    content = ujson.load(f)

map_path = content['map']
players = [Player(tuple(c['color']), tuple(c['unit_color'])) for c in content['players']]
history = content['history']

img = Image.open(map_path).convert('RGB')
img_px = img.load()
size = int(img.width * ratio_x), int(img.height * ratio_y)
territories = utils.territories_from_map(img_px, img.size)
utils.prettify_map(img, img_px)
img_px_original = img.copy().load()
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video = cv2.VideoWriter(f"{file_name}.avi", fourcc, fps, size)

armies = [{} for _ in players]
hl = len(history)

for i, tick_data in enumerate(history):
    if i % 100 == 0:
        print(i, "out of", hl, "done")

    for pid, aid, origin, target in tick_data:
        if origin:
            x, y = origin
        else:
            x, y = target

        if target:
            if territories[x, y, 1] not in (pid, -1):
                territories[x, y, 1] = pid
        else:
            if TERRAIN[territories[x, y, 0]][POP_VAL] > 0.0:  # Occupiable
                territories[x, y, 1] = pid
            armies[pid].pop(aid)
            continue
        x, y = target
        armies[pid][aid] = target

    for (x, y), color in utils.territories_colors_from_updates(tick_data, players, territories, armies):
        a = color[3] / 255
        img_px[x, y] = utils.mix_colors(color[:3], img_px_original[x, y], a)
    im = img.resize(size)
    video.write(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

video.release()
