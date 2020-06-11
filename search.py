from scipy.spatial import distance


MOVES = ((-1, 0), (0, 1), (1, 0), (0, -1))


def check_all(origin, walk_cond, find_cond):
    open_tiles = [origin]
    checked_tiles = [origin]
    findings = []

    while open_tiles:
        x, y = open_tiles.pop()

        for mx, my in MOVES:
            bx, by = x + mx, y + my
            if (bx, by) in checked_tiles:
                continue
            if walk_cond(bx, by):
                open_tiles.append((bx, by))
            if find_cond(bx, by):
                findings.append((bx, by))
            checked_tiles.append((bx, by))
    return findings


def astar(origin, target, wall_check):
    # print('############')
    # print('origin, target', origin, target)
    # a node consists of origin node and child nodes, sorted by distance to target
    checked = [origin]
    node = (None, origin, [])
    nodes = []#(distance.euclidean(target, (x, y)), node)]

    while node[1] != target:
        x, y = node[1]
        # print('x, y', x, y)
        m = [(mx + x, my + y) for mx, my in MOVES]
        moves = sorted(
            (
                distance.euclidean(target, (bx, by)),
                bx, by
            )
            for bx, by in m
            if (bx, by) not in checked and not wall_check(bx, by)
        )
        # print(moves)
        for d, x, y in moves:
            child = (node, (x, y), [])
            node[2].append(child)
            nodes.append((d, child))
            checked.append((x, y))
        nodes.sort(key=lambda _: _[0])
        # if moves:
            # print('add path')
            # child = node[2][0]  # first[0] child[1] of current node
            # d, x, y = moves[0]
            # checked.append((x, y))
        #     node = child
        # else:  # all moves already checked or walls
        #     # print('getting closest node')
        #     # print(nodes)
        #     # x, y = path.pop()
        #     nodes.pop(0)  # Remove current node as all paths are exhausted for it
        node = nodes.pop(0)[1]  # closest node to target
        # checked.append(node[1])
        # print('path', path)
        # print('nodes', len(nodes))

    path = []
    parent = node[0]
    while parent is not None:
        path.insert(0, (node[1]))
        node = parent
        parent = node[0]
    return path
