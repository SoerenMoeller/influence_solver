import solver.rules as rules
import statement_containers.util as util
from solver.constants import CORRECT_UPPER, CORRECT_LOWER
from statement_containers.statement import Statement
from statement_containers.statement_list_dynamic import StatementListDynamic


class IntervalListStatic:
    """
    Container for statements of variables pairs, that are not covered by static_list_dynamic nor
    overlap_map

    Attributes
    ----------
    _normalized : list[Statement]
        container of statements after normalization process
    _overlap_map : dict[float, set[Statement]]
        maps boundaries to overlapping statements
    _boundaries : list[float]
        all boundaries in the model
    """

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

    def get_statements_by_index(self, begin, end=None):
        """
        get statements of the normalized model using indices
        """
        if end is None:
            return self.get_statements_by_index(begin[0], begin[1])

        if begin < 0 or end > len(self._normalized):
            raise ValueError
        return self._normalized[begin:end]

    def strengthen_interval_height_sides(self):
        util.strengthen_interval_height_sides(self._normalized)

    def interval_height_and_transitives(self, solver, model, a: str, c: str):
        """
        Lower the height of the statements in the area relevant for the hypothesis and 
        try to only build the relevant one (in the same manner as in statement_list_dynamic)

        Parameters:
            solver (Solver): solver object
            model: model containing statements to use transitivity rule with
            a, c (str): transitive influence
        """
        
        instance: StatementListDynamic = StatementListDynamic.get_instance()
        lower, upper = instance.hypothesis[1]
        lower_y, upper_y = instance.hypothesis[3]
        begin, end = util.overlapping(self._normalized, lower, upper)  
        if begin == end == -1:
            return

        correct_left: set[str] = set()
        correct_right: set[str] = set()

        # build overlapping first
        if end > len(self._normalized):
            end = len(self._normalized)
        for i in range(begin, end):
            st: Statement = self._normalized[i]
            new_st: Statement = solver.create_transitive_from_statement(st, model, a, c)

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

                new_st: Statement = solver.create_transitive_from_statement(st, model, a, c)

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

                new_st: Statement = solver.create_transitive_from_statement(st, model, a, c)

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
