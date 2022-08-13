from intervalstruct.interval import Interval
import intervalstruct.interval_list_dynamic as FinalList
from solver.rules import interval_strength_left, interval_strength_right, interval_strength_multiple


class IntervalListStatic:
    def __init__(self, ivs=None):
        self._x_set: list[Interval] = sorted(ivs) if ivs is not None else []
        self._intersect: list[Interval] = []
        self._verbose: int = 1

        self._overlap_map: dict[float, set[Interval]] = {}
        tmp_boundaries: set[float] = set()
        for iv in self._x_set:
            if iv.begin not in self._overlap_map:
                self._overlap_map[iv.begin] = set()
                tmp_boundaries.add(iv.begin)
            if iv.end not in self._overlap_map:
                self._overlap_map[iv.end] = set()
                tmp_boundaries.add(iv.end)
            self._overlap_map[iv.begin].add(iv)
            self._overlap_map[iv.end].add(iv)

        # TODO: cleanup
        self._boundaries: list[float] = sorted(tmp_boundaries)
        to_add: set[Interval] = set()
        for var in self._boundaries:
            to_rem = set()
            for iv in to_add:
                if iv in self._overlap_map[var]:
                    self._overlap_map[var].remove(iv)
                    to_rem.add(iv)
            to_add.difference_update(to_rem)
            self._overlap_map[var].update(to_add)
            to_add.update(self._overlap_map[var])

    # TODO: Edge case only one iv?
    def strengthen_interval_height(self):
        # do we know any borders yet?
        # else: can we find some or strengthen the old ones

        self._x_set = []
        for i in range(len(self._boundaries) - 1):
            start: float = self._boundaries[i]
            if not self._overlap_map[start]:
                continue

            end: float = self._boundaries[i + 1]
            iv: Interval = interval_strength_multiple(start, end, self._overlap_map[start])
            self._x_set.append(iv)

    def __len__(self) -> int:
        return len(self._x_set)

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._x_set):
            raise ValueError
        return self._x_set[begin:end]

    def strengthen_interval_height_sides(self):
        changed = True
        i = 0
        while changed:
            i += 1
            if i > 1:
                print("MORE THAN ONE ROUND")
            changed = False
            for i in range(len(self._x_set) - 1):
                result = interval_strength_left(self._x_set[i], self._x_set[i + 1])
                if result is not None:
                    self._x_set[i + 1] = result
                    changed = True
            for i in range(len(self._x_set) - 2, -1, -1):
                result = interval_strength_right(self._x_set[i - 1], self._x_set[i])
                if result is not None:
                    self._x_set[i - 1] = result
                    changed = True

    def intervals(self):
        return self._x_set

    def intervals_turned(self):
        return sorted({iv.turn_interval() for iv in self._x_set})
