from typing import Union

import solver.rules as rules
import statementstruct.util as util
from statementstruct.statement import Statement


class OverlapMap:
    def __init__(self, ivs=None):
        self._ivs: set[Statement] = ivs if ivs is not None else set()
        self._x_set: list[Statement] = []
        self._overlap_map: dict[float, set[Statement]] = {}
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
            iv: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.append(iv)

    def add(self, iv: Statement):
        if iv is None:
            return False
        self._ivs.add(iv)
        return True

    def _overlap(self, begin: float, end: float) -> list[Statement]:
        start, end = util.overlapping(self._x_set, begin, end)
        if start == end == -1:
            return []
        return self._x_set[start:end]

    def widest_interval(self, begin: float, end: float) -> Union[Statement, None]:
        ivs: list[Statement] = self._overlap(begin, end)
        if not ivs:
            return None
        return rules.interval_join_multiple(ivs)

    def __len__(self) -> int:
        return len(self._ivs)

    def intervals(self) -> list[Statement]:
        return self._x_set

    def intervals_turned(self) -> list[Statement]:
        return sorted(iv.turn_interval() for iv in self._x_set)
