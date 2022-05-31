from typing import Union
from intervaltree import Interval
from util import get_quality, get_y_begin, get_y_end, turn_interval, quality_add
from constants import *


def interval_join(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_a.overlaps(interval_b) and turn_interval(interval_a).overlaps(turn_interval(interval_b))):
        return None

    start_x: float = min(interval_a.begin, interval_b.begin)
    end_x: float = max(interval_a.end, interval_b.end)
    start_y: float = min(get_y_begin(interval_a), get_y_end(interval_a))
    end_y: float = max(get_y_begin(interval_b), get_y_end(interval_b))
    quality: str = quality_add(interval_a.data[0], interval_b.data[0])

    return Interval(start_x, end_x, (quality, (start_y, end_y)))


def interval_strength_right(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_b.begin <= interval_a.end <= interval_b.end):
        return None

    x, y = get_y_begin(interval_a), get_y_end(interval_a)
    a, b = get_y_begin(interval_b), get_y_end(interval_b)
    quality_a = get_quality(interval_a)

    rule = None
    if x < b:
        if quality_a == QUALITY_CONS:
            data: tuple = (QUALITY_CONS, (max(x, a), min(y, b)))
            rule = Interval(interval_a.begin, interval_a.end, data)
        elif quality_a == QUALITY_MONO and b < y:
            data: tuple = (QUALITY_MONO, (x, b))
            rule = Interval(interval_a.begin, interval_a.end, data)
    elif quality_a == QUALITY_ANTI and x < a < y:
        data: tuple = (QUALITY_ANTI, (a, y))
        rule = Interval(interval_a.begin, interval_a.end, data)

    return rule


def interval_strength_left(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_a.begin <= interval_b.begin <= interval_a.end):
        return None

    x, y = get_y_begin(interval_a), get_y_end(interval_a)
    a, b = get_y_begin(interval_b), get_y_end(interval_b)
    quality_b = get_quality(interval_a)

    rule = None
    if quality_b == QUALITY_CONS and x < b:
        data: tuple = (QUALITY_CONS, (max(x, a), min(y, b)))
        rule = Interval(interval_b.begin, interval_b.end, data)
    elif quality_b == QUALITY_MONO and a < x < b:
        data: tuple = (QUALITY_MONO, (x, b))
        rule = Interval(interval_b.begin, interval_b.end, data)
    elif quality_b == QUALITY_ANTI and a < y < b:
        data: tuple = (QUALITY_ANTI, (a, y))
        rule = Interval(interval_b.begin, interval_b.end, data)

    return rule


def interval_strength(interval_a: Interval, interval_b: Interval) -> Union[Interval, None]:
    if not (interval_a.overlaps(interval_b) and turn_interval(interval_a).overlaps(turn_interval(interval_b))) \
            or get_quality(interval_a) != get_quality(interval_b) or interval_a == interval_b:
        return None

    x_start: float = max(interval_a.begin, interval_b.begin)
    x_end: float = min(interval_a.end, interval_b.end)
    y_start: float = max(interval_a.data[1][0], interval_b.data[1][0])
    y_end: float = min(interval_a.data[1][1], interval_b.data[1][1])

    return Interval(x_start, x_end, (get_quality(interval_a), (y_start, y_end)))
