import sys

import ujson
import numpy as np
from PIL import Image
import cv2

import utils


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
    fps = 30

file_name = file_path.rstrip('.json')
with open(file_path, 'r') as f:
    content = ujson.load(f)

map_path = content['map']
players = content['players']
history = content['history']

img = Image.open(map_path).convert('RGB')
img_px = img.load()
size = int(img.width * ratio_x), int(img.height * ratio_y)
territories = utils.territories_from_map(img_px, img.size)
utils.prettify_map(img, img_px)
img_px_original = img.copy().load()
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video = cv2.VideoWriter(f"{file_name}.avi", fourcc, fps, size)

armies = {}
hl = len(history)

for i, tick_data in enumerate(history):
    if i % 100 == 0:
        print(i, "out of", hl, "done")

    for pid, aid, origin, target in tick_data:
        # Origin
        if origin:
            x, y = origin
            if territories[x, y, 0] == 1:  # Passable
                img_px[x, y] = img_px_original[x, y]
            elif not any(a[1] == origin for i, a in armies.items() if i != aid):
                # No more armies left on origin tile, repaint
                img_px[x, y] = tuple(players[pid]['color'])

        # Target
        if not target:
            if territories[x, y, 0] == 2:  # Occupiable
                img_px[x, y] = tuple(players[pid]['color'])
            armies.pop(aid)
            continue
        x, y = target
        img_px[x, y] = tuple(players[pid]['unit_color'])
        armies[aid] = pid, target

    im = img.resize(size)
    video.write(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

video.release()
