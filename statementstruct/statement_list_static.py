import solver.rules as rules
import statementstruct.util as util
from solver.constants import CORRECT_UPPER, CORRECT_LOWER
from statementstruct.statement import Statement
from statementstruct.statement_list_dynamic import StatementListDynamic


class IntervalListStatic:
    def __init__(self, ivs):
        self._normalized: list[Statement] = []
        self._overlap_map: dict[float, set[Statement]] = {}
        self._boundaries: list[float] = util.init_boundaries(ivs, self._overlap_map)

        # init model
        for i in range(len(self._boundaries) - 1):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]

            st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._normalized.append(st)

        self.strengthen_interval_height_sides()

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._normalized):
            raise ValueError
        return self._normalized[begin:end]

    def strengthen_interval_height_sides(self):
        util.strengthen_interval_height_sides(self._normalized)

    def interval_height_and_transitives(self, solver, model, a: str, c: str):
        instance: StatementListDynamic = StatementListDynamic.get_instance()
        lower, upper = instance.hypothesis[1]
        lower_y, upper_y = instance.hypothesis[3]
        begin, end = util.overlapping(self._normalized, lower, upper)  # TODO: Fix?
        if begin == end == -1:
            return

        correct_left: set[str] = set()
        correct_right: set[str] = set()

        # build overlapping first
        if end > len(self._normalized):
            end = len(self._normalized)
        for i in range(begin, end):
            st: Statement = self._normalized[i]
            new_st: Statement = solver.create_transitive_from_interval(st, model, a, c)

            # check if correction is needed
            if new_st is not None and new_st.contains_point(lower):
                if new_st.begin_y < lower_y:
                    correct_left.add(CORRECT_LOWER)
                if new_st.end_y < upper_y:
                    correct_left.add(CORRECT_UPPER)
            if new_st is not None and new_st.contains_point(upper):
                if new_st.begin_y < lower_y:
                    correct_right.add(CORRECT_LOWER)
                if new_st.end_y < upper_y:
                    correct_right.add(CORRECT_UPPER)

        if correct_left:
            for i in range(begin - 1, -1, -1):
                st: Statement = self._normalized[i]
                if st.end < instance.x_min:
                    break

                new_st: Statement = solver.create_transitive_from_interval(st, model, a, c)

                # check if bound is corrected
                if new_st is not None:
                    if CORRECT_LOWER in correct_left and new_st.begin_y >= lower_y:
                        correct_left.remove(CORRECT_LOWER)
                    if CORRECT_UPPER in correct_left and new_st.end_y <= upper_y:
                        correct_left.remove(CORRECT_UPPER)
                    if not correct_left:
                        instance.x_min = st.end
                        break

        if correct_right:
            for i in range(end, len(self._normalized)):
                st: Statement = self._normalized[i]
                if st.begin > instance.x_max:
                    break

                new_st: Statement = solver.create_transitive_from_interval(st, model, a, c)

                # check if bound is corrected
                if new_st is not None:
                    if CORRECT_LOWER in correct_right and new_st.begin_y >= lower_y:
                        correct_left.remove(CORRECT_LOWER)
                    if CORRECT_UPPER in correct_right and new_st.end_y <= upper_y:
                        correct_right.remove(CORRECT_UPPER)
                    if not correct_right:
                        instance.x_max = st.begin
                        break

    def get_statements(self) -> list[Statement]:
        return self._normalized

    def __len__(self) -> int:
        return len(self._normalized)
