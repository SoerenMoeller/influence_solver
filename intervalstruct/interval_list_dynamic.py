import time
from typing import Union

import intervalstruct.util as util
import solver.rules as rules
from intervalstruct.interval import Interval


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
        self._overlapping: list[Interval] = []
        self.left_lower: Union[float, None] = None
        self.left_upper: Union[float, None] = None
        self.right_lower: Union[float, None] = None
        self.right_upper: Union[float, None] = None

    def reset(self):
        self._overlap_map = {}
        self._boundaries = []
        self._x_set = []
        self._overlapping = []
        tmp_ivs: set[Interval] = self._all_intervals.copy()
        self._all_intervals = set()
        for iv in tmp_ivs:
            self.add(iv)

    def solve(self) -> tuple[bool, float]:
        start_time: float = time.time()
        if not self._all_intervals:
            return False, time.time() - start_time

        self._overlap_map.clear()
        self._boundaries = util.init_boundaries(self._all_intervals, self._overlap_map)
        self._all_intervals = set()

        self.strengthen_interval_height()
        self.strengthen_interval_height_sides()
        return self.check_widest(), time.time() - start_time

    def strengthen_interval_height(self):
        lower, upper = self.statement[1]
        begin, end = util.get_overlap_index(self._boundaries, lower, upper)

        # build overlapping first
        if end > len(self._boundaries):
            end = len(self._boundaries)
        for i in range(begin, end):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.append(iv)
            self._all_intervals.add(iv)
            self._overlapping.append(iv)

        left, right = self._check_for_height()
        lower, upper = self.statement[3]
        if not left:
            for i in range(begin - 1, -1, -1):
                point: float = self._boundaries[i]
                if not self._overlap_map[point]:
                    continue

                next_point: float = self._boundaries[i + 1]

                if self.left_lower is not None and self.left_upper is not None \
                        and next_point <= self.left_lower and next_point <= self.left_upper:
                    break

                iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
                self._x_set.insert(0, iv)
                self._all_intervals.add(iv)

                if (self.left_lower is None or self.left_lower < next_point) and iv.begin_other >= lower:
                    self.left_lower = next_point
                if (self.left_upper is None or self.left_upper < next_point) and iv.end_other <= upper:
                    self.left_upper = next_point

        if not right:
            for i in range(end, len(self._boundaries) - 1):
                point: float = self._boundaries[i]

                if self.right_lower is not None and self.right_upper is not None \
                        and point >= self.right_lower and point >= self.right_upper:
                    break

                if not self._overlap_map[point]:
                    continue

                next_point: float = self._boundaries[i + 1]
                iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
                self._x_set.append(iv)
                self._all_intervals.add(iv)

                if (self.right_lower is None or self.right_lower > point) and iv.begin_other >= lower:
                    self.right_lower = point
                if (self.right_upper is None or self.right_upper > point) and iv.end_other <= upper:
                    self.right_upper = point

    def _check_for_height(self) -> tuple[bool, bool]:
        # This is used when only the overlapping ones are in the model
        begin, end = self.statement[1]
        lower, upper = self.statement[3]

        first: Interval = self._x_set[0]
        last: Interval = self._x_set[-1]

        if first.overlaps(begin):
            if first.begin_other >= lower:
                self.left_lower = first.begin
            if first.end_other <= upper:
                self.left_upper = first.begin
        if last.overlaps(end):
            if last.begin_other >= lower:
                self.right_lower = last.end
            if last.end_other <= upper:
                self.right_upper = last.end

        return self.left_upper is not None and self.left_lower is not None, \
               self.right_upper is not None and self.right_lower is not None

    def check_widest(self) -> bool:
        iv: Union[Interval, None] = rules.interval_join_multiple(self._overlapping)

        result: bool = rules.rule_fact(self.statement, iv)
        if result:
            self._x_set.append(iv)  # This destroys the order of the list, is for visualizing only
        return result

    def add(self, statement: Interval) -> bool:
        if statement is None or statement in self._all_intervals:
            return False

        self._all_intervals.add(statement)
        return True

    def __len__(self) -> int:
        return len(self._x_set)

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
