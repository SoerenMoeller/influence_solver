import bisect
import time
from collections import deque

from intervallist.interval_list import IntervalList
from plotter.plotter import plot_statements, show_plot
from .dependency_graph import DependencyGraph
from .rules import *

# TODO: Reflexive rule, Add reflexive statements?, Consistency?
# TODO: Höhe null -> Konstant / ARB rausschmeißen

class Solver:
    _intervals: dict[tuple] = {}
    _verbose: int = 4
    _dependency_graph: DependencyGraph = DependencyGraph()
    _tmp_intervals: dict[tuple, set] = {}

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
        self._dependency_graph.add(interval)

        quality: str = interval[2]
        interval_x: tuple[float, float] = interval[1]
        interval_y: tuple[float, float] = interval[3]

        selector: tuple[str, str] = (influencing, influenced)
        if selector not in self._intervals:
            self._intervals[selector] = IntervalList()
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
        interval_x: tuple[float, float] = statement[1]
        interval_y: tuple[float, float] = statement[3]
        order: list = self._dependency_graph.setup(influencing, influenced)

        used_variables: list[str] = order + [influencing, influenced]
        keys: set[tuple] = {key for key in self._tmp_intervals if key[0] in used_variables and key[1] in used_variables}
        for key in self._tmp_intervals:
            model = self._intervals[key]
            for iv in self._tmp_intervals[key]:
                model.add(iv)
        adding_time: float = time.time() - adding_time_start

        solve_time_start: float = time.time()
        if self._verbose >= 3:
            plot_statements(self._intervals, list(self._intervals.keys()), statement)
        start_amount: int = self._length()

        if not (influencing, influenced) in self._intervals:
            self._intervals[(influencing, influenced)] = IntervalList()
        model: IntervalList = self._intervals[(influencing, influenced)]

        # build transitives
        transitive_time_start: float = time.time()
        self._build_transitive_cover(order, statement)
        transitive_time: float = time.time() - transitive_time_start

        # get all overlapping
        overlaps_x: list[Interval] = model.overlap_x(interval_x[0], interval_x[1])
        overlaps_y: set[Interval] = {elem.turn_interval() for elem in model.overlap_y(interval_y[0], interval_y[1])}
        # not solvable if the condition is not met
        #if not overlaps_x.issubset(overlaps_y):
        #    self._print_result(adding_time, time.time() - solve_time_start, transitive_time, False, statement,
        #                       start_amount)
        #    return False

        # check if there is a gap
        if _check_for_gap(overlaps_x):
            if 2 <= self._verbose <= 3:
                print("== gap found in the searching area ==")

            self._print_result(adding_time, time.time() - solve_time_start, transitive_time, quality == QUALITY_ARB,
                               statement, start_amount)

            return quality == QUALITY_ARB

        # check if solvable from one of the statements in the model
        if rule_fact(statement, overlaps_x):
            self._print_result(adding_time, time.time() - solve_time_start, transitive_time, True, statement, start_amount)
            return True

        # check which area has to be checked for propagation
        sorted_tube: list[Interval] = sorted(overlaps_y)
        sorted_tube = _shorten_range(sorted_tube, statement)

        # propagate (here, left and right is only needed once)
        tube_time_start: float = time.time()
        model.strengthen_interval_height_sides()
        #model.strengthen_interval_height_sides(sorted_tube)
        #model.strengthen_interval_height_side_right(sorted_tube)

        # build the widest intervals in the affected area
        sorted_area: list[Interval] = model.overlap_x(interval_x[0], interval_x[1])
        sorted_area = self._strengthen_interval_width(sorted_area, interval_x[0], interval_x[1])
        tube_time: float = time.time() - tube_time_start

        result: bool = rule_fact(statement, sorted_area)
        solve_time: float = time.time() - solve_time_start

        self._print_result(adding_time, solve_time, transitive_time, result, statement, start_amount, tube_time=tube_time)

        return result

    def _print_result(self, adding_time: float, solve_time: float, transitive_time: float, result: bool,
                      statement: tuple, amount: int, tube_time: float = None):
        if self._verbose >= 1:
            adding: str = f"Adding statements time:      {adding_time}s"
            total: str = f"Total solving time:          {solve_time}s"
            building: str = f"Building transitives:        {transitive_time}s"
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

                new_model = IntervalList()
                self._intervals[(influencing, influenced)] = IntervalList()
                for iv in ivs:
                    new_model.add(iv)

            plot_statements(self._intervals, list(self._intervals.keys()), statement)
            show_plot()

    def _build_transitive_cover(self, order: list[str], statement: tuple):
        goal: str = statement[4]

        for node in order:
            for pre in self._dependency_graph.get_pre(node):
                model: IntervalList = self._intervals[(pre, node)]
                model.strengthen_interval_height_sides()
                self._build_transitives(pre, node, goal, statement)

                self._dependency_graph.remove_node(node)

    def _build_transitives(self, a: str, b: str, c: str, statement: tuple):
        height: tuple[float, float] = statement[3]

        model_ab: IntervalList = self._intervals[(a, b)]
        model_bc: IntervalList = self._intervals[(b, c)]
        if (a, c) not in self._intervals:
            self._intervals[(a, c)] = IntervalList

        # filter needed height
        height_tree: IntervalList = IntervalList([iv for iv in model_bc.all_intervals()
                                                  if iv.begin_other >= height[0] and iv.end_other <= height[1]])

        # check which ranges on x match the needed height
        sorted_ivs: list[Interval] = height_tree.all_intervals()
        x_union: list[list[float]] = [[sorted_ivs[0].begin, sorted_ivs[0].end]] if len(sorted_ivs) > 0 else []
        for i in range(1, len(sorted_ivs)):
            if sorted_ivs[i].begin <= x_union[-1][1]:
                x_union[-1][1] = sorted_ivs[i].end
                continue
            x_union.append([sorted_ivs[i].begin, sorted_ivs[i].end])


        intervals: set[Interval] = set()
        for x_range in x_union:
            intervals.update(model_ab.envelop_y(x_range[0], x_range[1]))

        for interval in intervals:
            overlapping: list[Interval] = height_tree.overlap_x(interval.begin, interval.end)
            overlapping = self._strengthen_interval_width(overlapping, interval.begin, interval.end)
            for overlapped_interval in overlapping:
                rule: Interval = transitivity(interval.turn_interval(), overlapped_interval)
                added: bool = self._intervals[(a, c)].add(rule, height=height)
                if added:
                    self._dependency_graph.add(rule)

    def _strengthen_interval_width(self, sorted_ivs: list[Interval], start: float, end: float) \
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
            if result is not None and len([iv for iv in all_intervals if iv.stronger_as(result)]) == 0:                              # NOT IN MODEL!, check if result is good?
                all_intervals -= [iv for iv in all_intervals if result.stronger_as(iv)]
                bisect.insort_left(all_intervals, result)       # TODO: give index?

                continue
            offset += 1

        return all_intervals

    def _strengthen_interval_width_long(self, sorted_ivs: list[Interval], start: float, end: float) \
            -> list[Interval]:
        all_intervals: list[Interval] = sorted_ivs

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

                    if result is not None and len([iv for iv in all_intervals if iv.stronger_as(result)]) == 0:      # TODO: check if good
                        all_intervals -= [iv for iv in all_intervals if result.stronger_as(iv)]
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

    def _length(self):
        length: int = 0
        for model in self._intervals:
            length += len(self._intervals[model].all_intervals())
        return length

    def __str__(self):
        return str(self._intervals)


def _check_for_gap(intervals: list[Interval]) -> bool:
    for i in range(len(intervals) - 1):
        if intervals[i].distance_to(intervals[i + 1]) > 0:
            return True
    return False


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
