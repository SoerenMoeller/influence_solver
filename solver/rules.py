from typing import Union
from intervaltree.intervaltree import Interval
from .util import quality_add, min_quality
from .constants import *


def interval_join(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_a.overlaps(interval_b) and interval_a.turn_interval().overlaps(interval_b.turn_interval())):
        return None

    start_x: float = min(interval_a.begin, interval_b.begin)
    end_x: float = max(interval_a.end, interval_b.end)
    start_y: float = min(interval_a.begin_other, interval_b.begin_other)
    end_y: float = max(interval_a.begin_other, interval_a.end_other)
    quality: str = quality_add(interval_a.quality, interval_b.quality)

    return Interval(start_x, end_x, quality, start_y, end_y)


def interval_strength_right(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_b.begin <= interval_a.end <= interval_b.end):
        return None

    x, y = interval_a.begin_other, interval_a.end_other
    a, b = interval_b.begin_other, interval_b.end_other
    quality_a = interval_a.quality

    rule = None
    if x < b:
        if quality_a == QUALITY_CONS:
            rule = Interval(interval_a.begin, interval_a.end, QUALITY_CONS, max(x, a), min(y, b))
        elif quality_a == QUALITY_MONO and b < y:
            rule = Interval(interval_a.begin, interval_a.end, QUALITY_MONO, x, b)
    elif quality_a == QUALITY_ANTI and x < a < y:
        rule = Interval(interval_a.begin, interval_a.end, QUALITY_ANTI, a, y)

    return rule


def interval_strength_left(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_a.begin <= interval_b.begin <= interval_a.end):
        return None

    x, y = interval_a.begin_other, interval_a.end_other
    a, b = interval_b.begin_other, interval_b.end_other
    quality_b = interval_b.quality

    rule = None
    if quality_b == QUALITY_CONS and x < b:
        rule = Interval(interval_b.begin, interval_b.end, QUALITY_CONS, max(x, a), min(y, b))
    elif quality_b == QUALITY_MONO and a < x < b:
        rule = Interval(interval_b.begin, interval_b.end, QUALITY_MONO, x, b)
    elif quality_b == QUALITY_ANTI and a < y < b:
        rule = Interval(interval_b.begin, interval_b.end, QUALITY_ANTI, a, y)

    return rule


def interval_strength(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_a.overlaps(interval_b) and interval_a.turn_interval().overlaps(interval_b.turn_interval())) \
            or interval_a.quality != interval_b.quality or interval_a == interval_b:
        return None

    x_start: float = max(interval_a.begin, interval_b.begin)
    x_end: float = min(interval_a.end, interval_b.end)
    y_start: float = max(interval_a.begin_other, interval_b.begin_other)
    y_end: float = min(interval_a.end_other, interval_b.end_other)
    quality: str = min_quality(interval_a.quality, interval_b.quality)

    return Interval(x_start, x_end, quality, y_start, y_end)
