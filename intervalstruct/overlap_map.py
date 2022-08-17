import bisect
from collections import deque
from itertools import chain
from typing import Union

from intervalstruct.interval import Interval
import intervalstruct.util as util
import solver.rules as rules
from solver.constants import QUALITY_CONS


class OverlapMap:
    def __init__(self, ivs=None):
        self._ivs: set[Interval] = ivs if ivs is not None else set()
        self._x_set: list[Interval] = []
        self._overlap_map: dict[float, set[Interval]] = {}
        self._boundaries: list[float] = []

        self._initiated: bool = False
        if ivs is not None:
            self.initiate()
            self._initiated = True

    def initiate(self):
        if self._initiated:
            return

        self._boundaries: list[float] = util.init_boundaries(self._ivs, self._overlap_map)
        for i in range(len(self._boundaries) - 1):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.append(iv)

    def _overlap(self, begin: float, end: float) -> list[Interval]:
        index = bisect.bisect_left(self._x_set, Interval(begin, begin, QUALITY_CONS, 0, 0))

        lower = index
        if index > 0 and len(self._x_set) > 0:
            for i in range(index - 1, -1, -1):
                if not self._x_set[i].overlaps(begin, end):
                    break
                lower = i

        upper = index - 1
        for i in range(index, len(self._x_set)):
            if self._x_set[i].begin > end:
                break
            upper = i

        if upper - lower < 0:
            return []
        return self._x_set[lower:upper+1]

    def widest_interval(self, begin: float, end: float) -> Union[Interval, None]:
        ivs: list[Interval] = self._overlap(begin, end)
        if not ivs:
            return None
        return rules.interval_join_multiple(ivs)

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

            result = rules.interval_join(all_intervals[i], all_intervals[i + offset])
            add: bool = _better_than_existing(result, all_intervals)
            if add:
                bisect.insort_left(all_intervals, result)
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
                    result = rules.interval_join(interval, all_intervals[index + i])
                    add: bool = _better_than_existing(result, all_intervals)

                    if add:
                        bisect.insort_left(all_intervals, result)
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

    def __len__(self) -> int:
        return len(self._ivs)

    def intervals(self) -> list[Interval]:
        return self._x_set

    def intervals_turned(self) -> list[Interval]:
        return sorted(iv.turn_interval() for iv in self._x_set)


def _better_than_existing(interval: Interval, intervals: list[Interval]) -> bool:
    if interval is None:
        return False
    return [iv for iv in intervals if iv.stronger_as(interval)] == []
