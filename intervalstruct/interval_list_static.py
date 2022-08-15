import intervalstruct.util as util
from intervalstruct.interval import Interval


class IntervalListStatic:
    def __init__(self, ivs=None):
        self._x_set: list[Interval] = []
        self._verbose: int = 1

        self._overlap_map: dict[float, set[Interval]] = {}
        self._boundaries: list[float] = util.init_boundaries_for_intersect(ivs, self._overlap_map)

    # TODO: Edge case only one iv?
    def strengthen_interval_height(self):
        util.strengthen_interval_height(self._boundaries, self._overlap_map, self._x_set)

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

    def intervals(self):
        return self._x_set

    def intervals_turned(self):
        return sorted({iv.turn_interval() for iv in self._x_set})
