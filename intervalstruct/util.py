import bisect

import solver.rules as rules
from intervalstruct.interval import Interval


def get_overlap_index(boundaries: list[float], begin, end=None) -> tuple[int, int]:
    if end is None:
        return get_overlap_index(boundaries, begin.begin, begin.end)

    left: int = bisect.bisect_left(boundaries, begin)
    if left > 0:
        left -= 1
    right: int = bisect.bisect_right(boundaries, end)
    return left, right


def init_boundaries(ivs: set[Interval], overlap_map: dict[float, set[Interval]]) -> list[float]:
    tmp_boundaries: set[float] = set()
    for iv in ivs:
        if iv.begin not in overlap_map:
            overlap_map[iv.begin] = set()
            tmp_boundaries.add(iv.begin)
        if iv.end not in overlap_map:
            overlap_map[iv.end] = set()
            tmp_boundaries.add(iv.end)
        overlap_map[iv.begin].add(iv)
        overlap_map[iv.end].add(iv)

    # TODO: cleanup
    boundaries = sorted(tmp_boundaries)
    to_add: set[Interval] = set()
    for var in boundaries:
        to_rem = set()
        for iv in to_add:
            if iv in overlap_map[var]:
                overlap_map[var].remove(iv)
                to_rem.add(iv)
        to_add.difference_update(to_rem)
        overlap_map[var].update(to_add)
        to_add.update(overlap_map[var])

    return boundaries


def strengthen_interval_height_sides(ivs: list[Interval]):
    changed = True
    i = 0
    while changed:
        i += 1
        if i > 1:
            print("MORE THAN ONE ROUND")
        changed = False
        for i in range(len(ivs) - 1):
            result = rules.interval_strength_left(ivs[i], ivs[i + 1])
            if result is not None:
                ivs[i + 1] = result
                changed = True
        for i in range(len(ivs) - 2, -1, -1):
            result = rules.interval_strength_right(ivs[i - 1], ivs[i])
            if result is not None:
                ivs[i - 1] = result
                changed = True
