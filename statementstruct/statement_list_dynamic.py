import time
from typing import Union

import solver.rules as rules
import statementstruct.util as util
from solver.constants import QUALITY_MONO, SEARCH_LEFT, SEARCH_RIGHT, QUALITY_ANTI, QUALITY_CONS, CORRECT_LOWER, \
    CORRECT_UPPER
from statementstruct.statement import Statement


class StatementListDynamic:
    instance = None

    @staticmethod
    def get_instance():
        return StatementListDynamic.instance

    def __init__(self, statement_init: tuple, ivs: set[Statement]):
        StatementListDynamic.instance = self
        self.statement: tuple = statement_init
        self._all_statements: set[Statement] = ivs
        self._x_set: list[Statement] = []
        self._verbose: int = 1
        self._overlap_map: dict[float, set[Statement]] = {}
        self._boundaries: list[float] = []
        self._overlapping: list[Statement] = []
        self.left_lower: Union[float, None] = None
        self.left_upper: Union[float, None] = None
        self.right_lower: Union[float, None] = None
        self.right_upper: Union[float, None] = None

        self.x_min: float = float("-inf")
        self.x_max: float = float("inf")
        self._ov_min: int = -1
        self._ov_max: int = -1

    def reset(self):
        self._overlap_map = {}
        self._boundaries = []
        self._x_set = []
        self._overlapping = []
        tmp_ivs: set[Statement] = self._all_statements.copy()
        self._all_statements = set()
        for iv in tmp_ivs:
            self.add(iv)

    def solve(self) -> tuple[bool, float]:
        start_time: float = time.time()
        if not self._all_statements:
            return False, time.time() - start_time

        self._overlap_map.clear()
        self._boundaries = util.init_boundaries(self._all_statements, self._overlap_map)
        self._all_statements = set()

        self.strengthen_interval_height()
        return self.check_widest(), time.time() - start_time

    def strengthen_interval_height(self):
        lower, upper = self.statement[1]
        lower_y, upper_y = self.statement[3]
        begin, end = util.get_overlap_index(self._boundaries, lower, upper)
        exceeding_height: list[Statement] = []

        # build overlapping first
        if end > len(self._boundaries):
            end = len(self._boundaries)
        for i in range(begin, end - 1):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])

            if st.exceeds_height(lower_y, upper_y):
                exceeding_height.append(st)

            self._x_set.append(st)
            self._all_statements.add(st)

        if len(exceeding_height) == 0:
            # try to solve
            return

        search_direction_left, correct_bounds_left = get_search_direction(exceeding_height[0], lower_y, upper_y)
        search_direction_right, correct_bounds_right = get_search_direction(exceeding_height[-1], lower_y, upper_y)
        search_left: bool = SEARCH_LEFT in search_direction_left
        search_right: bool = SEARCH_RIGHT in search_direction_right
        if exceeding_height[0] == self._x_set[0] and search_left:
            for i in range(begin - 1, -1, -1):
                point: float = self._boundaries[i]
                if not self._overlap_map[point]:
                    continue

                next_point: float = self._boundaries[i + 1]
                if next_point < self.x_min:
                    break

                st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
                self._x_set.insert(0, st)
                self._all_statements.add(st)

                if CORRECT_UPPER in correct_bounds_left and st.end_y <= upper_y:
                    correct_bounds_left.remove(CORRECT_UPPER)
                if CORRECT_LOWER in correct_bounds_left and st.begin_y >= lower_y:
                    correct_bounds_left.remove(CORRECT_LOWER)
                if not correct_bounds_left:
                    self.x_min = st.end

        if exceeding_height[-1] == self._x_set[-1] and search_right:
            for i in range(end, len(self._boundaries) - 1):
                point: float = self._boundaries[i]
                if not self._overlap_map[point]:
                    continue

                next_point: float = self._boundaries[i + 1]
                if point > self.x_max:
                    break

                st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
                self._x_set.append(st)
                self._all_statements.add(st)

                if CORRECT_UPPER in correct_bounds_right and st.end_y <= upper_y:
                    correct_bounds_right.remove(CORRECT_UPPER)
                if CORRECT_LOWER in correct_bounds_right and st.begin_y >= lower_y:
                    correct_bounds_right.remove(CORRECT_LOWER)
                if not correct_bounds_right:
                    self.x_max = st.begin

        self.strengthen_interval_height_sides()

    def check_widest(self) -> bool:
        overlapping: list[Statement] = self._x_set[self._ov_min:self._ov_max]
        iv: Union[Statement, None] = rules.interval_join_multiple(overlapping)

        result: bool = rules.rule_fact(self.statement, iv)
        if result:
            self._x_set.append(iv)  # This destroys the order of the list, is for visualizing only
        return result

    def add(self, statement: Statement) -> bool:
        if statement is None or statement in self._all_statements:
            return False

        self._all_statements.add(statement)
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


def get_enveloped_by_overlap(overlapping, begin, end: int = None) -> set[Statement]:
    if end is None:
        return get_enveloped_by_overlap(overlapping, begin.begin, begin.end)
    return {iv for iv in overlapping if iv.enveloping(begin, end)}


def get_enveloping_overlap(overlapping, begin, end: int = None) -> set[Statement]:
    if end is None:
        return get_enveloping_overlap(overlapping, begin.begin, begin.end)
    return {iv for iv in overlapping if iv.enveloped_by(begin, end)}


def get_search_direction(statement: Statement, lower_y: float, upper_y: float) -> tuple[set[str], set[str]]:
    search_direction: set[str] = set()
    correcting_bounds: set[str] = set()
    if statement.quality == QUALITY_MONO:
        if statement.begin_y < lower_y:
            search_direction.add(SEARCH_RIGHT)
            correcting_bounds.add(CORRECT_LOWER)
        if statement.end_y > upper_y:
            search_direction.add(SEARCH_LEFT)
            correcting_bounds.add(CORRECT_UPPER)
    if statement.quality == QUALITY_ANTI:
        if statement.begin_y < lower_y:
            search_direction.add(SEARCH_LEFT)
            correcting_bounds.add(CORRECT_LOWER)
        if statement.end_y > upper_y:
            search_direction.add(SEARCH_RIGHT)
            correcting_bounds.add(CORRECT_UPPER)
    if statement.quality == QUALITY_CONS and (statement.begin_y < lower_y or statement.end_y > upper_y):
        search_direction.update({SEARCH_LEFT, SEARCH_RIGHT})
        correcting_bounds.update({CORRECT_LOWER, CORRECT_UPPER})

    return search_direction, correcting_bounds
