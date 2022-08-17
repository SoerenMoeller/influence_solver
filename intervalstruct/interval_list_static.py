import intervalstruct.util as util
import solver.rules as rules
from intervalstruct.interval import Interval
from intervalstruct.interval_list_dynamic import IntervalListDynamic
from intervalstruct.overlap_map import OverlapMap


class IntervalListStatic:
    def __init__(self, ivs):
        self._x_set: list[Interval] = []
        self._verbose: int = 1

        self._overlap_map: dict[float, set[Interval]] = {}
        self._boundaries: list[float] = util.init_boundaries(ivs, self._overlap_map)
        self._intervals_created: bool = False

    def __len__(self) -> int:
        return len(self._x_set)

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._x_set):
            raise ValueError
        return self._x_set[begin:end]

    def strengthen_interval_height_sides(self):
        util.strengthen_interval_height_sides(self._x_set)

    def interval_height_and_transitives(self, solver, model: OverlapMap, a: str, c: str):
        instance: IntervalListDynamic = IntervalListDynamic.get_instance()
        lower, upper = instance.statement[1]
        begin, end = util.get_overlap_index(self._boundaries, lower, upper)

        # build overlapping first
        if end > len(self._boundaries):
            end = len(self._boundaries)
        for i in range(begin, end):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.append(iv)

            solver.create_transitive_from_interval(iv, model, a, c)
        util.strengthen_interval_height_sides(self._x_set)

        lower, upper = instance.statement[3]
        for i in range(begin - 1, -1, -1):
            point: float = self._boundaries[i]
            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]

            if instance.left_lower is not None and instance.left_upper is not None \
                    and next_point <= instance.left_lower and next_point <= instance.left_upper:
                break

            iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.insert(0, iv)
            self.strengthen_interval_height_sides_first()

            interval: iv = solver.create_transitive_from_interval(iv, model, a, c)
            if interval is None:
                continue

            if (instance.left_lower is None or instance.left_lower < next_point) and interval.begin_other >= lower:
                instance.left_lower = next_point
            if (instance.left_upper is None or instance.left_upper < next_point) and interval.end_other <= upper:
                instance.left_upper = next_point

        for i in range(end, len(self._boundaries) - 1):
            point: float = self._boundaries[i]

            if instance.right_lower is not None and instance.right_upper is not None \
                    and point >= instance.right_lower and point >= instance.right_upper:
                break

            if not self._overlap_map[point]:
                continue

            next_point: float = self._boundaries[i + 1]
            iv: Interval = rules.interval_strength_multiple(point, next_point, self._overlap_map[point])
            self._x_set.append(iv)
            self.strengthen_interval_height_sides_last()

            interval: iv = solver.create_transitive_from_interval(iv, model, a, c)
            if interval is None:
                continue

            if (instance.right_lower is None or instance.right_lower > point) and interval.begin_other >= lower:
                instance.right_lower = point
            if (instance.right_upper is None or instance.right_upper > point) and interval.end_other <= upper:
                instance.right_upper = point

    def strengthen_interval_height_sides_last(self):
        i = len(self._x_set) - 2 if len(self._x_set) > 2 else 0

        while i < len(self._x_set):
            changed: bool = False
            if i < len(self._x_set) - 1:
                iv: Interval = rules.interval_strength_right(self._x_set[i], self._x_set[i + 1])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if i > 0:
                iv: Interval = rules.interval_strength_left(self._x_set[i - 1], self._x_set[i])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if changed:
                i -= 1
                continue
            i += 1

    def strengthen_interval_height_sides_first(self):
        i = 1 if len(self._x_set) > 0 else 0

        while i >= 0:
            changed: bool = False
            if i < len(self._x_set) - 1:
                iv: Interval = rules.interval_strength_right(self._x_set[i], self._x_set[i + 1])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if i > 0:
                iv: Interval = rules.interval_strength_left(self._x_set[i - 1], self._x_set[i])
                if iv is not None:
                    self._x_set[i] = iv
                    changed = True
            if changed:
                i += 1
                continue
            i -= 1

    def intervals_created(self) -> bool:
        return self._intervals_created

    def intervals(self) -> list[Interval]:
        return self._x_set

    def intervals_turned(self) -> list[Interval]:
        return sorted({iv.turn_interval() for iv in self._x_set})
