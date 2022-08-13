import bisect
from itertools import chain

from intervalstruct.interval import Interval
from solver.constants import QUALITY_CONS
from solver.rules import interval_strength_left, interval_strength_right, interval_strength_multiple
from solver.util import is_stronger_as

"""
Only used once for the result, therefore no class is needed
"""

_statement: tuple
_x_set = []
_all_intervals = set()
_verbose = 1
_overlap_map = {}
_boundaries: list[float]
left_lower: bool = False
left_upper: bool = False
right_lower: bool = False
right_upper: bool = False
x_lower = None
x_upper = None


def init(statement: tuple, ivs: set[Interval]):
    global _statement, _overlap_map, _boundaries, _x_set

    _statement = statement
    tmp_boundaries: set[float] = set()
    for iv in ivs:
        if iv.begin not in _overlap_map:
            _overlap_map[iv.begin] = set()
            tmp_boundaries.add(iv.begin)
        if iv.end not in _overlap_map:
            _overlap_map[iv.end] = set()
            tmp_boundaries.add(iv.end)
        _overlap_map[iv.begin].add(iv)
        _overlap_map[iv.end].add(iv)

    # TODO: cleanup
    _boundaries = sorted(tmp_boundaries)
    to_add: set[Interval] = set()
    for var in _boundaries:
        to_rem = set()
        for iv in to_add:
            if iv in _overlap_map[var]:
                _overlap_map[var].remove(iv)
                to_rem.add(iv)
        to_add.difference_update(to_rem)
        _overlap_map[var].update(to_add)
        to_add.update(_overlap_map[var])

    solve()
    # restore for later
    _overlap_map = {}
    _boundaries = []
    _x_set = []

    for iv in _all_intervals:
        add(iv)


def solve():
    strengthen_interval_height()
    strengthen_interval_height_sides()
    build_widest()


def build_widest():
    pass


def add(statement: Interval, height=None) -> bool:
    if statement is None or statement in _all_intervals:
        return False

    if statement.begin_other == statement.end_other:
        statement = Interval(statement.begin, statement.end, QUALITY_CONS, statement.begin_other,
                             statement.end_other)

    overlapping: set[Interval] = overlap(statement)
    enveloping: set[Interval] = get_enveloping_overlap(overlapping, statement)
    enveloped_by: set[Interval] = get_enveloped_by_overlap(overlapping, statement)

    # if new statement envelops interval with less width and more height and weaker quality,
    # we can remove the old one
    for iv in enveloping:
        if is_stronger_as(statement.quality,
                          iv.quality) and statement.begin <= iv.begin and statement.end >= iv.end and \
                ((statement.begin_other >= iv.begin_other and statement.end_other <= iv.end_other)
                 or (height is not None and height[0] <= statement.begin_other and height[
                            1] >= statement.end_other)):
            # remove old interval (not needed anymore)
            remove(iv)

            if 2 <= _verbose <= 3:
                print(f"=== removed interval -{iv}- for stronger interval -{statement}- ===")

    for iv in enveloped_by:
        if is_stronger_as(iv.quality, statement.quality) and \
                (iv.begin_other >= statement.begin_other and iv.end_other <= statement.end_other
                 or (height is not None and height[0] >= iv.begin_other and height[1] <= iv.end_other)):
            if 2 <= _verbose <= 3:
                print(f"=== did not include interval -{statement}- because of stronger interval -{iv}- ===")
            return False

    _all_intervals.add(statement)
    _add_boundary(statement)
    return True


def strengthen_interval_height():
    global left_lower, left_upper, right_lower, right_upper, x_lower, x_upper

    lower, upper = _statement[1]
    begin, end = _get_overlap_index(lower, upper)

    # build overlapping first
    for i in range(begin, end):
        point: float = _boundaries[i]
        if not _overlap_map[point]:
            continue

        next_point: float = _boundaries[i + 1]
        iv: Interval = interval_strength_multiple(point, next_point, _overlap_map[point])
        _x_set.append(iv)
        _all_intervals.add(iv)

    left, right = _check_for_height()
    lower, upper = _statement[4]
    if not left:
        for i in range(begin - 1, -1, -1):
            point: float = _boundaries[i]
            if not _overlap_map[i]:
                continue

            next_point: float = _boundaries[i + 1]
            iv: Interval = interval_strength_multiple(point, next_point, _overlap_map[point])
            _x_set.insert(0, iv)
            _all_intervals.add(iv)

            if not left_lower and iv.begin_other >= lower:
                left_lower = True
            if not right_upper and iv.begin_other >= upper:
                left_upper = True
            if left_lower and left_upper:
                x_lower = next_point
                break

    if not right:
        for i in range(end, len(_boundaries) - 1):
            point: float = _boundaries[i]
            if not _overlap_map[i]:
                continue

            next_point: float = _boundaries[i + 1]
            iv: Interval = interval_strength_multiple(point, next_point, _overlap_map[point])
            _x_set.append(iv)
            _all_intervals.add(iv)

            if not right_lower and iv.begin_other >= lower:
                right_lower = True
            if not right_upper and iv.begin_other >= upper:
                right_upper = True
            if right_lower and right_upper:
                x_upper = point
                break


def remove(iv: Interval):
    _all_intervals.remove(iv)
    _remove_boundary(iv)


def discard(iv: Interval):
    _all_intervals.discard(iv)
    _remove_boundary(iv)


def _add_boundary(iv: Interval):
    if iv.begin not in _overlap_map:
        _overlap_map[iv.begin] = set()
    bisect.insort_left(_boundaries, iv.begin)

    if iv.end not in _overlap_map:
        _overlap_map[iv.end] = set()
    bisect.insort_left(_boundaries, iv.begin)

    left, right = _get_overlap_index(iv)
    for i in range(left, right):
        point: float = _boundaries[i]
        _overlap_map[point].add(iv)

    if left - 1 >= 0 and left + 1 < len(_boundaries):
        for iv in _overlap_map[_boundaries[left - 1]]:
            if iv in _overlap_map[_boundaries[left + 1]]:
                _overlap_map[_boundaries[left]].add(iv)

    if right - 1 >= 0 and right + 1 < len(_boundaries):
        for iv in _overlap_map[_boundaries[right - 1]]:
            if iv in _overlap_map[_boundaries[right + 1]]:
                _overlap_map[_boundaries[right]].add(iv)


def _remove_boundary(iv: Interval):
    left, right = _get_overlap_index(iv)

    removable: set[float] = set()
    for i in range(left, right):
        point: float = _boundaries[i]
        _overlap_map[point].remove(iv)
        if not _overlap_map[point]:
            removable.add(point)

    for i in removable:
        del _overlap_map[i]


def length() -> int:
    return len(_x_set)


def _get_overlap_index(begin, end=None) -> tuple[int, int]:
    if end is None:
        return _get_overlap_index(begin.begin, begin.end)

    left: int = bisect.bisect_left(_boundaries, begin)
    right: int = bisect.bisect_right(_boundaries, end)
    return left, right


def overlap(begin, end=None) -> set[Interval]:
    if end is None:
        return overlap(begin.begin, begin.end)

    left, right = _get_overlap_index(begin, end)

    return set(chain.from_iterable(_overlap_map[i] for i in range(left, right)))


def get_enveloped_by_overlap(overlapping, begin, end: int = None) -> set[Interval]:
    if end is None:
        return get_enveloped_by_overlap(overlapping, begin.begin, begin.end)
    return {iv for iv in overlapping if iv.enveloping(begin, end)}


def get_enveloping_overlap(overlapping, begin, end: int = None) -> set[Interval]:
    if end is None:
        return get_enveloping_overlap(overlapping, begin.begin, begin.end)
    return {iv for iv in overlapping if iv.enveloped_by(begin, end)}


def get_intervals(begin, end=None):
    if end is None:
        return get_intervals(begin[0], begin[1])

    if begin < 0 or end > len(_x_set):
        raise ValueError
    return _x_set[begin:end]


def strengthen_interval_height_sides():
    changed = True
    i = 0
    while changed:
        i += 1
        if i > 1:
            print("MORE T")
        changed = False
        for i in range(len(_x_set) - 1):
            result = interval_strength_left(_x_set[i], _x_set[i + 1])
            if result is not None:
                _x_set[i + 1] = result
                changed = True
        for i in range(len(_x_set) - 2, -1, -1):
            result = interval_strength_right(_x_set[i - 1], _x_set[i])
            if result is not None:
                _x_set[i - 1] = result
                changed = True


def intervals():
    return _x_set


def intervals_turned():
    return sorted({iv.turn_interval() for iv in _x_set})


def _check_for_gap() -> bool:
    for i in range(len(_x_set) - 1):
        if _x_set[i].distance_to(_x_set[i + 1]) > 0:
            return False
    return True


def _check_for_height() -> tuple[bool, bool]:
    global left_lower, left_upper, right_lower, right_upper, x_lower, x_upper

    # This is used when only the overlapping ones are in the model
    begin, end = _boundaries[1]
    lower, upper = _statement[4]

    first: Interval = _x_set[0]
    last: Interval = _x_set[-1]

    left_lower = first.overlaps(begin) and first.begin_other >= lower
    left_upper = first.overlaps(begin) and first.end_other <= upper
    right_lower = last.overlaps(end) and last.begin_other >= lower
    right_upper = last.overlaps(end) and last.end_other <= upper

    if left_upper and left_lower:
        x_lower = begin
    if right_upper and right_lower:
        x_upper = end

    return left_upper and left_lower, right_upper and right_lower
