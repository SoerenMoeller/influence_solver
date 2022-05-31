from intervaltree import IntervalTree, Interval

from dependency_graph import build_graph
from rules import interval_strength_left, interval_strength_right, interval_join
from util import is_stronger_as, turn_interval, add_to_tree


class Solver:
    _intervals: dict[tuple] = {}
    _verbose: bool = True

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
        quality: str = interval[2]
        interval_x: tuple[float, float] = interval[1]
        interval_y: tuple[float, float] = interval[3]

        selector: tuple[str, str] = (influencing, influenced)
        if selector not in self._intervals:
            tree_x: IntervalTree = IntervalTree()
            tree_y: IntervalTree = IntervalTree()
            self._intervals[selector] = (tree_x, tree_y)

        model: tuple = self._intervals[selector]
        interval: Interval = Interval(interval_x[0], interval_x[1], (quality, interval_y))
        add_to_tree(model, interval, self._verbose)

    def _add_multiple_intervals(self, intervals: list[tuple]):
        for interval in intervals:
            self._add_single_interval(interval)

    def solve(self, statement: tuple) -> bool:
        influencing: str = statement[0]
        influenced: str = statement[4]
        build_graph(set(self._intervals.keys()), (influencing, influenced))

        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]

        if not (influencing, influenced) in self._intervals:
            self._intervals[(influencing, influenced)] = (IntervalTree(), IntervalTree())
        model: tuple = self._intervals[(influencing, influenced)]

        # TODO: build transitives
        # TODO: do we need ALL sub intervals?

        # get all overlapping on x
        overlaps_x: set[Interval] = model[0][interval_x[0]:interval_x[1]]
        overlaps_y: set[Interval] = {turn_interval(elem) for elem in model[1][interval_y[0]:interval_y[1]]}

        # not solvable if the condition is not met
        if not overlaps_x.issubset(overlaps_y):
            return False

        # check if solvable from one of the statements in the model
        if self.rule_fact(statement):
            print("solved instantly")
            #return True

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
        overlaps_y: set[Interval] = {turn_interval(elem) for elem in model[1][interval_y[0]:interval_y[1]]}
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

        return self.rule_fact(statement)

    def rule_fact(self, statement) -> bool:
        influencing: str = statement[0]
        influenced: str = statement[4]
        quality: str = statement[2]
        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]

        model: tuple = self._intervals[(influencing, influenced)]
        sub_y: set[Interval] = model[1].envelop(interval_y[0], interval_y[1])

        for sub_interval in sub_y:
            data: tuple = sub_interval.data
            quality_sub: str = data[0]
            x_start: float = data[1][0]
            x_end: float = data[1][1]

            if x_start >= interval_x[0] and x_end <= interval_x[1] and is_stronger_as(quality_sub, quality):
                return True
            # else TODO: strengthen the qualities (enough once in the end?)
        return False

    def __str__(self):
        return str(self._intervals)
