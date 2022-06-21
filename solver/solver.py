import bisect
import time

from intervaltree_custom.intervaltree import IntervalTree
from plotter.plotter import plot_statements, show_plot
from .dependency_graph import add_to_graph, setup_graph, get_dependency_graph
from .rules import *
from .util import add_to_tree

# TODO: Reflexive rule, Add reflexive statements?, Consistency?

class Solver:
    _intervals: dict[tuple] = {}
    _verbose: int = 1
    _dependency_graph: dict[str, set[str]] = {}

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

        add_to_graph(interval)

        quality: str = interval[2]
        interval_x: tuple[float, float] = interval[1]
        interval_y: tuple[float, float] = interval[3]

        selector: tuple[str, str] = (influencing, influenced)
        if selector not in self._intervals:
            tree_x: IntervalTree = IntervalTree()
            tree_y: IntervalTree = IntervalTree()
            self._intervals[selector] = (tree_x, tree_y)

        model: tuple = self._intervals[selector]
        interval: Interval = Interval(interval_x[0], interval_x[1], quality, interval_y[0], interval_y[1])
        add_to_tree(model, interval, self._verbose)

    def _add_multiple_intervals(self, intervals: list[tuple]):
        for interval in intervals:
            self._add_single_interval(interval)

    def solve(self, statement: tuple) -> bool:
        solve_time_start: float = time.time()
        influencing: str = statement[0]
        influenced: str = statement[4]
        quality: str = statement[2]
        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]
        if self._verbose >= 3:
            plot_statements(self._intervals, list(self._intervals.keys()), statement)
        start_amount: int = self._length()

        # build transitive dependencies
        graph_time_start: float = time.time()
        order: list = setup_graph(influencing, influenced)
        graph_time: float = time.time() - graph_time_start

        if not (influencing, influenced) in self._intervals:
            self._intervals[(influencing, influenced)] = (IntervalTree(), IntervalTree())
        model: tuple = self._intervals[(influencing, influenced)]

        # build transitives
        transitive_time_start: float = time.time()
        self._build_transitive_cover(order)
        transitive_time: float = time.time() - transitive_time_start

        # get all overlapping
        overlaps_x: set[Interval] = model[0][interval_x[0]:interval_x[1]]
        overlaps_y: set[Interval] = {elem.turn_interval() for elem in model[1][interval_y[0]:interval_y[1]]}

        # not solvable if the condition is not met
        if not overlaps_x.issubset(overlaps_y):
            self._print_result(time.time() - solve_time_start, graph_time, transitive_time, False, statement,
                               start_amount)
            return False

        # check if there is a gap
        if _check_for_gap(sorted(overlaps_x))[0]:
            if 2 <= self._verbose <= 3:
                print("== gap found in the searching area ==")

            self._print_result(time.time() - solve_time_start, graph_time, transitive_time, quality == QUALITY_ARB,
                               statement, start_amount)
            return quality == QUALITY_ARB

        # check if solvable from one of the statements in the model
        if rule_fact(statement, overlaps_x):
            self._print_result(time.time() - solve_time_start, graph_time, transitive_time, True, statement,
                               start_amount)
            return True

        # propagate stronger intervals from left to right
        sorted_tube: list[Interval] = sorted(overlaps_y)
        all_indices: set[int] = {sorted_tube.index(elem) for elem in overlaps_x}
        max_index = max(all_indices) if len(all_indices) > 0 else -1
        min_index = min(all_indices) if len(all_indices) > 0 else -1

        if max_index != -1:
            result, new_tube = _check_for_gap(sorted_tube, chop=True, index=max_index, threshold=interval_y)

            if result:
                if 2 <= self._verbose <= 3:
                    print(f"== found gap or unnecessary precise interval and chopped right end off ==")
                    print(f"== Old: {sorted_tube} ==")
                    print(f"== New: {new_tube} ==")

                sorted_tube = new_tube

        if min_index != -1:
            result, new_tube = _check_for_gap_reversed(sorted_tube, chop=True, index=min_index, threshold=interval_y)

            if result:
                if 2 <= self._verbose <= 3:
                    print(f"== found gap or unnecessary precise interval and chopped left end off ==")
                    print(f"== Old: {sorted_tube} ==")
                    print(f"== New: {new_tube} ==")

                max_index -= (len(sorted_tube) - len(new_tube))
                sorted_tube = new_tube

        # propagate (here, left and right is only needed once)
        tube_time_start: float = time.time()
        sorted_tube = self._strengthen_interval_height(sorted_tube, model)
        self._strengthen_interval_height_side(sorted_tube, model)
        self._strengthen_interval_height_side(sorted_tube, model, right=True)

        # build the widest intervals in the affected area
        sorted_area: list[Interval] = sorted(model[0][interval_x[0]:interval_x[1]])
        sorted_area = self._strengthen_interval_width(sorted_area, model, threshold=interval_x[0], x=True)
        tube_time: float = time.time() - tube_time_start

        result: bool = rule_fact(statement, set(sorted_area))
        solve_time: float = time.time() - solve_time_start

        self._print_result(solve_time, graph_time, transitive_time, result, statement, start_amount,
                           tube_time=tube_time)

        return result

    def _print_result(self, solve_time: float, graph_time: float, transitive_time: float, result: bool,
                      statement: tuple, amount: int, tube_time: float = None):
        if self._verbose >= 1:
            total: str = f"Total solving time:          {solve_time}s"
            dependency: str = f"Dependency graph setup:      {graph_time}s"
            building: str = f"Building transitives:        {transitive_time}s"
            tube: str = ""
            if tube_time is not None:
                tube = f"Solving tube time:           {tube_time}s"
            max_length: int = max(len(total), len(dependency), len(building), len(tube))

            print("\n" + "=" * max_length)
            print(total)
            print(dependency)
            print(building)
            if tube_time is not None:
                print(tube)
            print("=" * max_length + "\n")

            print(f"Started with {amount} amount of statements in the model")
            print(f"Finished with {self._length()} amount of statements in the model\n")

            print(f"Statement: -{statement}-", end=" ")
            print("can be solved" if result else "is not solvable")

        if self._verbose >= 3:
            if self._verbose == 5:
                # remove unnecessary intervals from view
                influencing: str = statement[0]
                influenced: str = statement[4]
                interval_x: tuple[float, float] = statement[1]

                model = self._intervals[(influencing, influenced)]
                ivs = model[0][interval_x[0]:interval_x[1]]
                ivs = [iv for iv in ivs if iv.begin <= interval_x[0] and iv.end >= interval_x[1]]

                new_model = (IntervalTree(), IntervalTree())
                self._intervals[(influencing, influenced)] = new_model
                for iv in ivs:
                    add_to_tree(new_model, iv)

            plot_statements(self._intervals, list(self._intervals.keys()), statement)
            show_plot()

    def _build_transitive_cover(self, order: list[str]):
        graph: dict = get_dependency_graph()

        for i in order:
            for j in order:
                for k in order:
                    if not (i in graph and j in graph[i]) or not (j in graph and k in graph[j]):
                        continue

                    model: tuple = self._intervals[(i, j)]
                    sorted_ivs: list[Interval] = sorted(model[0].all_intervals)
                    sorted_ivs = self._strengthen_interval_height(sorted_ivs, model)
                    self._strengthen_interval_height_sides(sorted_ivs, model)
                    self._strengthen_interval_height_side(sorted_ivs, model)
                    self._strengthen_interval_height_side(sorted_ivs, model, right=True)
                    self._build_transitives(i, j, k)

    def _build_transitives(self, a: str, b: str, c: str):
        model_ab: tuple = self._intervals[(a, b)]
        model_bc: tuple = self._intervals[(b, c)]
        if (a, c) not in self._intervals:
            self._intervals[(a, c)] = (IntervalTree(), IntervalTree())

        for interval in model_ab[1]:
            overlapping: list[Interval] = sorted(model_bc[0][interval.begin:interval.end])
            overlapping = self._strengthen_interval_width(overlapping, model_bc, threshold=interval.begin)
            overlapping = [iv for iv in overlapping if iv.begin <= interval.begin and iv.end >= interval.end]

            for overlapped_interval in overlapping:
                rule: Interval = transitivity(interval.turn_interval(), overlapped_interval)
                add_to_tree(self._intervals[(a, c)], rule, self._verbose)

    def _strengthen_interval_height(self, sorted_ivs: list[Interval], model: tuple) -> list[Interval]:
        all_intervals: list[Interval] = sorted_ivs

        i: int = 0
        offset: int = 1
        while i < len(all_intervals):
            if not i + offset < len(all_intervals):
                i += 1
                offset = 1
                continue

            result = interval_strength(all_intervals[i], all_intervals[i + offset])
            added: tuple[bool, Union[Interval, None]] = add_to_tree(model, result, self._verbose)
            if added[0]:
                index: int = bisect.bisect_left(all_intervals, result)
                all_intervals = all_intervals[:index] + [result] + all_intervals[index:]
                continue
            if all_intervals[i].distance_to(all_intervals[i + offset]) > 0:
                i += 1
                offset = 1
            else:
                offset += 1

        return all_intervals

    def _strengthen_interval_height_sides(self, sorted_ivs: list[Interval], model: tuple):
        copy = []
        while sorted_ivs != copy:
            copy = sorted_ivs.copy()
            self._strengthen_interval_height_side(sorted_ivs, model)
            self._strengthen_interval_height_side(sorted_ivs, model, right=True)

    def _strengthen_interval_height_side(self, sorted_ivs: list[Interval], model: tuple, right: bool = False):
        all_intervals: list[Interval] = sorted_ivs
        if right:
            all_intervals = sorted(sorted_ivs, key=lambda x: x.end, reverse=True)

        i: int = 0
        offset: int = 1
        while i < len(all_intervals):
            if not i + offset < len(all_intervals):
                i += 1
                offset = 1
                continue

            if right:
                result = interval_strength_right(all_intervals[i + offset], all_intervals[i])
            else:
                result = interval_strength_left(all_intervals[i], all_intervals[i + offset])
            added: tuple[bool, Union[Interval, None]] = add_to_tree(model, result, self._verbose)
            if added[0]:
                all_intervals[i + offset] = result
            if all_intervals[i].distance_to(all_intervals[i + offset]) == 0:
                offset += 1
            else:
                i += 1
                offset = 1

    def _strengthen_interval_width(self, sorted_ivs: list[Interval], model: tuple, threshold: float = None, x=False) \
            -> list[Interval]:
        all_intervals: list[Interval] = sorted_ivs

        i: int = 0
        offset: int = 1
        while i < len(all_intervals):
            if threshold is not None and all_intervals[i].begin > threshold:
                return all_intervals
            if not i + offset < len(all_intervals):
                i += 1
                offset = 1
                continue

            result = interval_join(all_intervals[i], all_intervals[i + offset])
            added: tuple[bool, Union[Interval, None]] = add_to_tree(model, result, self._verbose)
            if added[0]:
                index: int = bisect.bisect_left(all_intervals, result)
                all_intervals = all_intervals[:index] + [result] + all_intervals[index:]
                offset = 1
                continue
            if all_intervals[i].distance_to(all_intervals[i + offset]) > 0:
                i += 1
                offset = 1
            else:
                offset += 1

        return all_intervals

    def _length(self):
        length: int = 0
        for model in self._intervals:
            length += len(self._intervals[model][0].all_intervals)
        return length

    def __str__(self):
        return str(self._intervals)


# TODO: Cancel when arbitrary is in the way?
def _check_for_gap_reversed(intervals: list[Interval], index: int = 0, chop: bool = False, threshold: tuple = None) \
        -> tuple[bool, list[Interval]]:
    cond_x: bool = False
    cond_y: bool = False

    for i in range(index, -1, -1):
        if threshold is not None:
            if intervals[i].begin_other >= threshold[0]:
                cond_x = True
            if intervals[i].end_other <= threshold[1]:
                cond_y = True

        if intervals[i].distance_to(intervals[i + 1]) > 0 or (cond_x and cond_y):
            if chop:
                intervals = intervals[i + 1:]
            return True, intervals

    return False, []


def _check_for_gap(intervals: list[Interval], index: int = 0, chop: bool = False, threshold: tuple = None) \
        -> tuple[bool, list[Interval]]:
    cond_x: bool = False
    cond_y: bool = False

    for i in range(index, len(intervals) - 1):
        if threshold is not None:
            if intervals[i].begin_other >= threshold[0]:
                cond_x = True
            if intervals[i].end_other <= threshold[1]:
                cond_y = True

        if intervals[i].distance_to(intervals[i + 1]) > 0 or (cond_x and cond_y):
            if chop:
                intervals = intervals[:i + 1]
            return True, intervals

    return False, []
