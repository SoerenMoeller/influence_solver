from intervaltree_custom.intervaltree import IntervalTree
from intervaltree_custom.interval import Interval

from .dependency_graph import add_to_graph, setup_graph, get_dependency_graph
from .rules import interval_strength_left, interval_strength_right, interval_join, interval_strength
from .util import is_stronger_as, add_to_tree

import time


class Solver:
    _intervals: dict[tuple] = {}
    _verbose: int = 2
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
        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]

        # build transitive dependencies
        graph_time_start: float = time.time()
        order: list = setup_graph(influencing, influenced)
        graph_time: float = time.time() - graph_time_start

        if not (influencing, influenced) in self._intervals:
            self._intervals[(influencing, influenced)] = (IntervalTree(), IntervalTree())
        model: tuple = self._intervals[(influencing, influenced)]

        transitive_time_start: float = time.time()
        self._build_transitive_cover(order)
        # TODO: build transitives
        # TODO: do we need ALL sub intervals?
        transitive_time: float = time.time() - transitive_time_start

        # get all overlapping on x
        overlaps_x: set[Interval] = model[0][interval_x[0]:interval_x[1]]
        overlaps_y: set[Interval] = {elem.turn_interval() for elem in model[1][interval_y[0]:interval_y[1]]}

        # not solvable if the condition is not met
        if not overlaps_x.issubset(overlaps_y):
            return False

        # check if solvable from one of the statements in the model
        if self._rule_fact(statement):
            print("solved instantly")
            # return True

        # propagate now to create the strongest possible intervals (interval and quality wise)
        # TODO: is this needed? - no
        # build all overlapping intervals in the tube first
        """
        tube_tree_y: IntervalTree = IntervalTree(overlaps_y)
        for interval in tube_tree_y:
            overlapping: set = tube_tree_y[interval.begin:interval.end]
            for interval_b in overlapping:
                rule: Interval = interval_strength(interval, interval_b)

                if rule is not None:
                    overlaps_y.add(rule)
                    model[0].add(rule)
                    model[1].add(norm_interval(rule))
        """
        # propagate stronger intervals from left to right
        sorted_tube: list[Interval] = sorted(overlaps_y)
        all_indices: set[int] = {sorted_tube.index(elem) for elem in overlaps_x}
        max_index = max(all_indices) if len(all_indices) > 0 else -1
        for i in range(max_index):
            rule: Interval = interval_strength_left(sorted_tube[i], sorted_tube[i + 1])

            if rule is not None:
                # use the stronger height to propagate further
                sorted_tube[i + 1] = rule

                add_to_tree(model, rule, self._verbose)

        # propagate stronger intervals from right to left
        overlaps_x: set[Interval] = model[0][interval_x[0]:interval_x[1]]
        overlaps_y: set[Interval] = {elem.turn_interval() for elem in model[1][interval_y[0]:interval_y[1]]}
        sorted_tube: list[Interval] = sorted(sorted(overlaps_y), key=lambda x: x.end)[::-1]
        all_indices: set[int] = {sorted_tube.index(elem) for elem in overlaps_x}
        max_index = max(all_indices) if len(all_indices) > 0 else -1
        for i in range(max_index):
            rule: Interval = interval_strength_right(sorted_tube[i + 1], sorted_tube[i])

            if rule is not None:
                # use the stronger height to propagate further
                sorted_tube[i + 1] = rule
                add_to_tree(model, rule, self._verbose)

        # TODO: build joins for all intervals in range of the needed interval
        # TODO: Which ones are important in the first place
        overlaps_x: list[Interval] = sorted(model[0][interval_x[0]:interval_x[1]])
        i: int = 0
        offset: int = 1
        while i < len(overlaps_x) - 1:
            rule: Interval = interval_join(overlaps_x[i], overlaps_x[i + offset])

            if rule is not None and rule not in overlaps_x:
                overlaps_x.append(rule)
                overlaps_x.sort()
                if i + offset < len(overlaps_x) - 1:
                    offset += 1
                else:
                    offset = 1
                    i += 1
            else:
                offset = 1
                i += 1

        result: bool = self._rule_fact(statement)
        solve_time: float = time.time() - solve_time_start

        self._print_result(solve_time, graph_time, transitive_time, result)

        return result

    def _print_result(self, solve_time: float, graph_time: float, transitive_time: float, result: bool):
        if self._verbose >= 1:
            total: str = f"Total solving time:          {solve_time}s"
            dependency: str = f"Dependency graph setup:      {graph_time}s"
            building: str = f"Building transitives:        {transitive_time}s"
            max_length: int = max(len(total), len(dependency), len(building))

            print("\n" + "=" * max_length)
            print(total)
            print(dependency)
            print(building)
            print("=" * max_length + "\n")

            print("solved" if result else "not solvable")

    def _build_transitive_cover(self, order: list[str]):
        graph: dict = get_dependency_graph()

        for i in order:
            for j in order:
                for k in order:
                    if not (i in graph and j in graph[i]) or not (j in graph and k in graph[j]):
                        continue

                    self._strengthen_interval_height(i, j, interval_strength)
                    self._strengthen_interval_height(i, j, interval_strength_left)
                    self._strengthen_interval_height(i, j, interval_strength_right)
                    self._strengthen_interval_width(j, k)
                    self._build_transitives(i, j, k)
                    return

    def _build_transitives(self, a: str, b: str, c: str):
        pass

    def _strengthen_interval_height(self, influencing: str, influenced: str, strengthening_method, rev: bool = False):
        # iterate over given statements of influences with the goal of strengthening the qualities
        model: tuple = self._intervals[(influencing, influenced)]
        all_intervals: list[Interval]
        if rev:
            all_intervals = sorted(sorted(model[0].all_intervals), key=lambda x: x.end, reverse=True)
        else:
            all_intervals = sorted(model[0].all_intervals)

        i: int = 0
        offset: int = 1
        while i < len(all_intervals):
            if not i + offset < len(all_intervals):
                i += 1
                offset = 1
                continue

            first: int = i + offset if rev else i
            second: int = i if rev else i + offset
            result = strengthening_method(all_intervals[first], all_intervals[second])
            added: bool = add_to_tree(model, result)
            if added:
                offset += 1
            else:
                i += 1
                offset = 1

    def _strengthen_interval_width(self, influencing: str, influenced: str):
        # iterate over given statements of influences with the goal of maximizing the width
        pass

    def _rule_fact(self, statement) -> bool:
        influencing: str = statement[0]
        influenced: str = statement[4]
        quality: str = statement[2]
        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]

        model: tuple = self._intervals[(influencing, influenced)]
        sub_y: set[Interval] = model[1].envelop(interval_y[0], interval_y[1])

        for sub_interval in sub_y:
            quality_sub: str = sub_interval.quality
            x_start: float = sub_interval.begin
            x_end: float = sub_interval.begin_other

            if x_start >= interval_x[0] and x_end <= interval_x[1] and is_stronger_as(quality_sub, quality):
                return True
        return False

    def __str__(self):
        return str(self._intervals)
