import bisect
from typing import Union

import intervalstruct.util as util
import solver.rules as rules
from intervalstruct.interval import Interval
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

    def add(self, iv: Interval):
        if iv is None:
            return False
        self._ivs.add(iv)
        return True

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
        return self._x_set[lower:upper + 1]

    def widest_interval(self, begin: float, end: float) -> Union[Interval, None]:
        ivs: list[Interval] = self._overlap(begin, end)
        if not ivs:
            return None
        return rules.interval_join_multiple(ivs)

    def __len__(self) -> int:
        return len(self._ivs)

    def intervals(self) -> list[Interval]:
        return self._x_set

    def intervals_turned(self) -> list[Interval]:
        return sorted(iv.turn_interval() for iv in self._x_set)
