import time

from plotter.plotter import plot_statements, show_plot
from statement_containers.overlap_map import OverlapMap
from statement_containers.statement import Statement
from statement_containers.statement_list_dynamic import StatementListDynamic
from statement_containers.statement_list_static import IntervalListStatic
from solver.constants import QUALITY_ANTI, QUALITY_CONS
from solver.dependency_graph import DependencyGraph
from solver.rules import transitivity


class Solver:
    """
    Main class of the Solver, used to build models and check a hyptothesis afterwards.

    Atttibutes
    ----------
    _tmp_statements : dict[tuple, set]
        Used to store statements initially. Main purpose is to maintain 
        statements here in the process of building the model. This is not used in the 
        solving process. Maps variable pairs to sets of statements
    _statements : dict[tuple]
        Maps pairs of variables to sufficient data structures, containing the statements 
        related to those variables. Used in the solving process
    _verbose : int
        1 - Prints timings and data to the console
        2 - Plots models using matplotlib
    _dependency_graph : DependencyGraph
        Graph containing variables and edges representing the presence of statement(s)
        between them. Used for sanity checks and to extract order for using the 
        transitivity rule
    """

    def __init__(self, statements=None, v=None):
        """
        Initialize the solver

        Parameters:
            v (int): Verbose level
            statements (tuple/container[tuple]): statements to add to the model
        """

        self._statements: dict[tuple] = {}
        self._verbose: int = v if v is not None else 0
        self._dependency_graph: DependencyGraph = DependencyGraph()
        self._tmp_statements: dict[tuple, set] = {}

        if statements:
            self.add(statements)

    def add(self, statements):
        """
        Method to add statements to the model

        Parameters:
            statements (tuple/container[tuple]): statement(s) to add to the model
        """

        if type(statements) == tuple and type(statements[0]) != tuple:
            self._add_single_statement(statements)
            return

        self._add_multiple_statements([*statements])

    def remove(self, statement: tuple):
        """
        Method to remove a statement from the model. Throws exception if not present

        Parameters:
            statement (tuple): statement to remove from the model
        """

        selector: tuple[str, str] = statement[0], statement[4]
        if selector not in self._tmp_statements:
            raise ValueError

        self._tmp_statements[selector].remove(statement)

    def discard(self, statement: tuple):
        """
        Method to remove a statement from the model. 

        Parameters:
            statement (tuple): statement to remove from the model
        """

        selector: tuple[str, str] = statement[0], statement[4]
        if selector not in self._tmp_statements:
            return

        self._tmp_statements[selector].remove(statement)

    def _add_single_statement(self, statement: tuple):
        """
        Add a statement to the model. Convert it to the internal form and put it into the (tmp)-container under
        its variable pair

        Parameters:
            statement (tuple): Statement to add to the model
        """

        influencing: str = statement[0]
        influenced: str = statement[4]
        self._dependency_graph.add(influencing, influenced)

        quality: str = statement[2]
        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]

        selector: tuple[str, str] = (influencing, influenced)
        if selector not in self._tmp_statements:
            self._tmp_statements[selector] = set()

        internal_statement: Statement = Statement(interval_x[0], interval_x[1], quality, interval_y[0], interval_y[1])
        self._tmp_statements[selector].add(internal_statement)

    def _add_multiple_statements(self, statements: list[tuple]):
        """
        Adds multiple statements to the model

        Parameters:
            statements (list[tuple]): statements to add
        """

        for statement in statements:
            self._add_single_statement(statement)

    def solve(self, hypothesis: tuple, v=None) -> bool:
        """
        Main method to start the solving method. Takes a hypothesis and tries to prove it using 
        the model and the proof rules. 

        Parameters:
            hypothesis (tuple): Hypothesis to check
            v (int): Verbose level

        Returns:
            (bool): Hypothesis being derivable by the model
        """

        if v is not None:
            self._verbose = v

        # extract data
        adding_time_start: float = time.time()
        influencing: str = hypothesis[0]
        influenced: str = hypothesis[4]
        y_lower, y_upper = hypothesis[3]

        # check special case
        if influencing == influenced:
            return check_reflexive_hypothesis(hypothesis[1], hypothesis[2], hypothesis[3])

        # extract order and initialize models
        order = self._dependency_graph.setup(influencing, influenced)
        used_variables: list[str] = order + [influencing, influenced]
        if (influencing, influenced) not in self._tmp_statements:
            self._tmp_statements[(influencing, influenced)] = set()
        keys: set[tuple] = {key for key in self._tmp_statements if key[0] in used_variables and key[1] in used_variables}
        for key in keys:
            statements: set[Statement] = {st for st in self._tmp_statements[key] if st.overlaps_y(y_lower, y_upper)} \
                if key[1] == influenced else self._tmp_statements[key]
            if key[1] == influenced and key[0] != influencing:
                self._statements[key] = OverlapMap(statements)
                continue
            if key == (influencing, influenced):
                self._statements[key] = StatementListDynamic(hypothesis, statements)
                continue
            self._statements[key] = IntervalListStatic(statements)
        adding_time: float = time.time() - adding_time_start

        solve_time_start: float = time.time()
        if self._verbose >= 3:
            plot_statements(self._tmp_statements, list(self._tmp_statements.keys()))
        start_amount: int = sum(len(self._tmp_statements[ivs]) for ivs in self._tmp_statements)

        # try to solve
        instance = StatementListDynamic.get_instance()
        result, initial_solving_time = instance.solve()
        if result:
            self._print_result(adding_time, time.time() - solve_time_start, initial_solving_time, True, start_amount)
        instance.reset()

        # build transitives
        transitive_time_start: float = time.time()
        self._build_transitive_cover(order, hypothesis)
        transitive_time: float = time.time() - transitive_time_start

        # try solving again
        result, final_solving_time = instance.solve()
        solve_time: float = time.time() - solve_time_start

        self._print_result(adding_time, solve_time, initial_solving_time, result, start_amount,
                           transitive_time, final_solving_time)
        return result

    def _print_result(self, adding_time: float, solve_time: float, initial_solving_time: float, result: bool,
                      amount: int, transitive_time: float = None, final_solving_time: float = None):
        """
        Prints timing data and further information of the solving process 
        """

        instance = StatementListDynamic.get_instance()
        if self._verbose >= 1:
            adding: str = f"Adding statements time:      {adding_time}s"
            total: str = f"Total solving time:          {solve_time}s"
            initial_solving: str = f"Initial solving time:        {initial_solving_time}s"
            building: str = ""
            if transitive_time is not None:
                building = f"Building transitives:        {transitive_time}s"
            final_solving: str = ""
            if final_solving_time is not None:
                final_solving = f"Final solving time:          {final_solving_time}s"
            max_length: int = max(len(total), len(building), len(final_solving), len(adding), len(initial_solving))

            print("\n" + "=" * max_length)
            print(adding)
            print(initial_solving)
            if building:
                print(building)
            if final_solving:
                print(final_solving)
            print(total)
            print("=" * max_length + "\n")

            print(f"Started with {amount} amount of statements in the model")
            print(f"Finished with {len(self)} amount of statements in the model\n")

            print(f"Statement: -{instance.hypothesis}-", end=" ")
            print("can be solved" if result else "is not solvable")

        if self._verbose >= 2:
            plot_statements(self._statements, list(self._statements.keys()))
            show_plot()

    def _build_transitive_cover(self, order: list[str], hypothesis: tuple):
        """
        Build tranistive cover using the extracted order

        Parameters:
            order (list[str]): order of the variables
            hypothesis (tuple): hypothesis containg information about the start/end variables
        """
        goal: str = hypothesis[4]

        for node in order:
            for pre in self._dependency_graph.get_pre(node):
                self._build_transitives(pre, node, goal)
                self._dependency_graph.remove_node(node)

    def _build_transitives(self, a: str, b: str, c: str):
        """
        Build important statements using transitivity rule

        Parameters: 
            a, b, c (str): Variables to use transitivity rule on its statements 
        """

        model_ab: IntervalListStatic = self._statements[(a, b)]
        model_bc: OverlapMap = self._statements[(b, c)]
        model_bc.initiate()
        if (a, c) not in self._statements:
            self._statements[(a, c)] = OverlapMap()

        model_ab.interval_height_and_transitives(self, model_bc, a, c)

    def create_transitive_from_statement(self, st: Statement, model: OverlapMap, a: str, c: str):
        """
        Use transitivity rule on a given statement. Check which statements in the next model overlap the statement 
        and build one enveloping it by using join rule, followed by the transitivity rule

        Parameters:
            st (Statement): statement used in the left side of the transitivity rule
            model (OverlapMap): model containing statements to search in
            a, c (str): variables of the (possibly new) influence
        """
        overlapping = model.slimest_statement(st.begin_y, st.end_y)
        if overlapping is None:
            return
        rule: Statement = transitivity(st, overlapping)
        added: bool = self._statements[(a, c)].add(rule)
        if added:
            self._dependency_graph.add(a, c, check=False)
        return rule

    def __len__(self):
        length: int = 0
        for model in self._statements:
            length += len(self._statements[model])
        return length

    def __str__(self):
        return str(self._statements)


def check_reflexive_hypothesis(x_interval: tuple[float, float], quality: str, y_interval: tuple[float, float]) -> bool:
    if quality in [QUALITY_ANTI, QUALITY_CONS]:
        return False

    return x_interval[0] <= y_interval[0] <= x_interval[1] and x_interval[0] <= y_interval[1] <= x_interval[1]
