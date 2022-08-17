import time

from intervalstruct.interval import Interval
from intervalstruct.interval_list_dynamic import IntervalListDynamic
from intervalstruct.interval_list_static import IntervalListStatic
from intervalstruct.overlap_map import OverlapMap
from plotter.plotter import plot_statements, show_plot
from .dependency_graph import DependencyGraph
from .rules import transitivity


# TODO: Reflexive rule, Add reflexive statements?, Consistency?
# TODO: Höhe null -> Konstant / ARB rausschmeißen


class Solver:
    _intervals: dict[tuple] = {}
    _verbose: int = 1
    _dependency_graph: DependencyGraph = DependencyGraph()
    _tmp_intervals: dict[tuple, set] = {}
    _statement: tuple[str, tuple[float, float], str, tuple[float, float], str]

    def __init__(self, intervals=None):
        if intervals is None:
            return

        self.add_intervals(intervals)

    def add_intervals(self, intervals):
        if type(intervals) == tuple and type(intervals[0]) != tuple:
            self._add_single_interval(intervals)
            return

        self._add_multiple_intervals([*intervals])

    def add_interval(self, interval):
        assert type(interval) == tuple and type(interval[0]) != tuple

        self._add_single_interval(interval)

    def _add_single_interval(self, interval: tuple):
        influencing: str = interval[0]
        influenced: str = interval[4]
        self._dependency_graph.add(influencing, influenced)

        quality: str = interval[2]
        interval_x: tuple[float, float] = interval[1]
        interval_y: tuple[float, float] = interval[3]

        selector: tuple[str, str] = (influencing, influenced)
        if selector not in self._tmp_intervals:
            self._tmp_intervals[selector] = set()

        interval: Interval = Interval(interval_x[0], interval_x[1], quality, interval_y[0], interval_y[1])
        self._tmp_intervals[selector].add(interval)

    def _add_multiple_intervals(self, intervals: list[tuple]):
        for interval in intervals:
            self._add_single_interval(interval)

    def solve(self, statement: tuple) -> bool:
        adding_time_start: float = time.time()

        influencing: str = statement[0]
        influenced: str = statement[4]
        y_lower, y_upper = statement[3]
        order = self._dependency_graph.setup(influencing, influenced)

        used_variables: list[str] = order + [influencing, influenced]
        if (influencing, influenced) not in self._tmp_intervals:
            self._tmp_intervals[(influencing, influenced)] = set()
        keys: set[tuple] = {key for key in self._tmp_intervals if key[0] in used_variables and key[1] in used_variables}
        for key in keys:
            intervals: set[Interval] = {iv for iv in self._tmp_intervals[key] if
                                        iv.turn_interval().overlaps(y_lower, y_upper)} \
                if key[1] == influenced else self._tmp_intervals[key]
            if key[1] == influenced and key[0] != influencing:
                self._intervals[key] = OverlapMap(intervals)
                continue
            if key[1] == influenced and key[0] == influencing:
                self._intervals[key] = IntervalListDynamic(statement, intervals)
                continue
            self._intervals[key] = IntervalListStatic(intervals)
        adding_time: float = time.time() - adding_time_start

        solve_time_start: float = time.time()
        if self._verbose >= 3:
            plot_statements(self._tmp_intervals, list(self._tmp_intervals.keys()))
        start_amount: int = sum(len(self._tmp_intervals[ivs]) for ivs in self._tmp_intervals)

        instance = IntervalListDynamic.get_instance()
        result, initial_solving_time = instance.solve()
        if result:
            self._print_result(adding_time, time.time() - solve_time_start, initial_solving_time, True, start_amount)
        instance.reset()

        # build transitives
        transitive_time_start: float = time.time()
        self._build_transitive_cover(order, statement)
        transitive_time: float = time.time() - transitive_time_start

        result, final_solving_time = instance.solve()
        solve_time: float = time.time() - solve_time_start

        self._print_result(adding_time, solve_time, initial_solving_time, result, start_amount,
                           transitive_time, final_solving_time)
        return result

    def _print_result(self, adding_time: float, solve_time: float, initial_solving_time: float, result: bool,
                      amount: int, transitive_time: float = None, final_solving_time: float = None):
        instance = IntervalListDynamic.get_instance()
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
            print(building)
            print(final_solving)
            print(total)
            print("=" * max_length + "\n")

            print(f"Started with {amount} amount of statements in the model")
            print(f"Finished with {len(self)} amount of statements in the model\n")

            print(f"Statement: -{instance.statement}-", end=" ")
            print("can be solved" if result else "is not solvable")

        if self._verbose >= 3:
            plot_statements(self._intervals, list(self._intervals.keys()))
            show_plot()

    def _build_transitive_cover(self, order: list[str], statement: tuple):
        goal: str = statement[4]

        for node in order:
            for pre in self._dependency_graph.get_pre(node):
                self._build_transitives(pre, node, goal)
                self._dependency_graph.remove_node(node)

    def _build_transitives(self, a: str, b: str, c: str):
        model_ab: IntervalListStatic = self._intervals[(a, b)]
        model_bc: OverlapMap = self._intervals[(b, c)]
        model_bc.initiate()
        if (a, c) not in self._intervals:
            self._intervals[(a, c)] = OverlapMap()

        if model_ab.intervals_created():
            for interval in model_ab.intervals():
                self.create_transitive_from_interval(interval, model_bc, a, c)
            return

        model_ab.interval_height_and_transitives(self, model_bc, a, c)

    def create_transitive_from_interval(self, iv: Interval, model: OverlapMap, a: str, c: str):
        overlapping = model.widest_interval(iv.begin_other, iv.end_other)
        if overlapping is None:
            return
        rule: Interval = transitivity(iv, overlapping)
        added: bool = self._intervals[(a, c)].add(rule)
        if added:
            self._dependency_graph.add(a, c, check=False)
        return rule

    def __len__(self):
        length: int = 0
        for model in self._intervals:
            length += len(self._intervals[model])
        return length

    def __str__(self):
        return str(self._intervals)
