from typing import Union

import solver.rules as rules
import statement_containers.util as util
from statement_containers.statement import Statement


class OverlapMap:
    """
    Container for statements related to variable pair (a, b), where 
    b is the influenced variable of the hypothesis and a is not the influencing 
    variable of the hypothesis

    Attributes
    ----------
    _statements : set[Statement]
        container of the initially added statements
    _normalized : list[Statement]
        container of statements after normalization process
    _overlap_map : dict[float, set[Statement]]
        maps boundaries to overlapping statements
    _boundaries (list[float]
        all boundaries in the model
    _initiated : bool
        indicates that the building of the container is done and the normalized ones are extracted
    """


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
        """
        Build the normalized statements of the model
        """

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
        """
        Add a statement to the container

        Parameters:
            statement (Statement): statement to add
        """

        if statement is None:
            return False
        self._statements.add(statement)
        return True

    def _overlap(self, begin: float, end: float) -> list[Statement]:
        """
        Check which statements overlap a given area

        Parameters: 
            begin, end (float): [begin, end] interval to check overlap for 
        """

        start, end = util.overlapping(self._normalized, begin, end)
        if start == end == -1:
            return []
        return self._normalized[start:end]

    def slimest_statement(self, begin: float, end: float) -> Union[Statement, None]:
        """
        Build the slimest statement envelopping a given area, by joining overlapping ones together

        Parameters:
            begin, end (float): [begin, end] interval to check overlap for 
        
        Returns:
            (Statement): slimest statement enveloping the given area
        """
        
        statement: list[Statement] = self._overlap(begin, end)
        if not statement:
            return None
        return rules.interval_join_multiple(statement)

    def get_statements(self) -> list[Statement]:
        return self._normalized

    def __len__(self) -> int:
        return len(self._statements)
