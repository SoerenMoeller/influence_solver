from typing import Union

import solver.rules as rules
import statementstruct.util as util
from statementstruct.statement import Statement


class OverlapMap:
    def __init__(self, statements=None):
        self._statements: set[Statement] = statements if statements is not None else set()
        self._normalized: list[Statement] = []
        self._overlap_map: dict[float, set[Statement]] = {}
        self._boundaries: list[float] = []

        self._initiated: bool = False
        if statements is not None:
            self.initiate()
            self._initiated = True

    def initiate(self):
        if self._initiated:
            return

        self._boundaries: list[float] = util.init_boundaries(self._statements, self._overlap_map)
        for i in range(len(self._boundaries) - 1):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            statement: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._normalized.append(statement)

    def add(self, statement: Statement):
        if statement is None:
            return False
        self._statements.add(statement)
        return True

    def _overlap(self, begin: float, end: float) -> list[Statement]:
        start, end = util.overlapping(self._normalized, begin, end)
        if start == end == -1:
            return []
        return self._normalized[start:end]

    def widest_interval(self, begin: float, end: float) -> Union[Statement, None]:
        statement: list[Statement] = self._overlap(begin, end)
        if not statement:
            return None
        return rules.interval_join_multiple(statement)

    def get_statements(self) -> list[Statement]:
        return self._normalized

    def __len__(self) -> int:
        return len(self._statements)
