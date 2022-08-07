import bisect
from collections import deque
from collections.abc import MutableSet
from typing import Iterator

from intervallist.interval import Interval
from solver.constants import QUALITY_CONS
from solver.rules import interval_strength, interval_strength_left, interval_strength_right, interval_join
from solver.util import is_stronger_as


class IntervalList(MutableSet):
    def __init__(self, ivs=None):
        self._x_set: list[Interval] = []
        self._y_set: list[Interval] = []
        self._verbose: int = 1

        if ivs is None:
            ivs = []
        for iv in ivs:
            self.add(iv)

    def add(self, statement: Interval, intersect=False, height=None) -> bool:
        if statement is None or statement in self._x_set:  # TODO: optimize
            return False

        if statement.begin_other == statement.end_other:
            statement = Interval(statement.begin, statement.end, QUALITY_CONS, statement.begin_other,
                                 statement.end_other)

        overlapping: list[Interval] = self.overlap_x_iv(statement)
        enveloping: list[Interval] = IntervalList.get_enveloping_overlap(self._x_set, statement)
        enveloped_by: list[Interval] = IntervalList.get_enveloped_by_overlap(self._x_set, statement)

        # if new statement envelops interval with less width and more height and weaker quality,
        # we can remove the old one
        for iv in enveloping:
            if is_stronger_as(statement.quality, iv.quality) and \
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

        bisect.insort_left(self._x_set, statement)
        bisect.insort_left(self._y_set, statement.turn_interval())

        # build all intersections
        if not intersect:
            return True
        for iv in overlapping:
            self.add(interval_strength(statement, iv), intersect=False)

        return True

    def strengthen_interval_height(self, ):
        i: int = 0
        while i < len(self._x_set):
            updated: bool = False

            offset: int = 1
            while i + offset < len(self._x_set) and self._x_set[i].distance_to(self._x_set[i + offset]) == 0:
                result = interval_strength(self._x_set[i], self._x_set[i + offset])
                added: bool = self.add(result)
                if added:
                    updated = True
                    continue
                offset += 1

            if not updated:
                i += 1

    def remove(self, iv: Interval):
        self._x_set.remove(iv)
        self._y_set.remove(iv.turn_interval())

    def discard(self, iv: Interval):
        self._x_set.remove(iv)
        self._y_set.remove(iv.turn_interval())

    def __contains__(self, iv: Interval) -> bool:
        return iv in self._x_set

    def __len__(self) -> int:
        return len(self._x_set)

    def __iter__(self) -> Iterator:
        return self._x_set.__iter__()

    def overlap_x_iv(self, iv: Interval) -> list[Interval]:
        return IntervalList._overlap(self._x_set, iv.begin, iv.end)

    def overlap_y_iv(self, iv: Interval) -> list[Interval]:
        return IntervalList._overlap(self._y_set, iv.begin, iv.end)

    def overlap_x(self, begin: float, end: float) -> list[Interval]:
        return IntervalList._overlap(self._x_set, begin, end)

    def overlap_y(self, begin: float, end: float) -> list[Interval]:
        return IntervalList._overlap(self._y_set, begin, end)

    @staticmethod
    def _overlap(ivs: list, begin: float, end: float) -> list[Interval]:
        index: int = _bisect_point(ivs, begin)

        lower = index
        if index > 0 and len(ivs) > 0:
            for i in range(index - 1, -1, -1):
                if not ivs[i].overlaps(begin, end):
                    break
                lower = i

        upper = index - 1
        for i in range(index, len(ivs)):
            if ivs[i].begin > end:
                break
            upper = i

        if upper - lower < 0:
            return []
        return ivs[lower:upper+1]

    def envelop_x_iv(self, iv: Interval) -> list[Interval]:
        return IntervalList._envelop(self._x_set, iv.begin, iv.end)

    def envelop_y_iv(self, iv: Interval) -> list[Interval]:
        return IntervalList._envelop(self._y_set, iv.begin, iv.end)

    def envelop_x(self, begin: float, end: float) -> list[Interval]:
        return IntervalList._envelop(self._x_set, begin, end)

    def envelop_y(self, begin: float, end: float) -> list[Interval]:
        return IntervalList._envelop(self._y_set, begin, end)

    @staticmethod
    def _envelop(ivs: list, begin: float, end: float) -> list[Interval]:
        index: int = _bisect_point(ivs, begin)
        if index == len(ivs) and index > 0:
            index -= 1

        envelop: list[Interval] = []
        for i in range(index, len(ivs)):
            if ivs[i].begin > end:
                break
            if ivs[i].enveloped_by(begin, end):
                envelop.append(ivs[i])

        return envelop

    @staticmethod
    def get_enveloped_by_overlap(overlapping, begin, end: int = None) -> list[Interval]:
        if end is None:
            return IntervalList.get_enveloped_by_overlap(overlapping, begin.begin, begin.end)
        return [iv for iv in overlapping if iv.enveloping(begin, end)]

    @staticmethod
    def get_enveloping_overlap(overlapping, begin, end: int = None) -> list[Interval]:
        if end is None:
            return IntervalList.get_enveloping_overlap(overlapping, begin.begin, begin.end)
        return [iv for iv in overlapping if iv.enveloped_by(begin, end)]

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._x_set):
            raise ValueError
        return self._x_set[begin:end]

    def strengthen_interval_height_sides(self):
        i: int = 0
        while i < len(self._x_set):
            updated: bool = False

            # right check
            for offset in range(1, len(self._x_set) - 1 - i):
                if self._x_set[i].distance_to(self._x_set[i + offset]) > 0:
                    break
                result = interval_strength_right(self._x_set[i], self._x_set[i + offset])
                if result is not None:
                    self._x_set[i] = result
                    updated = True

            # left check
            for offset in range(1, i + 1):
                if self._x_set[i - offset].distance_to(self._x_set[i]) > 0:
                    break
                result = interval_strength_left(self._x_set[i - offset], self._x_set[i])
                if result is not None:
                    self._x_set[i] = result
                    updated = True

            if updated and i > 0:
                i -= 1
                continue
            i += 1

    def _strengthen_interval_height_side_left(self):
        i: int = len(self._x_set) - 1
        while i >= 0:
            for offset in range(1, i + 1):
                if self._x_set[i - offset].distance_to(self._x_set[i]) > 0:
                    break
                result = interval_strength_left(self._x_set[i - offset], self._x_set[i])
                if result is not None:
                    self._x_set[i] = result
            i -= 1

    # TODO: I assume no other intersects get created
    def _strengthen_interval_height_side_right(self):
        i: int = 0
        while i < len(self._x_set):
            for offset in range(1, len(self._x_set) - 1 - i):
                if self._x_set[i].distance_to(self._x_set[i + offset]) > 0:
                    break
                result = interval_strength_right(self._x_set[i], self._x_set[i + offset])
                if result is not None:
                    self._x_set[i] = result
            i += 1

    def strengthen_interval_height_side_left(self, sorted_ivs: list[Interval]):
        all_intervals: list[Interval] = sorted_ivs

        i: int = len(all_intervals) - 1
        while i >= 0:
            for offset in range(1, i + 1):
                if all_intervals[i - offset].distance_to(all_intervals[i]) > 0:
                    break
                result = interval_strength_left(all_intervals[i - offset], all_intervals[i])
                added: bool = self.add(result)
                if added:
                    all_intervals[i] = result
            i -= 1

    def strengthen_interval_height_side_right(self, sorted_ivs: list[Interval]):
        all_intervals: list[Interval] = sorted_ivs

        i: int = 0
        while i < len(all_intervals):
            for offset in range(1, len(all_intervals) - 1 - i):
                if all_intervals[i].distance_to(all_intervals[i + offset]) > 0:
                    break
                result = interval_strength_right(all_intervals[i], all_intervals[i + offset])
                added: bool = self.add(result)
                if added:
                    all_intervals[i] = result
            i += 1

    def strengthen_interval_width(self, sorted_ivs: list[Interval], start: float, end: float) \
            -> list[Interval]:
        return self._strengthen_interval_width_short(sorted_ivs, start) if len(sorted_ivs) < 20 else \
            self._strengthen_interval_width_long(sorted_ivs, start, end)

    def _strengthen_interval_width_short(self, all_intervals: list[Interval], start: float) \
            -> list[Interval]:
        i: int = 0
        offset: int = 1
        while i < len(all_intervals):
            if not all_intervals[i].contains_point(start):
                return all_intervals[:i]
            if not i + offset < len(all_intervals) or all_intervals[i].distance_to(all_intervals[i + offset]) > 0:
                i += 1
                offset = 1
                continue

            result = interval_join(all_intervals[i], all_intervals[i + offset])
            added: bool = self.add(result)
            if added:
                index: int = bisect.bisect_left(all_intervals, result)
                all_intervals.insert(index, result)
                continue
            offset += 1

        return all_intervals

    def _strengthen_interval_width_long(self, all_intervals: list[Interval], start: float, end: float) \
            -> list[Interval]:
        match_start: deque = deque()
        for iv in all_intervals:
            if iv.contains_point(start):
                match_start.append(iv)
                continue
            break

        while len(match_start) > 0:
            interval: Interval = match_start.popleft()
            index: int = bisect.bisect_left(all_intervals, interval)
            for i in range(len(all_intervals) - index):
                if index + i < len(all_intervals) and interval.distance_to(all_intervals[index + i]) == 0:
                    result = interval_join(interval, all_intervals[index + i])
                    added: bool = self.add(result)

                    if added:
                        added_index: int = bisect.bisect_left(all_intervals, result)
                        all_intervals.insert(added_index, result)
                        match_start.append(result)
                    continue
                break
            if not (interval.begin <= start and interval.end >= end):
                all_intervals.remove(interval)

        border: int = len(all_intervals)
        for i in range(len(all_intervals)):
            if not all_intervals[i].contains_point(start):
                border = i
                break
        return all_intervals[:border]

    def all_intervals(self):
        return self._x_set

    def all_intervals_turned(self):
        return self._y_set


def _bisect_point(ivs: list, point: float) -> int:
    return bisect.bisect_left(ivs, Interval(point, point, QUALITY_CONS, 0, 0))
