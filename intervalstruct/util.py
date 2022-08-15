import bisect

from intervalstruct.interval import Interval
from intervalstruct.interval_list_dynamic import IntervalListDynamic
import solver.rules as rules


def strengthen_interval_height(boundaries: list[float], overlap_map: dict[float, set[Interval]], ivs: list[Interval],
                               tmp_ivs=None):
    instance = IntervalListDynamic.get_instance()
    lower, upper = instance.statement[1]
    begin, end = get_overlap_index(boundaries, lower, upper)

    # build overlapping first
    if end == len(boundaries) - 1:
        end -= 1
    for i in range(begin, end):
        point: float = boundaries[i]
        if not overlap_map[point]:
            continue

        next_point: float = boundaries[i + 1]
        iv: Interval = rules.interval_strength_multiple(point, next_point, overlap_map[point])
        ivs.append(iv)
        if tmp_ivs is not None:
            tmp_ivs.add(iv)

    left, right = _check_for_height(ivs)
    lower, upper = instance.statement[3]
    if not left:
        for i in range(begin - 1, -1, -1):
            point: float = boundaries[i]
            if not overlap_map[point]:
                continue

            next_point: float = boundaries[i + 1]

            if instance.left_lower is not None and instance.left_upper is not None \
                    and next_point <= instance.left_lower and next_point <= instance.left_upper:
                break

            iv: Interval = rules.interval_strength_multiple(point, next_point, overlap_map[point])
            ivs.insert(0, iv)
            if tmp_ivs is not None:
                tmp_ivs.add(iv)

            if instance.left_lower is not None and instance.left_lower < next_point and iv.begin_other >= lower:
                instance.left_lower = next_point
            if instance.left_upper is not None and instance.left_upper < next_point and iv.end_other <= upper:
                instance.left_upper = next_point

    if not right:
        for i in range(end, len(boundaries) - 1):
            point: float = boundaries[i]

            if instance.right_lower is not None and instance.right_upper is not None \
                    and point >= instance.right_lower and point >= instance.right_upper:
                break

            if not overlap_map[point]:
                continue

            next_point: float = boundaries[i + 1]
            iv: Interval = rules.interval_strength_multiple(point, next_point, overlap_map[point])
            ivs.insert(0, iv)
            if tmp_ivs is not None:
                tmp_ivs.add(iv)

            if instance.right_lower is not None and instance.right_lower > point and iv.begin_other >= lower:
                instance.right_lower = point
            if instance.right_upper is not None and instance.right_upper > point and iv.end_other <= upper:
                instance.right_upper = point


def _check_for_height(ivs: list[Interval]) -> tuple[bool, bool]:
    # This is used when only the overlapping ones are in the model
    instance = IntervalListDynamic.get_instance()
    begin, end = instance.statement[1]
    lower, upper = instance.statement[3]

    first: Interval = ivs[0]
    last: Interval = ivs[-1]

    if first.overlaps(begin):
        if first.begin_other >= lower:
            instance.left_lower = begin
        if first.end_other <= upper:
            instance.left_upper = end
    if last.overlaps(end):
        if last.begin_other >= lower:
            instance.right_lower = begin
        if last.end_other <= upper:
            instance.right_upper = end

    return instance.left_upper is not None and instance.left_lower is not None, \
           instance.right_upper is not None and instance.right_lower is not None


def get_overlap_index(boundaries: list[float], begin, end=None) -> tuple[int, int]:
    if end is None:
        return get_overlap_index(boundaries, begin.begin, begin.end)

    left: int = bisect.bisect_left(boundaries, begin)
    right: int = bisect.bisect_right(boundaries, end)
    return left, right


def init_boundaries_for_intersect(ivs: set[Interval], overlap_map: dict[float, set[Interval]]) -> list[float]:
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
