import bisect
from collections import deque
from collections.abc import MutableSet
from typing import Iterator

from intervalstruct.interval import Interval
from solver.constants import QUALITY_CONS
from solver.rules import interval_strength_left, interval_strength_right, interval_join, \
    interval_strength_multiple
from solver.util import is_stronger_as


class IntervalListDynamic(MutableSet):
    def __init__(self, statement: tuple, ivs=None):
        self._statement = statement
        self._x_set: list[Interval] = sorted(ivs) if ivs is not None else []
        self._verbose: int = 1

        self._overlap_map: dict[float, set[Interval]] = {}
        tmp_boundaries: set[float] = set()
        for iv in self._x_set:
            if iv.begin not in self._overlap_map:
                self._overlap_map[iv.begin] = set()
                tmp_boundaries.add(iv.begin)
            if iv.end not in self._overlap_map:
                self._overlap_map[iv.end] = set()
                tmp_boundaries.add(iv.end)
            self._overlap_map[iv.begin].add(iv)
            self._overlap_map[iv.end].add(iv)

        # TODO: cleanup
        self._boundaries: list[float] = sorted(tmp_boundaries)
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

        self.solve()

    def solve(self):
        self.strengthen_interval_height()
        self.strengthen_interval_height_sides()

    def add(self, statement: Interval, height=None) -> bool:
        if statement is None or self.ins(self._x_set, statement):
            return False

        if statement.begin_other == statement.end_other:
            statement = Interval(statement.begin, statement.end, QUALITY_CONS, statement.begin_other,
                                 statement.end_other)

        overlapping: list[Interval] = self.overlap_x_iv(statement)
        enveloping: list[Interval] = IntervalListDynamic.get_enveloping_overlap(overlapping, statement)
        enveloped_by: list[Interval] = IntervalListDynamic.get_enveloped_by_overlap(overlapping, statement)

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

        bisect.insort_left(self._x_set, statement)
        return True

    def __contains__(self, key):
        i = bisect.bisect_left(self._x_set, key)
        return i != len(self._x_set) and self._x_set[i] == key

    """
    def remove_envelop(self):
        going = True
        while going:
            for i in range(len(self._x_set)):
                iv: Interval = self._x_set[i]
                x = False
                for offset in range(1, len(self._x_set) - 1 - i):
                    other_iv: Interval = self._x_set[i + offset]
                    if not iv.overlaps(other_iv):
                        break
                    if iv.enveloping(other_iv) and iv.begin != other_iv.begin and iv.end != other_iv.end:
                        result = interval_strength_2(iv, other_iv)
                        self._x_set.remove(iv)
                        self._x_set.remove(other_iv)
                        for iv in result:
                            bisect.insort_left(self._x_set, iv)
                        x = True
                        print("changed")
                        break
                if x:
                    break
                if i == len(self._x_set) - 1:
                    going = False
    """

    # TODO: Edge case only one iv?
    def strengthen_interval_height(self):
        self._x_set = []
        for i in range(len(self._boundaries) - 1):
            start: float = self._boundaries[i]
            if not self._overlap_map[start]:
                continue

            end: float = self._boundaries[i + 1]
            iv: Interval = interval_strength_multiple(start, end, self._overlap_map[start])
            self._x_set.append(iv)

    def remove(self, iv: Interval):
        self._x_set.remove(iv)

    def discard(self, iv: Interval):
        self._x_set.remove(iv)

    def __contains__(self, iv: Interval) -> bool:
        return iv in self._x_set

    def __len__(self) -> int:
        return len(self._x_set)

    def __iter__(self) -> Iterator:
        return self._x_set.__iter__()

    def overlap_x_iv(self, iv: Interval) -> list[Interval]:
        return IntervalList._overlap(self._x_set, iv.begin, iv.end)

    def overlap_x(self, begin: float, end: float) -> list[Interval]:
        return IntervalList._overlap(self._x_set, begin, end)

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
        return ivs[lower:upper + 1]

    def envelop_x_iv(self, iv: Interval) -> list[Interval]:
        return IntervalList._envelop(self._x_set, iv.begin, iv.end)

    def envelop_x(self, begin: float, end: float) -> list[Interval]:
        return IntervalList._envelop(self._x_set, begin, end)

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

    def _strengthen_interval_height_side_left(self):
        i: int = len(self._x_set) - 1
        while i >= 0:
            for offset in range(1, i + 1):
                if self._x_set[i - offset].distance_to(self._x_set[i]) > 0:
                    break
                result = interval_strength_left(self._x_set[i - offset], self._x_set[i])
                self.add(result)
                # if result is not None:
                #    self._x_set[i] = result
            i -= 1

    # TODO: I assume no other intersects get created
    def _strengthen_interval_height_side_right(self):
        i: int = 0
        while i < len(self._x_set):
            for offset in range(1, len(self._x_set) - 1 - i):
                if self._x_set[i].distance_to(self._x_set[i + offset]) > 0:
                    break
                result = interval_strength_right(self._x_set[i], self._x_set[i + offset])
                self.add(result)
                # if result is not None:
                #    self._x_set[i] = result
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

    def intervals(self):
        return self._x_set

    def intervals_turned(self):
        return sorted({iv.turn_interval() for iv in self._x_set})
