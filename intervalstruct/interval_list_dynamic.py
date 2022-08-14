import bisect
from itertools import chain
from typing import Union

from intervalstruct.interval import Interval
from solver.constants import QUALITY_CONS
from solver.rules import interval_strength_left, interval_strength_right, interval_join_multiple, rule_fact
import solver.solver as solver
from solver.util import is_stronger_as, get_overlap_index

# TODO: Stricter search in final


class IntervalListDynamic:
    instance = None

    @staticmethod
    def get_instance():
        return IntervalListDynamic.instance

    def __init__(self, statement_init: tuple, ivs: set[Interval]):
        IntervalListDynamic.instance = self
        self.statement: tuple = statement_init
        self._all_intervals: set[Interval] = ivs
        self._x_set: list[Interval] = []
        self._verbose: int = 1
        self._overlap_map: dict[float, set[Interval]] = {}
        self._boundaries: list[float] = []
        self.left_lower: Union[float, None] = None
        self.left_upper: Union[float, None] = None
        self.right_lower: Union[float, None] = None
        self.right_upper: Union[float, None] = None

    def reset(self):
        self._overlap_map = {}
        self._boundaries = []
        self._x_set = []
        tmp_ivs: set[Interval] = self._all_intervals.copy()
        self._all_intervals = set()
        for iv in tmp_ivs:
            self.add(iv)

    def solve(self):
        if not self._all_intervals:
            return

        self._overlap_map.clear()
        tmp_boundaries: set[float] = set()
        for iv in self._all_intervals:
            if iv.begin not in self._overlap_map:
                self._overlap_map[iv.begin] = set()
                tmp_boundaries.add(iv.begin)
            if iv.end not in self._overlap_map:
                self._overlap_map[iv.end] = set()
                tmp_boundaries.add(iv.end)
            self._overlap_map[iv.begin].add(iv)
            self._overlap_map[iv.end].add(iv)

        # TODO: cleanup
        self._boundaries = sorted(tmp_boundaries)
        to_add: set[Interval] = set()
        for var in self._boundaries:
            to_rem = set()
            for iv in to_add:
                if iv in self._overlap_map[var]:
                    self._overlap_map[var].remove(iv)
                    to_rem.add(iv)
            to_add.difference_update(to_rem)
            self._overlap_map[var].update(to_add)
            to_add.update(self._overlap_map[var])
        self._all_intervals = set()

        self.strengthen_interval_height()
        self.strengthen_interval_height_sides()
        return self.check_widest()

    def strengthen_interval_height(self):
        solver.strengthen_interval_height(self._boundaries, self._overlap_map, self._x_set, self._all_intervals)

    def check_widest(self):
        # TODO: fix for edge cases
        begin, end = get_overlap_index(self._boundaries, self.statement[1][0], self.statement[1][1])
        iv: Union[Interval, None] = interval_join_multiple(self._x_set[begin:end])

        return rule_fact(self.statement, iv)

    def add(self, statement: Interval, height=None) -> bool:
        if statement is None or statement in self._all_intervals:
            return False

        if statement.begin_other == statement.end_other:
            statement = Interval(statement.begin, statement.end, QUALITY_CONS, statement.begin_other,
                                 statement.end_other)

        overlapping: set[Interval] = self.overlap(statement)
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
                self.remove(iv)

                if 2 <= self._verbose <= 3:
                    print(f"=== removed interval -{iv}- for stronger interval -{statement}- ===")

        for iv in enveloped_by:
            if is_stronger_as(iv.quality, statement.quality) and \
                    (iv.begin_other >= statement.begin_other and iv.end_other <= statement.end_other
                     or (height is not None and height[0] >= iv.begin_other and height[1] <= iv.end_other)):
                if 2 <= self._verbose <= 3:
                    print(f"=== did not include interval -{statement}- because of stronger interval -{iv}- ===")
                return False

        self._all_intervals.add(statement)
        self._add_boundary(statement)
        return True

    """
    def strengthen_interval_height():
        global left_lower, left_upper, right_lower, right_upper
    
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
                
                if left_lower is not None and left_upper is not None \
                        and next_point <= left_lower and next_point <= left_upper:
                    break
                
                iv: Interval = interval_strength_multiple(point, next_point, _overlap_map[point])
                _x_set.insert(0, iv)
                _all_intervals.add(iv)
    
                if left_lower is not None and left_lower < next_point and iv.begin_other >= lower:
                    left_lower = next_point
                if left_upper is not None and left_upper < next_point and iv.end_other <= upper:
                    left_upper = next_point
    
        if not right:
            for i in range(end, len(_boundaries) - 1):
                point: float = _boundaries[i]
                
                if right_lower is not None and right_upper is not None \
                        and point >= right_lower and point >= right_upper:
                    break
                
                if not _overlap_map[i]:
                    continue
    
                next_point: float = _boundaries[i + 1]
                iv: Interval = interval_strength_multiple(point, next_point, _overlap_map[point])
                _x_set.append(iv)
                _all_intervals.add(iv)
                
                if right_lower is not None and right_lower > point and iv.begin_other >= lower:
                    right_lower = point
                if right_upper is not None and right_upper > point and iv.end_other <= upper:
                    right_upper = point
    """

    def remove(self, iv: Interval):
        self._all_intervals.remove(iv)
        self._remove_boundary(iv)

    def discard(self, iv: Interval):
        self._all_intervals.discard(iv)
        self._remove_boundary(iv)

    def _add_boundary(self, iv: Interval):
        if iv.begin not in self._overlap_map:
            self._overlap_map[iv.begin] = set()
            bisect.insort_left(self._boundaries, iv.begin)

        if iv.end not in self._overlap_map:
            self._overlap_map[iv.end] = set()
            bisect.insort_left(self._boundaries, iv.end)

        for i in range(len(self._boundaries)):
            for j in range(i + 1, len(self._boundaries)):
                if self._boundaries[i] == self._boundaries[j]:
                    print("ERROR")

        left, right = get_overlap_index(self._boundaries, iv)
        for i in range(left, right):
            point: float = self._boundaries[i]
            self._overlap_map[point].add(iv)

        if left - 1 >= 0 and left + 1 < len(self._boundaries):
            for iv in self._overlap_map[self._boundaries[left - 1]]:
                if iv in self._overlap_map[self._boundaries[left + 1]]:
                    self._overlap_map[self._boundaries[left]].add(iv)

        if right - 1 >= 0 and right + 1 < len(self._boundaries):
            for iv in self._overlap_map[self._boundaries[right - 1]]:
                if iv in self._overlap_map[self._boundaries[right + 1]]:
                    self._overlap_map[self._boundaries[right]].add(iv)

    def _remove_boundary(self, iv: Interval):
        if iv == Interval(3.1214952229299366, 3.1314904458598725, "anti", -0.1516300189437798, 0.0483699810562202):
            print("")
        left, right = get_overlap_index(self._boundaries, iv)

        removable: set[float] = set()
        for i in range(left, right):
            point: float = self._boundaries[i]
            self._overlap_map[point].remove(iv)
            if not self._overlap_map[point]:
                removable.add(point)

        for i in removable:
            del self._overlap_map[i]
            self._boundaries.remove(i)

    def __len__(self) -> int:
        return len(self._x_set)

    def overlap(self, begin, end=None) -> set[Interval]:
        if end is None:
            return self.overlap(begin.begin, begin.end)

        left, right = get_overlap_index(self._boundaries, begin, end)

        return set(chain.from_iterable(self._overlap_map[self._boundaries[i]] for i in range(left, right)))

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._x_set):
            raise ValueError
        return self._x_set[begin:end]

    def strengthen_interval_height_sides(self):
        changed = True
        i = 0
        while changed:
            i += 1
            if i > 1:
                print("MORE T")
            changed = False
            for i in range(len(self._x_set) - 1):
                result = interval_strength_left(self._x_set[i], self._x_set[i + 1])
                if result is not None:
                    self._x_set[i + 1] = result
                    changed = True
            for i in range(len(self._x_set) - 2, -1, -1):
                result = interval_strength_right(self._x_set[i - 1], self._x_set[i])
                if result is not None:
                    self._x_set[i - 1] = result
                    changed = True

    def intervals(self):
        return self._x_set

    def intervals_turned(self):
        return sorted({iv.turn_interval() for iv in self._x_set})

    def _check_for_gap(self) -> bool:
        for i in range(len(self._x_set) - 1):
            if self._x_set[i].distance_to(self._x_set[i + 1]) > 0:
                return False
        return True


def get_enveloped_by_overlap(overlapping, begin, end: int = None) -> set[Interval]:
    if end is None:
        return get_enveloped_by_overlap(overlapping, begin.begin, begin.end)
    return {iv for iv in overlapping if iv.enveloping(begin, end)}


def get_enveloping_overlap(overlapping, begin, end: int = None) -> set[Interval]:
    if end is None:
        return get_enveloping_overlap(overlapping, begin.begin, begin.end)
    return {iv for iv in overlapping if iv.enveloped_by(begin, end)}
