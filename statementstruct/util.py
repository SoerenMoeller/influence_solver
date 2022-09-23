import bisect

import solver.rules as rules
from solver.constants import QUALITY_CONS
from statementstruct.statement import Statement


def get_overlap_index(boundaries: list[float], begin, end=None) -> tuple[int, int]:
    if end is None:
        return get_overlap_index(boundaries, begin.begin, begin.end)

    left: int = bisect.bisect_left(boundaries, begin)
    if left > 0:
        left -= 1
    right: int = bisect.bisect_right(boundaries, end)
    return left, right


def init_boundaries(ivs: set[Statement], overlap_map: dict[float, set[Statement]]) -> list[float]:
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
    to_add: set[Statement] = set()
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


def strengthen_interval_height_sides(ivs: list[Statement]):
    i: int = 0
    while i < len(ivs):
        changed: bool = False
        if i < len(ivs) - 1:
            result = rules.interval_strength_left(ivs[i], ivs[i + 1])
            if result is not None:
                ivs[i + 1] = result
                changed = True
        if i > 0:
            result = rules.interval_strength_right(ivs[i - 1], ivs[i])
            if result is not None:
                ivs[i - 1] = result
                changed = True
        if changed:
            i -= 1
            continue
        i += 1


def overlapping(statements: list[Statement], begin, end) -> tuple[int, int]:
    index = bisect.bisect_left(statements, Statement(begin, begin, QUALITY_CONS, 0, 0))

    lower = index
    if index > 0 and len(statements) > 0:
        for i in range(index - 1, -1, -1):
            if not statements[i].overlaps(begin, end):
                break
            lower = i

    upper = index - 1
    for i in range(index, len(statements)):
        if statements[i].begin > end:
            break
        upper = i

    if upper - lower < 0:
        return -1, -1
    return lower, upper + 1
