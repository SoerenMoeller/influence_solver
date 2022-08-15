import bisect
from itertools import chain
from typing import Union

from intervalstruct.interval import Interval
from solver.constants import QUALITY_CONS
import solver.rules as rules
import intervalstruct.util as util
from solver.util import is_stronger_as

# TODO: Stricter search in final


class IntervalListDynamic:
    instance = None

    @staticmethod
    def get_instance():
        return IntervalListDynamic.instance

    def __init__(self, statement_init: tuple, ivs: set[Interval], paths: int):
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

        self._check_overlap = paths > 2

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
        self._boundaries = util.init_boundaries_for_intersect(self._all_intervals, self._overlap_map)
        self._all_intervals = set()

        self.strengthen_interval_height()
        self.strengthen_interval_height_sides()
        return self.check_widest()

    def strengthen_interval_height(self):
        util.strengthen_interval_height(self._boundaries, self._overlap_map, self._x_set, self._all_intervals)

    def check_widest(self):
        # TODO: fix for edge cases
        begin, end = util.get_overlap_index(self._boundaries, self.statement[1][0], self.statement[1][1])
        iv: Union[Interval, None] = rules.interval_join_multiple(self._x_set[begin:end])

        return rules.rule_fact(self.statement, iv)

    def add(self, statement: Interval) -> bool:
        if statement is None or statement in self._all_intervals:
            return False

        if statement.begin_other == statement.end_other:
            statement = Interval(statement.begin, statement.end, QUALITY_CONS, statement.begin_other,
                                 statement.end_other)

        if self._check_overlap:
            height: tuple[float, float] = self.statement[3]
            overlapping: set[Interval] = self.overlap(statement)
            enveloping: set[Interval] = get_enveloping_overlap(overlapping, statement)
            enveloped_by: set[Interval] = get_enveloped_by_overlap(overlapping, statement)

            # if new statement envelops interval with less width and more height and weaker quality,
            # we can remove the old one
            for iv in enveloping:
                if is_stronger_as(statement.quality,
                                  iv.quality) and statement.begin <= iv.begin and statement.end >= iv.end and \
                        ((statement.begin_other >= iv.begin_other and statement.end_other <= iv.end_other)
                         or (height[0] <= statement.begin_other and height[1] >= statement.end_other)):
                    # remove old interval (not needed anymore)
                    self.remove(iv)

                    if 2 <= self._verbose <= 3:
                        print(f"=== removed interval -{iv}- for stronger interval -{statement}- ===")

            for iv in enveloped_by:
                if is_stronger_as(iv.quality, statement.quality) and \
                        (iv.begin_other >= statement.begin_other and iv.end_other <= statement.end_other
                         or (height[0] >= iv.begin_other and height[1] <= iv.end_other)):
                    if 2 <= self._verbose <= 3:
                        print(f"=== did not include interval -{statement}- because of stronger interval -{iv}- ===")
                    return False

            self._add_boundary(statement)

        self._all_intervals.add(statement)
        return True

    def remove(self, iv: Interval):
        self._all_intervals.remove(iv)
        self._remove_boundary(iv)

    def _add_boundary(self, iv: Interval):
        if iv.begin not in self._overlap_map:
            self._overlap_map[iv.begin] = set()
            bisect.insort_left(self._boundaries, iv.begin)

        if iv.end not in self._overlap_map:
            self._overlap_map[iv.end] = set()
            bisect.insort_left(self._boundaries, iv.end)

        left, right = util.get_overlap_index(self._boundaries, iv)
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
        left, right = util.get_overlap_index(self._boundaries, iv)

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

        left, right = util.get_overlap_index(self._boundaries, begin, end)

        return set(chain.from_iterable(self._overlap_map[self._boundaries[i]] for i in range(left, right)))

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._x_set):
            raise ValueError
        return self._x_set[begin:end]

    def strengthen_interval_height_sides(self):
        util.strengthen_interval_height_sides(self._x_set)

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
