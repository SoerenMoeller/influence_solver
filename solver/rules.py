from functools import reduce
from typing import Union

from statementstruct.statement import Statement
from .constants import *
from .util import quality_add, min_quality, quality_times, is_stronger_as


def interval_join(interval_a: Statement, interval_b: Statement) -> Union[Statement, None]:
    if not interval_a.begin <= interval_b.begin <= interval_a.end <= interval_b.end:
        return None

    start_x: float = min(interval_a.begin, interval_b.begin)
    end_x: float = max(interval_a.end, interval_b.end)
    start_y: float = min(interval_a.begin_other, interval_b.begin_other)
    end_y: float = max(interval_a.end_other, interval_a.end_other)
    quality: str = quality_add(interval_a.quality, interval_b.quality)

    return Statement(start_x, end_x, quality, start_y, end_y)


def interval_strength_right(interval_a: Statement, interval_b: Statement) -> Union[Statement, None]:
    if not (interval_b.begin <= interval_a.end <= interval_b.end):
        return None

    x, y = interval_a.begin_y, interval_a.end_y
    a, b = interval_b.begin_y, interval_b.end_y
    quality_a = interval_a.quality

    rule = None
    if x < b:
        if quality_a == QUALITY_CONS:
            rule = Statement(interval_a.begin, interval_a.end, QUALITY_CONS, max(x, a), min(y, b))
        elif quality_a == QUALITY_MONO and b < y:
            rule = Statement(interval_a.begin, interval_a.end, QUALITY_MONO, x, b)
    elif quality_a == QUALITY_ANTI and x < a < y:
        rule = Statement(interval_a.begin, interval_a.end, QUALITY_ANTI, a, y)

    if rule is not None and interval_a.stronger_as(rule):
        rule = None

    return rule


def interval_strength_left(interval_a: Statement, interval_b: Statement) -> Union[Statement, None]:
    if not (interval_a.begin <= interval_b.begin <= interval_a.end):
        return None

    x, y = interval_a.begin_y, interval_a.end_y
    a, b = interval_b.begin_y, interval_b.end_y
    quality_b = interval_b.quality

    rule = None
    if quality_b == QUALITY_CONS and x < b:
        rule = Statement(interval_b.begin, interval_b.end, QUALITY_CONS, max(x, a), min(y, b))
    elif quality_b == QUALITY_MONO and a < x < b:
        rule = Statement(interval_b.begin, interval_b.end, QUALITY_MONO, x, b)
    elif quality_b == QUALITY_ANTI and a < y < b:
        rule = Statement(interval_b.begin, interval_b.end, QUALITY_ANTI, a, y)

    if rule is not None and interval_b.stronger_as(rule):
        rule = None

    return rule


def interval_strength(interval_a: Statement, interval_b: Statement) -> Union[Statement, None]:
    if not (interval_a.overlaps(interval_b) and interval_a.turn_interval().overlaps(interval_b.turn_interval())) \
            or interval_a == interval_b:
        return None

    x_start: float = max(interval_a.begin, interval_b.begin)
    x_end: float = min(interval_a.end, interval_b.end)
    y_start: float = max(interval_a.begin_other, interval_b.begin_other)
    y_end: float = min(interval_a.end_other, interval_b.end_other)
    quality: str = min_quality(interval_a.quality, interval_b.quality)

    return Statement(x_start, x_end, quality, y_start, y_end)


def interval_strength_multiple(begin: float, end: float, ivs: set[Statement]) -> Statement:
    # Only use when overlapping!

    begin_other: float = max(iv.begin_y for iv in ivs)
    end_other: float = min(iv.end_y for iv in ivs)
    quality: str = reduce(min_quality, (iv.quality for iv in ivs))

    return Statement(begin, end, quality, begin_other, end_other)


def interval_join_multiple(ivs: list[Statement]) -> Union[Statement, None]:
    if not ivs:
        return None
    for i in range(len(ivs) - 1):
        if ivs[i].distance_to(ivs[i + 1]) > 0:
            return None

    quality: str = reduce(quality_add, (iv.quality for iv in ivs))
    begin_other: float = min(iv.begin_y for iv in ivs)
    end_other: float = max(iv.end_y for iv in ivs)

    return Statement(ivs[0].begin, ivs[-1].end, quality, begin_other, end_other)


def transitivity(interval_a: Statement, interval_b: Statement) -> Union[Statement, None]:
    if not (interval_a.begin_y >= interval_b.begin and interval_a.end_y <= interval_b.end):
        return None

    quality: str = quality_times(interval_a.quality, interval_b.quality)
    return Statement(interval_a.begin, interval_a.end, quality, interval_b.begin_y, interval_b.end_y)


def rule_fact(statement: tuple, iv: Statement) -> bool:
    if iv is None:
        return False

    quality: str = statement[2]
    interval_x: tuple[float, float] = statement[1]
    interval_y: tuple[float, float] = statement[3]

    return iv.enveloping(interval_x[0], interval_x[1]) and iv.begin_y >= interval_y[0] \
           and iv.end_y <= interval_y[1] and is_stronger_as(iv.quality, quality)
