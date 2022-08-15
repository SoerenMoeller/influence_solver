import bisect
import time
from collections import deque

from intervalstruct.interval_list_static import IntervalListStatic
from intervalstruct.intervaltree import IntervalTree
from intervalstruct.interval_list_dynamic import IntervalListDynamic
from plotter.plotter import plot_statements, show_plot
from .dependency_graph import DependencyGraph
from .rules import *

# TODO: Reflexive rule, Add reflexive statements?, Consistency?
# TODO: Höhe null -> Konstant / ARB rausschmeißen
from .util import get_overlap_index

# TODO: initial solving time, final solving time
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
        quality: str = statement[2]
        x_lower, x_upper = statement[1]
        y_lower, y_upper = statement[3]
        order, paths = self._dependency_graph.setup(influencing, influenced)

        used_variables: list[str] = order + [influencing, influenced]
        if (influencing, influenced) not in self._tmp_intervals:
            self._tmp_intervals[(influencing, influenced)] = set()
        keys: set[tuple] = {key for key in self._tmp_intervals if key[0] in used_variables and key[1] in used_variables}
        for key in keys:
            intervals: set[Interval] = {iv for iv in self._tmp_intervals[key] if
                                        iv.turn_interval().overlaps(y_lower, y_upper)} \
                if key[1] == influenced else self._tmp_intervals[key]
            if key[1] == influenced and key[0] != influencing:
                self._intervals[key] = IntervalTree(intervals)
                continue
            if key[1] == influenced and key[0] == influencing:
                self._intervals[key] = IntervalListDynamic(statement, intervals, paths)
                continue
            self._intervals[key] = IntervalListStatic(intervals)
        adding_time: float = time.time() - adding_time_start

        solve_time_start: float = time.time()
        if self._verbose >= 3:
            plot_statements(self._tmp_intervals, list(self._tmp_intervals.keys()))
        start_amount: int = sum(len(self._tmp_intervals[ivs]) for ivs in self._tmp_intervals)

        instance = IntervalListDynamic.get_instance()
        if instance.solve():
            self._print_result(adding_time, time.time() - solve_time_start, True, start_amount)
        instance.reset()

        # build transitives
        transitive_time_start: float = time.time()
        self._build_transitive_cover(order, statement)
        transitive_time: float = time.time() - transitive_time_start

        result: bool = instance.solve()
        solve_time: float = time.time() - solve_time_start

        self._print_result(adding_time, solve_time, True, start_amount, transitive_time)
        return result

    def _print_result(self, adding_time: float, solve_time: float, result: bool, amount: int,
                      transitive_time: float = None, tube_time: float = None):
        instance = IntervalListDynamic.get_instance()
        if self._verbose >= 1:
            adding: str = f"Adding statements time:      {adding_time}s"
            total: str = f"Total solving time:          {solve_time}s"
            building: str = ""
            if transitive_time is not None:
                building = f"Building transitives:        {transitive_time}s"
            tube: str = ""
            if tube_time is not None:
                tube = f"Solving tube time:           {tube_time}s"
            max_length: int = max(len(total), len(building), len(tube), len(adding))

            print("\n" + "=" * max_length)
            print(adding)
            print(total)
            print(building)
            if tube_time is not None:
                print(tube)
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
        height_build: set[tuple] = set()

        for node in order:
            for pre in self._dependency_graph.get_pre(node):
                key: tuple[str, str] = pre, node
                model: IntervalListStatic = self._intervals[key]

                if key not in height_build:
                    model.strengthen_interval_height()
                    model.strengthen_interval_height_sides()
                    height_build.add(key)

                self._build_transitives(pre, node, goal)
                self._dependency_graph.remove_node(node)

    def _build_transitives(self, a: str, b: str, c: str):
        model_ab: IntervalListStatic = self._intervals[(a, b)]
        model_bc: IntervalTree = self._intervals[(b, c)]
        if (a, c) not in self._intervals:
            self._intervals[(a, c)] = IntervalTree()

        for interval in model_ab.intervals():
            overlapping: list[Interval] = model_bc[interval.begin_other:interval.end_other]
            # TODO: build widths, dont add them / only when more nodes use this?
            overlapping = self.strengthen_interval_width(overlapping, interval.begin_other, interval.end_other)

            for overlapped_interval in overlapping:
                rule: Interval = transitivity(interval, overlapped_interval)
                added: bool = self._intervals[(a, c)].add(rule)
                if added:
                    self._dependency_graph.add(a, c, check=False)

    def strengthen_interval_width(self, sorted_ivs: list[Interval], start: float, end: float) \
            -> list[Interval]:
        return self._strengthen_interval_width_short(sorted_ivs, start) if len(sorted_ivs) < 20 else \
            self._strengthen_interval_width_long(sorted_ivs, start, end)

    def _strengthen_interval_width_short(self, all_intervals: list[Interval], start: float) \
            -> list[Interval]:
        i: int = 0
        offset: int = 1
        while i < len(all_intervals):
            if not all_intervals[i].contains_point(start):
                return all_intervals[:i]
            if not i + offset < len(all_intervals) or all_intervals[i].distance_to(all_intervals[i + offset]) > 0:
                i += 1
                offset = 1
                continue

            result = interval_join(all_intervals[i], all_intervals[i + offset])
            add: bool = better_than_existing(result, all_intervals)
            if add:
                bisect.insort_left(all_intervals, result)
                continue
            offset += 1

        return all_intervals

    def _strengthen_interval_width_long(self, all_intervals: list[Interval], start: float, end: float) \
            -> list[Interval]:
        match_start: deque = deque()
        for iv in all_intervals:
            if iv.contains_point(start):
                match_start.append(iv)
                continue
            break

        while len(match_start) > 0:
            interval: Interval = match_start.popleft()
            index: int = bisect.bisect_left(all_intervals, interval)
            for i in range(len(all_intervals) - index):
                if index + i < len(all_intervals) and interval.distance_to(all_intervals[index + i]) == 0:
                    result = interval_join(interval, all_intervals[index + i])
                    add: bool = better_than_existing(result, all_intervals)

                    if add:
                        bisect.insort_left(all_intervals, result)
                        match_start.append(result)
                    continue
                break
            if not (interval.begin <= start and interval.end >= end):
                all_intervals.remove(interval)

        border: int = len(all_intervals)
        for i in range(len(all_intervals)):
            if not all_intervals[i].contains_point(start):
                border = i
                break
        return all_intervals[:border]

    def __len__(self):
        length: int = 0
        for model in self._intervals:
            length += len(self._intervals[model])
        return length

    def __str__(self):
        return str(self._intervals)


def better_than_existing(interval: Interval, intervals: list[Interval]) -> bool:
    if interval is None:
        return False
    return [iv for iv in intervals if iv.stronger_as(interval)] == []


def _shorten_range(intervals: list[Interval], statement: tuple) -> list[Interval]:
    interval_x: tuple[float, float] = statement[1]
    interval_y: tuple[float, float] = statement[3]

    min_index: int = 0
    for i in range(len(intervals)):
        if intervals[i].contains_point(interval_x[0]):
            min_index = i
            break

    max_index: int = len(intervals) - 1
    for i in range(len(intervals) - 1, -1, -1):
        if intervals[i].contains_point(interval_x[1]):
            max_index = i
            break

    chop_right_index: int = len(intervals) - 1
    y_begin: bool = False
    y_end: bool = False
    if max_index != -1:
        for i in range(max_index, len(intervals) - 1):
            if intervals[i].begin_other >= interval_y[0]:
                y_begin = True
            if intervals[i].end_other <= interval_y[1]:
                y_end = True
            if intervals[i].distance_to(intervals[i + 1]) > 0 or intervals[i].quality == QUALITY_ARB \
                    or (y_begin and y_end):
                chop_right_index = i
                break

    chop_left_index: int = 0
    y_begin: bool = False
    y_end: bool = False
    if min_index != -1:
        for i in range(min_index, 0, -1):
            if intervals[i].begin_other >= interval_y[0]:
                y_begin = True
            if intervals[i].end_other <= interval_y[1]:
                y_end = True
            if intervals[i].distance_to(intervals[i - 1]) > 0 or intervals[i].quality == QUALITY_ARB \
                    or (y_begin and y_end):
                chop_left_index = i
                break

    return intervals[chop_left_index:chop_right_index + 1]
