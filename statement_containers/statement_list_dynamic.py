import time
from typing import Union

import solver.rules as rules
import statement_containers.util as util
from solver.constants import QUALITY_MONO, SEARCH_LEFT, SEARCH_RIGHT, QUALITY_ANTI, QUALITY_CONS, CORRECT_LOWER, \
    CORRECT_UPPER
from statement_containers.statement import Statement


class StatementListDynamic:
    """
    Container for statements related to variable pair (a, b), where 
    b is the influenced variable of the hypothesis and a is the influencing 
    variable of the hypothesis. This class is used for checking the hypothesis
    before and after the transitive cover has been build. For that, the normalized 
    model can be reset to further add statements. The search area can be shrinked to 
    allow only adding the most important statements for solving

    Attributes
    ----------
    instance : StatementListDynamic
        (only) instance of this class
    statements : set[Statement]
        container of the added statements
    hypothesis : tuple
        hypothesis to check
    _normalized : list[Statement]
        container of statements after normalization process
    _overlap_map : dict[float, set[Statement]]
        maps boundaries to overlapping statements
    _boundaries : list[float]
        all boundaries in the model
    x_min : float
        minimum x value to consider for solving
    x_max : float
        maximum x value to consider for solving
    _ov_min : int
        index of lowest (in order) statement overlapping the hypothesis
    _ov_max: int
        index of highest (in order) statement overlapping the hypothesis
    """

    instance = None

    @staticmethod
    def get_instance():
        return StatementListDynamic.instance

    def __init__(self, hypothesis: tuple, statements: set[Statement]):
        StatementListDynamic.instance = self
        self.hypothesis: tuple = hypothesis
        self.statements: set[Statement] = statements
        self._normalized: list[Statement] = []
        self._overlap_map: dict[float, set[Statement]] = {}
        self._boundaries: list[float] = []

        self.x_min: float = float("-inf")
        self.x_max: float = float("inf")
        self._ov_min: int = -1
        self._ov_max: int = -1

    def reset(self):
        """
        Reset the normilaization
        """

        self._overlap_map = {}
        self._boundaries = []
        self._normalized = []
        tmp_sts: set[Statement] = self.statements.copy()
        self.statements = set()
        for st in tmp_sts:
            self.add(st)

    def solve(self) -> tuple[bool, float]:
        """
        Try solving the hypothesis in the given model, by extracting the statements overlapping it 
        and trying to shrink their height as much as possible

        Returns:
            (bool): indicating if the hypothesis can be proven
            (float): running time information 
        """

        start_time: float = time.time()
        if not self.statements:
            return False, time.time() - start_time

        self._overlap_map.clear()
        self._boundaries = util.init_boundaries(self.statements, self._overlap_map)
        self.statements = set()

        self.build_necessary_statements()
        return self.check_slimest_envelopping(), time.time() - start_time

    def build_necessary_statements(self):
        """
        Check statements overlapping hypethesis and search as many statements needed to possibly decrease their height 
        as low as needed (envoloped by hypothesis)
        """

        lower, upper = self.hypothesis[1]
        lower_y, upper_y = self.hypothesis[3]

        if len(self._boundaries) > 0 and self._boundaries[0] > lower or self._boundaries[-1] < upper:
            pass

        begin, end = util.get_overlap_index(self._boundaries, lower, upper)
        exceeding_height: list[Statement] = []

        # build overlapping first
        if end > len(self._boundaries):
            end = len(self._boundaries)

        # build area overlapping the hypothesis
        self._ov_min = 0
        self._ov_max = end
        for i in range(begin, end):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])

            if st.exceeds_height(lower_y, upper_y):
                exceeding_height.append(st)

            self._normalized.append(st)
            self.statements.add(st)

        if len(exceeding_height) == 0:
            # try to solve
            return

        # extract search information
        search_direction_left, correct_bounds_left = get_search_direction(exceeding_height[0], lower_y, upper_y)
        search_direction_right, correct_bounds_right = get_search_direction(exceeding_height[-1], lower_y, upper_y)
        search_left: bool = SEARCH_LEFT in search_direction_left
        search_right: bool = SEARCH_RIGHT in search_direction_right

        # add left statements
        if exceeding_height[0] == self._normalized[0] and search_left:
            for i in range(begin - 1, -1, -1):
                point: float = self._boundaries[i]
                if not self._overlap_map[point]:
                    continue

                next_point: float = self._boundaries[i + 1]
                if next_point < self.x_min:
                    break

                st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
                self._normalized.insert(0, st)
                self.statements.add(st)

                # correct area overlapping the hypothesis
                self._ov_min += 1
                self._ov_max += 1

                # check bounds correction
                if CORRECT_UPPER in correct_bounds_left and st.end_y <= upper_y:
                    correct_bounds_left.remove(CORRECT_UPPER)
                if CORRECT_LOWER in correct_bounds_left and st.begin_y >= lower_y:
                    correct_bounds_left.remove(CORRECT_LOWER)
                if not correct_bounds_left:
                    self.x_min = st.end

        # add right statements
        if exceeding_height[-1] == self._normalized[-1] and search_right:
            for i in range(end, len(self._boundaries) - 1):
                point: float = self._boundaries[i]
                if not self._overlap_map[point]:
                    continue

                next_point: float = self._boundaries[i + 1]
                if point > self.x_max:
                    break

                st: Statement = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
                self._normalized.append(st)
                self.statements.add(st)

                # check bounds correction
                if CORRECT_UPPER in correct_bounds_right and st.end_y <= upper_y:
                    correct_bounds_right.remove(CORRECT_UPPER)
                if CORRECT_LOWER in correct_bounds_right and st.begin_y >= lower_y:
                    correct_bounds_right.remove(CORRECT_LOWER)
                if not correct_bounds_right:
                    self.x_max = st.begin

        self.strengthen_interval_height_sides()

    def check_slimest_envelopping(self) -> bool:
        """
        check if the slimest statement enveloppig the hypothesis can prove the hypothesis.
        Join the overlapping ones together for that

        Returns:
            (bool): result of the fact rule
        """

        if self._ov_max == -1 or self._ov_min == -1:
            return False
        overlapping: list[Statement] = self._normalized[self._ov_min:self._ov_max]
        statement: Union[Statement, None] = rules.interval_join_multiple(overlapping)

        result: bool = rules.rule_fact(self.hypothesis, statement)
        if result:
            self._normalized.append(statement)  # This destroys the order of the list, is for visualizing only
        return result

    def add(self, statement: Statement) -> bool:
        """
        Add a statement to the model

        Parameters:
            statement (Statement): statement to add
        
        Returns:
            (bool): indicating if adding was a success
        """

        if statement is None or statement in self.statements:
            return False

        self.statements.add(statement)
        return True

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

    def get_statements(self):
        return self._normalized

    def __len__(self) -> int:
        return len(self._normalized)


def get_enveloped_by_overlap(overlapping, begin, end: int = None) -> set[Statement]:
    if end is None:
        return get_enveloped_by_overlap(overlapping, begin.begin, begin.end)
    return {st for st in overlapping if st.enveloping(begin, end)}


def get_enveloping_overlap(overlapping, begin, end: int = None) -> set[Statement]:
    if end is None:
        return get_enveloping_overlap(overlapping, begin.begin, begin.end)
    return {st for st in overlapping if st.enveloped_by(begin, end)}


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
