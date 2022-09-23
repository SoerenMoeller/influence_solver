import solver.rules as rules
import statementstruct.util as util
from solver.constants import CORRECT_UPPER, CORRECT_LOWER
from statementstruct.overlap_map import OverlapMap
from statementstruct.statement import Statement
from statementstruct.statement_list_dynamic import StatementListDynamic


class IntervalListStatic:
    def __init__(self, ivs):
        self._x_set: list[Statement] = []
        self._connection_set: list[Statement] = []
        self._verbose: int = 1

        self._overlap_map: dict[float, set[Statement]] = {}
        self._boundaries: list[float] = util.init_boundaries(ivs, self._overlap_map)

        # init model
        for i in range(len(self._boundaries) - 1):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]

            st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.append(st)

        self.strengthen_interval_height_sides()

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

    def interval_height_and_transitives(self, solver, model: OverlapMap, a: str, c: str):
        instance: StatementListDynamic = StatementListDynamic.get_instance()
        lower, upper = instance.statement[1]
        lower_y, upper_y = instance.statement[3]
        begin, end = util.overlapping(self._x_set, lower, upper)
        if begin == end == -1:
            return

        correct_left: set[str] = set()
        correct_right: set[str] = set()
        # build overlapping first
        if end > len(self._x_set):
            end = len(self._x_set)
        for i in range(begin, end):
            st: Statement = self._x_set[i]
            new_st: Statement = solver.create_transitive_from_interval(st, model, a, c)

            if new_st is not None and new_st.overlaps(lower):
                if new_st.begin_y < lower_y:
                    correct_left.add(CORRECT_LOWER)
                if new_st.end_y < upper_y:
                    correct_left.add(CORRECT_UPPER)
            if new_st is not None and new_st.overlaps(upper):
                if new_st.begin_y < lower_y:
                    correct_right.add(CORRECT_LOWER)
                if new_st.end_y < upper_y:
                    correct_right.add(CORRECT_UPPER)

        if correct_left:
            for i in range(begin - 1, -1, -1):
                st: Statement = self._x_set[i]
                if st.end < instance.x_min:
                    break

                new_st: Statement = solver.create_transitive_from_interval(st, model, a, c)

                if new_st is not None:
                    if CORRECT_LOWER in correct_left and new_st.begin_y >= lower_y:
                        correct_left.remove(CORRECT_LOWER)
                    if CORRECT_UPPER in correct_left and new_st.end_y <= upper_y:
                        correct_left.remove(CORRECT_UPPER)
                    if not correct_left:
                        instance.x_min = st.end
                        break

        if correct_right:
            for i in range(end, len(self._x_set)):
                st: Statement = self._x_set[i]
                if st.begin > instance.x_max:
                    break

                new_st: Statement = solver.create_transitive_from_interval(st, model, a, c)

                if new_st is not None:
                    if CORRECT_LOWER in correct_right and new_st.begin_y >= lower_y:
                        correct_left.remove(CORRECT_LOWER)
                    if CORRECT_UPPER in correct_right and new_st.end_y <= upper_y:
                        correct_right.remove(CORRECT_UPPER)
                    if not correct_right:
                        instance.x_max = st.begin
                        break

    def strengthen_interval_height_sides_last(self):
        i = len(self._x_set) - 2 if len(self._x_set) > 2 else 0

        while i < len(self._x_set):
            changed: bool = False
            if i < len(self._x_set) - 1:
                iv: Statement = rules.interval_strength_right(self._x_set[i], self._x_set[i + 1])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if i > 0:
                iv: Statement = rules.interval_strength_left(self._x_set[i - 1], self._x_set[i])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if changed:
                i -= 1
                continue
            i += 1

    def strengthen_interval_height_sides_first(self):
        i = 1 if len(self._x_set) > 0 else 0

        while i >= 0:
            changed: bool = False
            if i < len(self._x_set) - 1:
                iv: Statement = rules.interval_strength_right(self._x_set[i], self._x_set[i + 1])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if i > 0:
                iv: Statement = rules.interval_strength_left(self._x_set[i - 1], self._x_set[i])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if changed:
                i += 1
                continue
            i -= 1

    def intervals(self) -> list[Statement]:
        return self._x_set

    def intervals_turned(self) -> list[Statement]:
        return sorted({iv.turn_interval() for iv in self._x_set})
