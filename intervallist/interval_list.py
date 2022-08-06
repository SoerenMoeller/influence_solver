from collections.abc import MutableSet
from typing import Iterator

from sortedcontainers import SortedSet

from solver.constants import QUALITY_CONS
from solver.util import is_stronger_as
from .interval import Interval


class IntervalList(MutableSet):
    _x_set: SortedSet[Interval] = SortedSet(key=lambda iv: (iv.begin, iv.end))
    _y_set: SortedSet[Interval] = SortedSet(key=lambda iv: (iv.begin, iv.end))

    def add(self, statement: Interval, v=0):
        if statement is None:
            return

        area: tuple[int, int] = self.overlap_x_iv(statement)
        enveloping: list[int] = IntervalList.get_enveloping_overlap(self._x_set, area, statement)
        enveloped_by: list[int] = IntervalList.get_enveloped_by_overlap(self._x_set, area, statement)

        adding: bool = True
        # if new statement envelops interval with less width and more height and weaker quality,
        # we can remove the old one
        for i in enveloping:
            iv: Interval = self._x_set[i]
            if is_stronger_as(statement.quality, iv.quality) and \
                    ((statement.begin_other >= iv.begin_other and statement.end_other <= iv.end_other)):
                     #or (height is not None and height[0] <= statement.begin_other and height[
                     #           1] >= statement.end_other)):
                # remove old interval (not needed anymore)
                self.remove(iv)

                if 2 <= v <= 3:
                    print(f"=== removed interval -{iv}- for stronger interval -{statement}- ===")

        for i in enveloped_by:
            iv: Interval = self._x_set[i]
            if is_stronger_as(iv.quality, statement.quality) and \
                    (iv.begin_other >= statement.begin_other and iv.end_other <= statement.end_other):
                     #or (height is not None and height[0] >= intervallist.begin_other and height[
                     #           1] <= intervallist.end_other)):
                if 2 <= v <= 3:
                    print(
                        f"=== did not include intervallist -{statement}- because of stronger intervallist -{intervallist}- ===")
                adding = False

        if not adding:
            return

        # build all intersections, 
        self.add(statement)


    def remove(self, iv: Interval):
        self._x_set.remove(iv)
        self._y_set.remove(iv.turn_interval())

    def discard(self, iv: Interval):
        self._x_set.discard(iv)
        self._y_set.discard(iv.turn_interval())

    def __contains__(self, iv: Interval) -> bool:
        return iv in self._x_set

    def __len__(self) -> int:
        return len(self._x_set)

    def __iter__(self) -> Iterator:
        return self._x_set.__iter__()

    def overlap_x_iv(self, iv: Interval) -> tuple[int, int]:
        return IntervalList._overlap(self._x_set, iv.begin, iv.end)

    def overlap_y_iv(self, iv: Interval) -> tuple[int, int]:
        return IntervalList._overlap(self._y_set, iv.begin, iv.end)

    def overlap_x(self, begin: int, end: int) -> tuple[int, int]:
        return IntervalList._overlap(self._x_set, begin, end)

    def overlap_y(self, begin: int, end: int) -> tuple[int, int]:
        return IntervalList._overlap(self._y_set, begin, end)

    @staticmethod
    def _overlap(ivs: SortedSet, begin: int, end: int):
        index: int = _bisect_point(ivs, begin)
        if index == len(ivs) and index > 0:
            index -= 1

        if not ivs[index].overlaps(begin, end):
            return -1, -1

        upper_border: int = index
        for i in range(index + 1, len(ivs)):
            if not ivs[i].overlaps(begin, end):
                break
            upper_border = i

        lower_border: int = index
        for i in range(index - 1, -1, -1):
            if not ivs[i].overlaps(begin, end):
                break
            lower_border = i

        return lower_border, upper_border + 1

    def envelop_x_iv(self, iv: Interval) -> list[int]:
        return IntervalList._envelop(self._x_set, iv.begin, iv.end)

    def envelop_y_iv(self, iv: Interval) -> list[int]:
        return IntervalList._envelop(self._y_set, iv.begin, iv.end)

    def envelop_x(self, begin: int, end: int) -> list[int]:
        return IntervalList._envelop(self._x_set, begin, end)

    def envelop_y(self, begin: int, end: int) -> list[int]:
        return IntervalList._envelop(self._y_set, begin, end)

    @staticmethod
    def _envelop(ivs: SortedSet, begin: int, end: int) -> list[int]:
        index: int = _bisect_point(ivs, begin)
        if index == len(ivs) and index > 0:
            index -= 1

        indices: list[int] = []
        for i in range(index, len(ivs)):
            if ivs[i].begin > end:
                break
            if ivs[i].enveloped_by(begin, end):
                indices.append(i)

        return indices

    @staticmethod
    def get_enveloped_by_overlap(overlapping, area: tuple[int, int], begin, end: int = None) -> list[int]:
        if end is None:
            return IntervalList.get_enveloped_by_overlap(overlapping, area, begin.begin, begin.end)
        return [i for i in range(area[0], area[1]) if overlapping[i].enveloped_by(begin, end)]

    @staticmethod
    def get_enveloping_overlap(overlapping, area: tuple[int, int], begin, end: int = None) -> list[int]:
        if end is None:
            return IntervalList.get_enveloping_overlap(overlapping, area, begin.begin, begin.end)
        return [i for i in range(area[0], area[1]) if overlapping[i].enveloping(begin, end)]

    def get_intervals(self, begin, end=None):
        if end is None:
            return self.get_intervals(begin[0], begin[1])

        if begin < 0 or end > len(self._x_set):
            raise ValueError
        return self._x_set[begin:end]


def _bisect_point(ivs: SortedSet, point: int) -> int:
    return ivs.bisect_left(Interval(point, point, QUALITY_CONS, 0, 0))
