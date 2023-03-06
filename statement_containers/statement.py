from collections import namedtuple

from solver.util import is_stronger_as


class Statement(namedtuple('IntervalBase', ['begin', 'end', 'quality', 'begin_y', 'end_y'])):
    """
    Internal representation of statements

    namedtuple
    ----------
    begin (float):
        start value of range interval
    end (float):
        end value of range interval
    quality (str):
        quality of the statement
    begin_y (float):
        start value of domain interval
    end_y (float):
        end value of domain interval
    """
    __slots__ = ()

    def __new__(cls, begin, end, quality, begin_y, end_y):
        return super(Statement, cls).__new__(cls, begin, end, quality, begin_y, end_y)

    def stronger_as(self, iv, height=None):
        return is_stronger_as(self.quality, iv.quality) and self.begin <= iv.begin and self.end >= iv.end and \
               ((self.begin_y >= iv.begin_y and self.end_y <= iv.end_y) or
                (height is not None and height[0] <= self.begin_y and height[1] >= self.end_y))

    def enveloped_by(self, begin, end=None):
        if end is None:
            return self.enveloped_by(begin.begin, begin.end)
        return begin <= self.begin and end >= self.end

    def enveloping(self, begin, end=None):
        if end is None:
            return self.enveloping(begin.begin, begin.end)
        return begin >= self.begin and end <= self.end

    def exceeds_height(self, begin, end):
        return self.begin_y < begin or self.end_y > end

    def overlaps(self, begin, end=None):
        if end is None:
            return self.overlaps(begin.begin, begin.end)
        return begin <= self.end and end >= self.begin

    def overlaps_y(self, begin, end=None):
        if end is None:
            return self.overlaps_y(begin.begin, begin.end)
        return begin <= self.end_y and end >= self.begin_y

    def distance_to(self, other):
        if self.overlaps(other):
            return 0

        return other.begin - self.end if self.begin < other.begin else self.begin - other.end

    def contains_point(self, p: float) -> bool:
        return self.begin <= p <= self.end

    def __eq__(self, other):
        return (
                self.begin == other.begin and
                self.end == other.end and
                self.quality == other.quality and
                self.begin_y == other.begin_y and
                self.end_y == other.end_y
        )

    def __hash__(self):
        return hash((self.begin, self.end, self.quality, self.begin_y, self.end_y))

    def __cmp__(self, other):
        if self.begin != other.begin:
            return -1 if self.begin < other.begin else 1
        if self.quality == other.quality:
            return 0
        return 1 if is_stronger_as(self.quality, other.quality) else -1

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __repr__(self):
        return f"Interval({self.begin}, {self.end}, {self.quality}, {self.begin_y}, {self.end_y})"

    __str__ = __repr__
